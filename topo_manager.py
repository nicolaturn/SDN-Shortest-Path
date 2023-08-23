from ryu.controller.handler import set_ev_cls
from ryu.topology import event
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ofctl_utils import OfCtl, packet,ethernet, arp 
from ryu.lib.packet import ether_types
import networkx as nx


class Device():
    """Base class to represent an device in the network.

    Any device (switch or host) has a name (used for debugging only)
    and a set of neighbors.
    """
    def __init__(self, name):
        self.name = name
        self.neighbors = set()

    def add_neighbor(self, dev):
        self.neighbors.add(dev)

    # . . .

    def __str__(self):
        return "{}({})".format(self.__class__.__name__,
                               self.name)


class TMSwitch(Device):
    """Representation of a switch, extends Device

    This class is a wrapper around the Ryu Switch object,
    which contains information about the switch's ports
    """

    def __init__(self, name, switch):
        super(TMSwitch, self).__init__(name)

        self.switch = switch
        self.name=name
        
        # TODO:  Add more attributes as necessary

    def get_dpid(self):
        """Return switch DPID"""
        return self.switch.dp.id

    def get_ports(self):
        """Return list of Ryu port objects for this switch
        """
        return self.switch.ports

    def get_dp(self):
        """Return switch datapath object"""
        return self.switch.dp

    # . . .


class TMHost(Device):
    """Representation of a host, extends Device

    This class is a wrapper around the Ryu Host object,
    which contains information about the switch port to which
    the host is connected
    """

    def __init__(self, name, host):
        super(TMHost, self).__init__(host)

        self.host = host
        # TODO:  Add more attributes as necessary

    def get_mac(self):
        return self.host.mac

    def get_ips(self):
        return self.host.ipv4

    def get_port(self):
        """Return Ryu port object for this host"""
        return self.host.port

    # . . .
