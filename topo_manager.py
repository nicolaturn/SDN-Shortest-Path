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
        self.host_locate = {}

    

    @set_ev_cls(event.EventSwitchEnter)
    def handle_switch_enter(self, ev):
        switch = ev.switch
        self.add_switch(switch)

    @set_ev_cls(event.EventLinkAdd)
    def handle_link_add(self, ev):
        link = ev.link
        self.add_link(link)

    @set_ev_cls(event.EventHostAdd)
    def handle_host_add(self, ev):
        host = ev.host
        self.add_host(host)

    def add_switch(self, sw):
        name = "switch_{}".format(sw.dp.id)
        switch = TMSwitch(name, sw)

        self.all_devices.append(switch)
        self.network_graph.add_node(switch.dp.id)
        self.topo[str(sw.dp.id)] = {}

    def add_host(self, h):
        name = "host_{}".format(h.mac)
        host = TMHost(name, h)

        self.all_devices.append(host)
        self.network_graph.add_node(host.mac)
        self.host_locate[str(h.port.dpid)] = {h.mac}

    def add_link(self, link):
        src_dev = self.get_device_by_port(link.src)
        dst_dev = self.get_device_by_port(link.dst)

        if src_dev and dst_dev:
            src_dev.add_neighbor(dst_dev)
            dst_dev.add_neighbor(src_dev)

        src_switch = link.src.dpid
        dst_switch = link.dst.dpid
        self.network_graph.add_edge(src_switch, dst_switch)
        self.topo[str(src_switch)][str(dst_switch)] = 1
        self.topo[str(dst_switch)][str(src_switch)] = 1

    def remove_link(self, link):
        src_dev = self.get_device_by_port(link.src)
        dst_dev = self.get_device_by_port(link.dst)

        if src_dev and dst_dev:
            src_dev.neighbors.remove(dst_dev)
            dst_dev.neighbors.remove(src_dev)

        # Remove link from data structure(s)

    def get_device_by_port(self, port):
        for dev in self.all_devices:
            if isinstance(dev, TMSwitch) and port in dev.get_ports():
                return dev
            elif isinstance(dev, TMHost) and port == dev.get_port():
                return dev

    def get_shortest_path(self, src_switch, dst_switch):
        try:
            shortest_path = nx.shortest_path(self.network_graph, source=src_switch, target=dst_switch)
            return shortest_path
        except nx.NetworkXNoPath:
            return None
        
    def get_switch_by_dpid(self, dpid):
        for dev in self.all_devices:
            if isinstance(dev, TMSwitch) and dev.get_dpid() == dpid:
                return dev
        return None