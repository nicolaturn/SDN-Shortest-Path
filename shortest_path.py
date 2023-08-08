#!/usr/bin/env python3

"""Shortest Path Switching template
CSCI1680

This example creates a simple controller application that watches for
topology events.  You can use this framework to collect information
about the network topology and install rules to implement shortest
path switching.

"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0, ofproto_v1_0_parser

from ryu.topology import event, switches
import ryu.topology.api as topo
from ryu.topology.event import EventHostAdd

from ryu.lib.packet import packet, ether_types
from ryu.lib.packet import ethernet, arp, icmp

from ofctl_utils import OfCtl, VLANID_NONE

from topo_manager import TopoManager
import logging





class ShortestPathSwitching(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ShortestPathSwitching, self).__init__(*args, **kwargs)

        self.tm = TopoManager()
        self.mac_to_port={}
        logging.basicConfig(level=logging.DEBUG)

    @set_ev_cls(event.EventSwitchEnter)
    def handle_switch_add(self, ev):
        """
        Event handler indicating a switch has come online.
        """
        switch = ev.switch

        self.logger.warn("Added Switch switch%d with ports:", switch.dp.id)
        for port in switch.ports:
            self.logger.warn("\t%d:  %s", port.port_no, port.hw_addr)

        # TODO:  Update network topology and flow rules
        self.tm.add_switch(switch)

    @set_ev_cls(event.EventSwitchLeave)
    def handle_switch_delete(self, ev):
        """
        Event handler indicating a switch has been removed
        """
        switch = ev.switch

        self.logger.warn("Removed Switch switch%d with ports:", switch.dp.id)
        for port in switch.ports:
            self.logger.warn("\t%d:  %s", port.port_no, port.hw_addr)

        # TODO:  Update network topology and flow rules
        

    @set_ev_cls(EventHostAdd)
    def handle_host_add(self, ev):
        """
        Event handler indicating a host has joined the network
        This handler is automatically triggered when a host sends an ARP response.
        """
        self.logger.info("Handling EventHostAdds")
        host = ev.host
        self.logger.warn("Host Added:  %s (IPs:  %s) on switch%s/%s (%s)",
                          host.mac, host.ipv4,
                          host.port.dpid, host.port.port_no, host.port.hw_addr)

        # TODO:  Update network topology and flow rules
        for ip in host.ipv4:
            self.tm.add_host_ip_mac_mapping(ip, host.mac)
        self.tm.add_host(host)
        print(f"Checking dictionaries population: host_locate->{self.tm.host_locate}")

    @set_ev_cls(event.EventLinkAdd)
    def handle_link_add(self, ev):
        """
        Event handler indicating a link between two switches has been added
        """
        self.logger.warn("adding link....")
        link = ev.link
        src_switch=link.src.dpid
        src_port_no=link.src.port_no
        dst_switch=link.dst.dpid
        dst_port_no=link.dst.port_no
        #self.logger.warn("Added Link:  switch%s/%s (%s) -> switch%s/%s (%s)",
                         #src_port.dpid, src_port.port_no, src_port.hw_addr,
                         #dst_port.dpid, dst_port.port_no, dst_port.hw_addr)

        # TODO:  Update network topology and flow rules
        #self.logger.warn("link of type", type(link.src))
        self.tm.add_link(src_switch,src_port_no,dst_switch,dst_port_no)

    @set_ev_cls(event.EventLinkDelete)
    def handle_link_delete(self, ev):
        """
        Event handler indicating when a link between two switches has been deleted
        """
        link = ev.link
        src_port = link.src
        dst_port = link.dst

        self.logger.warn("Deleted Link:  switch%s/%s (%s) -> switch%s/%s (%s)",
                          src_port.dpid, src_port.port_no, src_port.hw_addr,
                          dst_port.dpid, dst_port.port_no, dst_port.hw_addr)

        # TODO:  Update network topology and flow rules

    @set_ev_cls(event.EventPortModify)
    def handle_port_modify(self, ev):
        """
        Event handler for when any switch port changes state.
        This includes links for hosts as well as links between switches.
        """
        port = ev.port
        self.logger.warn("Port Changed:  switch%s/%s (%s):  %s",
                         port.dpid, port.port_no, port.hw_addr,
                         "UP" if port.is_live() else "DOWN")

        # TODO:  Update network topology and flow rules
        



# ... Existing code ...

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        self.logger.debug("packet received!")
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                            ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.in_port

        

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        src=eth.src
        


        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # Ignore LLDP packet
            return
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            arp_packet = pkt.get_protocol(arp.arp)
            if arp_packet:
                if arp_packet.opcode == arp.ARP_REQUEST:
                    # Handle ARP request
                    self.logger.info("Received ARP request from %s for %s", src, arp_packet.dst_ip)
                    # Add your logic here to handle ARP requests and add the host to your topology manager
                    res=self.handle_arp_request(datapath, in_port, eth, arp_packet)
                    



                elif arp_packet.opcode == arp.ARP_REPLY:
                    # Handle ARP reply
                    self.logger.info("Received ARP reply from %s", src)
                    # Add your logic here to handle ARP replies and update your topology manager if needed
             

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        print(f"datapath tracked:{datapath}")
        src_dpid = self.tm.dpid_hostLookup(src)
        dst_dpid = self.tm.dpid_hostLookup(dst)
        self.mac_to_port.setdefault(dpid, {})

        if dst_dpid is not None:
            self.logger.info("\n\tpacket in %s %s %s %s %s", dpid, src, dst, dst_dpid, in_port)

        # Learn a MAC address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Call the TopoManager to get the shortest path between source and destination switches
        if str(src_dpid) in self.tm.topo and str(dst_dpid) in self.tm.topo:
                    self.logger.info("calling to dijkstra with source %s destination %s", src_dpid, dst_dpid)
                    print(f"graph of the current network: {self.tm.network_graph.nodes()}\n {self.tm.network_graph.edges()} ")
                    path = self.tm.get_shortest_path(str(src_dpid),str(dst_dpid))
                    print(f"setting flow rules in path:{path}")

                    if path is not None and len(path) >= 2:
                                print(f"lenght of path:{len(path)}")
                                for i in range(1, len(path)+1):
                                    print (f"{i} iteration on path of lenght: {len(path)} to set up rules")
                                    if(i==len(path)):
                                         last=path[i-1]
                                         prev=path[i-2]
                                         print(f"trying to set flow for {last} to connect to host under the assumption that switches and hosts are connected on port 1")
                                         #retrieving the out_port of the previous element to set in the last as the in_port
                                         in_port=self.tm.get_output_port(prev,last)
                                         print("setting last rule")
                                         if out_port is not None:
                                              actions=[parser.OFPActionOutput(1)]
                                              match=ofproto_v1_0_parser.OFPMatch(in_port=out_port)
                                              self.add_flow(datapath,match,actions)
                                         break
                                    prv = path[i-1]
                                    next = path[i]
                                    print(f"trying to set flow for {prv} to {next}")
                                    out_port = self.tm.get_output_port(prv, next)
                                    print(f"outport:{out_port}")
                                    if out_port is not None:
                                        print("setting forwarding rules...")
                                        actions = [parser.OFPActionOutput(out_port)]
                                        
                                        # Get datapath for the current switch
                                        switch_dp = self.tm.get_switch_by_dpid(prv)  # Assuming get_switch_by_dpid returns datapath
                                        
                                        # Create match object
                                        print(f"in_port retrieved:{in_port}")
                                        match = ofproto_v1_0_parser.OFPMatch(in_port=in_port)
                                        
                                        # Add flow rule to the current switch
                                        self.add_flow(datapath, match, actions) 
                                        
                                print(actions)   
                            
        """ 
        # Install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port)

            # Verify if we have a valid buffer_id, if yes avoid sending both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out) """

    def handle_arp_request(self, datapath, in_port, eth, arp_packet):
        # Check if the destination IP is in your topology manager's hosts
        if arp_packet.dst_ip in self.tm.host_ip_lookup:
            dst_mac = self.tm.host_ip_lookup[arp_packet.dst_ip]
            print(f"sending the mac: {dst_mac}")
            print(f"Received ARP request for {arp_packet.dst_ip} from {arp_packet.src_ip}")
            print(f"Sending ARP reply to {arp_packet.src_ip} with MAC address: {dst_mac}")
            # Update the ARP reply packet with the correct MAC address
            arp_reply = arp.arp(
                opcode=arp.ARP_REPLY,
                src_mac=dst_mac,
                src_ip=arp_packet.dst_ip,
                dst_mac=arp_packet.src_mac,
                dst_ip=arp_packet.src_ip
            )
            eth_reply = ethernet.ethernet(
                ethertype=ether_types.ETH_TYPE_ARP,
                src=dst_mac,
                dst=arp_packet.src_mac
            )
            pkt = packet.Packet()
            pkt.add_protocol(eth_reply)
            pkt.add_protocol(arp_reply)
            pkt.serialize()

            # Send the ARP reply packet out
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            actions = [parser.OFPActionOutput(in_port)]
            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=ofproto.OFP_NO_BUFFER,
                in_port=ofproto.OFPP_CONTROLLER,
                actions=actions,
                data=pkt.data
            )
            datapath.send_msg(out)
            print("terminated")
        else:
            # If the destination IP is not known in the network, you can either flood the ARP request
            # or drop it. Here, I will simply drop the ARP request.
            return



        
    def add_flow(self, datapath, match, actions):
        ofproto = ofproto_v1_0
        parser = ofproto_v1_0_parser

        flow_mod = parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=ofproto.OFP_DEFAULT_PRIORITY,
            actions=actions,
             
        )
        res=datapath.send_msg(flow_mod)
        print(f"inside add_flow:{res}")







if __name__ == '__main__':
    from ryu.cmd import main

    # Run the Ryu controller
    app_manager.run_eventlet(ShortestPathSwitching)
    #ryu_app=ShortestPathSwitching()
    #main([ryu_app])