class TopoManager():
    """
    Example class for keeping track of the network topology

    """
    def __init__(self):
        # Initialize some data structures
        self.all_devices = []
        self.all_links = []
        self.network_graph = nx.Graph()
        self.topo = {}
        self.host_ip_lookup={}
        self.host_locate = {}
        self.flow_rules={}
        self.host_to_switch_port={}

    def add_switch(self, sw):
        """
        Function for handling in the topology manager the add switch event:
        Parameters:
            sw: instance of the switch to be added
        Returns:
            None
        """
        name = "switch_{}".format(str(sw.dp.id))
        switch = TMSwitch(name, sw)

        self.all_devices.append(switch)
        self.network_graph.add_node(str(sw.dp.id))
        dpid_str = str(sw.dp.id)
        if dpid_str not in self.topo:
            self.topo[dpid_str] = {}
        print("Added switch node to network_graph:", sw.dp.id)
        print("Current network_graph nodes:",self.network_graph.nodes)

    def add_host(self, h):
        """
        Function for handling in the topology manager the add host event:
        Parameters:
            h: istance of the host to be added
        Returns:
            None
        """
        print(f"initial phase of adding host: mac-->{h.mac} dpip-->{h.port.dpid}")
        name = "host_{}".format(h.mac)
        host = TMHost(name, h)
        print("adding host...",h)
        dpid=str(h.port.dpid)
        

        self.all_devices.append(host)
        self.network_graph.add_node(name)
        self.network_graph.add_edge(dpid, name)
        self.host_locate[h.mac] = {dpid}
        switch_dpid=dpid
        port_no=h.port.port_no
        self.host_to_switch_port[h.mac]={switch_dpid:port_no}
        print(f"current mapping of the hosts with switches:{self.host_to_switch_port}")

    def add_host_ip_mac_mapping(self, ip, mac):
        """
        Function for handling the mapping of the hosts ip to the corrisponding mac addres
        Parameters:
            ip: the ip address of the host
            mac: the mac address of the host
        Returns:
            None 
        """
        self.host_ip_lookup[ip] = mac

    def add_link(self, src_switch, src_port_no, dst_switch, dst_port_no):
        """
        Function for handling in the topology manager the add link event
        Parameters:
            src_switch: the source switch of the link
            src_port_no: the port number of the source switch
            dst_switch: the destination switch of the link
            dst_port_no: the port number of the destination switch
        Returns:
            None
        """
        src_switch=str(src_switch)
        dst_switch=str(dst_switch)
        src_dev = self.get_device_by_port(src_switch, src_port_no)
        dst_dev = self.get_device_by_port(dst_switch, dst_port_no)

        if src_dev and dst_dev and isinstance(src_dev, TMSwitch) and isinstance(dst_dev, TMSwitch):
            src_dev.add_neighbor(dst_dev)
            dst_dev.add_neighbor(src_dev)

        # Add switches as nodes to the network graph (if they are not already added)
        if src_switch not in self.network_graph.nodes:
            self.network_graph.add_node(src_switch)
        if dst_switch not in self.network_graph.nodes:
            self.network_graph.add_node(dst_switch)

        # Add the link to the network graph
        self.network_graph.add_edge(src_switch, dst_switch)
        
        # Add src_switch to self.topo if not present
        if src_switch not in self.topo:
            self.topo[src_switch] = {}
        
        # Add dst_switch to self.topo if not present
        if dst_switch not in self.topo:
            self.topo[dst_switch] = {}

        # Set ouput port in self.topo
        self.topo[src_switch][dst_switch] = src_port_no
        self.topo[dst_switch][src_switch] = dst_port_no

        #print("Added link edge to network_graph:", src_switch, "->", dst_switch)
        #print("Current network_graph edges:", self.network_graph.edges())
        #print("Current network_graph nodes:", self.network_graph.nodes())
        #print(f"Current dictionaries:topo->{self.topo}\n host_locate->{self.host_locate}\n")



        

    def remove_link(self, link):
        """
        Function for handling in the topology manager the remove link event
        Parameters:
            link: the link to be removed
        Returns:
            None
        """
        src_dev = self.get_device_by_port(link.src.dpid, link.src.port_no)
        dst_dev = self.get_device_by_port(link.dst.dpid, link.dst.port_no)

        if src_dev and dst_dev and isinstance(src_dev,TMSwitch) and isinstance(dst_dev,TMSwitch):
            #src_dev.neighbors.remove(dst_dev)
            #dst_dev.neighbors.remove(src_dev)
            src_switch=link.src.dpid
            dst_switch=link.dst.dpid
            self.network_graph.remove_edge(str(dst_switch),str(src_switch))

        # Remove link from data structure(s)

    def get_device_by_port(self, dpid, port_no):
        """
        Function for getting the device by the port number
        Parameters:
            dpid: the dpid of the device
            port_no: the port number of the device
        Returns:
            an instance of the device found, None otherwise
        """
        for dev in self.all_devices:
            if isinstance(dev, TMSwitch):
                for port in dev.get_ports():
                    if port.port_no == port_no and dev.get_dpid() == dpid:
                        return dev
            elif isinstance(dev, TMHost) and port_no == dev.get_port().port_no:
                return dev
        return None
    
    def get_device_by_name(self, name):
        name="switch_"+name
        #print(f"name is: {name}")
        for dev in self.all_devices:
            if isinstance (dev, TMSwitch):
                #print(f" device : {dev.switch}, name: {dev.name}")
                if name==str(dev.name):
                    return dev

    def get_host_port_on_switch(self,host_mac,switch_dpid):
        if host_mac in self.host_to_switch_port and switch_dpid in self.host_to_switch_port[host_mac]:
            switch_port=self.host_to_switch_port[host_mac][switch_dpid]
            print(switch_port)
            return int(switch_port) 
        else:
            return None


    def get_shortest_path(self, src_switch, dst_switch):
        """
        Function for getting the shortest path between two switches
        Parameters:
            src_switch: the source switch of our path
            dst_switch: the destination switch of our path
        Returns:
            a list containing the shortest path between src and dst
        """
        print(f"getting the shortest path from {src_switch} to {dst_switch}")
        try:
            src_switch=str(src_switch)
            dst_switch=str(dst_switch)
            shortest_path = nx.shortest_path(self.network_graph, source=src_switch, target=dst_switch)
            return shortest_path
        except nx.NetworkXNoPath:
            print("Not finding any path...")
            return None
        except nx.NodeNotFound:
            print("not founding any the nodes passed...")
            return None
        
    def get_switch_by_dpid(self, dpid):
        """
        Function for getting a switch by his dpid
        Parameters:
            dpid: the dpid of the switch to retrieve
        Returns: 
            the switch istance if it's found, None otherwise
        """
        for dev in self.all_devices:
            if isinstance(dev, TMSwitch) and str(dev.get_dpid()) == dpid:
                return dev
        return None
    
    def dpid_hostLookup(self, mac):
        """
        Function for getting a host dpid by its mac address
        Parameters:
            mac: the mac address of the host to be retrieved
        Returns:
            the host dpid if found, None otherwise
        """
        for host in self.all_devices:
            if isinstance(host, TMHost) and host.get_mac() == mac:
                return (host.get_port().dpid)
        return None
    




    def get_port(self, dpid, port_no):
        """
        Function to retrieve a port by the corresponding dpid and port_no
        Parameters:
            dpid: the dpid of the device
            port_no: the port number to be retrieved
        Returns:
            the port if found, None otherwise
        """
        switch = self.get_switch_by_dpid(dpid)
        if switch is not None:
            for port in switch.ports.values():
                if port.port_no == port_no:
                    return port
        return None






    def get_output_port(self, src_switch, dst_switch):
        """
        Function to retrieve the output port between a given src and dst
        Parameters:
            src_switch: the source switch 
            dst_switch: the destination switch
        Returns:
            the output port if it's found, None otherwise
        """
        src_switch = str(src_switch)
        dst_switch = str(dst_switch)

        path = self.get_shortest_path(src_switch, dst_switch)
        if path is not None and len(path) > 1:
            src = path[0]
            dst = path[1]
            print(f"Entering get_output_port on src:{src}, dst:{dst}")

            if src in self.topo and dst in self.topo[src]:
                print(self.topo)
                return self.topo[src][dst]  # Use the topology dictionary to get the output port

        return None
    
    def add_rule_to_dict(self,switch, in_port, out_port):
        print(f"adding to the rul dict rule for switch {switch} [{in_port}]= {out_port}")
        if switch not in self.flow_rules:
            self.flow_rules[switch]={}
        self.flow_rules[switch][in_port]=out_port

    def get_rule_from_dict(self, switch, in_port):
        """
        Retrieve the out port associated with the given switch and in port from the rule dictionary.
        Returns None if the rule is not found.
        """
        print(f"searching for {switch} and related rules on the in_port {in_port}")
        if switch in self.flow_rules and in_port in self.flow_rules[switch]:
            print(f"found existing rule on {switch}[{in_port}]:{self.flow_rules[switch][in_port]}")
            return self.flow_rules[switch][in_port]
        else:
            print(f"not finding any rules on {switch}[{in_port}]")
            return None


