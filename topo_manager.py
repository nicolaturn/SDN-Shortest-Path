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
        self.switch_to_host={}

    def add_switch(self, sw):
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
        print(f"initial phase of adding host: mac-->{h.mac} dpip-->{h.port.dpid}")
        name = "host_{}".format(h.mac)
        host = TMHost(name, h)
        print("adding host...",h)
        

        self.all_devices.append(host)
        self.network_graph.add_node(h.mac)
        self.network_graph.add_edge(h.port.dpid, h.mac)
        self.host_locate[h.mac] = {h.port.dpid}

    def add_host_ip_mac_mapping(self, ip, mac):
        self.host_ip_lookup[ip] = mac

    def add_link(self, src_switch, src_port_no, dst_switch, dst_port_no, cost=1):
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

        #set switches to host dictionary

        if isinstance(src_dev, TMHost):
            self.switch_to_host_port[src_switch] = {'host': src_dev, 'port': src_port_no}
        if isinstance(dst_dev, TMHost):
            self.switch_to_host_port[dst_switch] = {'host': dst_dev, 'port': dst_port_no}

        print("Added link edge to network_graph:", src_switch, "->", dst_switch)
        print("Current network_graph edges:", self.network_graph.edges())
        print("Current network_graph nodes:", self.network_graph.nodes())
        print(f"Current dictionaries:topo->{self.topo}\n host_locate->{self.host_locate}\n switch_to_host->{self.switch_to_host}")



        

    def remove_link(self, link):
        src_dev = self.get_device_by_port(link.src)
        dst_dev = self.get_device_by_port(link.dst)

        if src_dev and dst_dev and isinstance(src_dev,TMSwitch) and isinstance(dst_dev,TMSwitch):
            src_dev.neighbors.remove(dst_dev)
            dst_dev.neighbors.remove(src_dev)
            src_switch=link.src.dpid
            dst_switch=link.dst.dpid
            self.network_graph.remove_edge(src_switch,dst_switch)

        # Remove link from data structure(s)

    def get_device_by_port(self, dpid, port_no):
        for dev in self.all_devices:
            if isinstance(dev, TMSwitch):
                for port in dev.get_ports():
                    if port.port_no == port_no and dev.get_dpid() == dpid:
                        return dev
            elif isinstance(dev, TMHost) and port_no == dev.get_port().port_no:
                return dev
        return None



    def get_shortest_path(self, src_switch, dst_switch):
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
        for dev in self.all_devices:
            if isinstance(dev, TMSwitch) and str(dev.get_dpid()) == dpid:
                return dev
        return None
    
    def dijkstra(self, src_switch, dst_switch):
        # Initialize distance and previous nodes
        dist = {switch: float('inf') for switch in self.topo}
        prev = {switch: None for switch in self.topo}

        # Distance to the source switch is 0
        dist[src_switch] = 0

        # Set of unvisited switches
        unvisited = set(self.topo.keys())

        while unvisited:
            # Find the unvisited switch with the minimum distance
            current_switch = min(unvisited, key=lambda switch: dist[switch])

            # Remove the current switch from the unvisited set
            unvisited.remove(current_switch)

            # If the destination switch has been reached, break the loop
            if current_switch == dst_switch:
                break

            # Update the distance and previous nodes for neighboring switches
            for neighbor_switch, cost in self.topo[current_switch].items():
                new_distance = dist[current_switch] + cost
                if new_distance < dist[neighbor_switch]:
                    dist[neighbor_switch] = new_distance
                    prev[neighbor_switch] = current_switch

        # Build and return the shortest path
        shortest_path = []
        current_switch = dst_switch
        while current_switch is not None:
            shortest_path.append(current_switch)
            current_switch = prev[current_switch]

        shortest_path.reverse()
        return shortest_path
    
    def dpid_hostLookup(self, mac):
        for host in self.all_devices:
            if isinstance(host, TMHost) and host.get_mac() == mac:
                return (host.get_port().dpid)
        return None
    
    def forward_packet(self, datapath, in_port, pkt, eth_pkt):
        src_mac = eth_pkt.src
        dst_mac = eth_pkt.dst

        src_switch = datapath.id

        # If the destination MAC is known in the same switch, send the packet directly
        for neighbor in self.get_device_by_port(in_port).neighbors:
            if isinstance(neighbor, TMHost) and neighbor.get_mac() == dst_mac:
                self.send_packet(datapath, in_port, pkt)
                return

        # If the destination MAC is not known in the same switch, calculate the shortest path
        # to the destination and forward the packet accordingly
        dst_switch = self.dpid_hostLookup(dst_mac)

        if dst_switch is not None:
            shortest_path = self.dijkstra(src_switch, dst_switch)

            if shortest_path is not None and len(shortest_path) > 1:
                next_hop_switch = shortest_path[1]
                out_port = self.get_output_port(src_switch, next_hop_switch)

                if out_port is not None:
                    actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                    self.send_packet_out(datapath, pkt, actions)


    def send_packet_out(self, datapath, pkt, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = datapath.ofproto.OFPP_CONTROLLER
        buffer_id = datapath.ofproto.OFP_NO_BUFFER
        data = pkt.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=buffer_id,
                                    in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    def send_packet(self, datapath, out_port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        data = pkt.data
        actions = [parser.OFPActionOutput(out_port, ofproto.OFPCML_NO_BUFFER)]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=data)
        datapath.send_msg(out)

    def get_port(self, dpid, port_no):
        switch = self.get_switch_by_dpid(dpid)
        if switch is not None:
            for port in switch.ports.values():
                if port.port_no == port_no:
                    return port
        return None






    def get_output_port(self, src_switch, dst_switch):
        src_switch = str(src_switch)
        dst_switch = str(dst_switch)

        path = self.get_shortest_path(src_switch, dst_switch)
        if path is not None and len(path) > 1:
            src = path[0]
            dst = path[1]
            print(f"Entering get_output_port on src:{src}, dst:{dst}")

            if src in self.topo and dst in self.topo[src]:
                print(self.topo)
                return self.topo[dst][src]  # Use the topology dictionary to get the output port

        return None


