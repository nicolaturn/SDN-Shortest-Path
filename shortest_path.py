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

from topo_manager import TopoManager
import logging
import pickle
import socket


class ShortestPathSwitching(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]
    

    def __init__(self, *args, **kwargs):
        super(ShortestPathSwitching, self).__init__(*args, **kwargs)

        self.tm = TopoManager()
        self.mac_to_port={}
        logging.basicConfig(level=logging.DEBUG)
        self.ipRyuApp = "127.0.0.1"  
        self.portRyuApp = 6653  

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
        self.ipRyuApp = "127.0.0.1"  
        self.portRyuApp = 6653  


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
        

        self.send_to_thread()

        

    @set_ev_cls(EventHostAdd)
    def handle_host_add(self, ev):
        """
        Event handler indicating a host has joined the network
        This handler is automatically triggered when a host sends an ARP response.
        """
        
        host = ev.host
        self.logger.warn("Host Added:  %s (IPs:  %s) on switch%s/%s (%s)",
                          host.mac, host.ipv4,
                          host.port.dpid, host.port.port_no, host.port.hw_addr)

        # TODO:  Update network topology and flow rules
        for ip in host.ipv4:
            self.tm.add_host_ip_mac_mapping(ip, host.mac)
        self.tm.add_host(host)
        self.logger.warn(f"Checking dictionaries population: host_locate->{self.tm.host_locate}")
        self.logger.warn(self.tm.network_graph )

        self.send_to_thread()



    @set_ev_cls(event.EventLinkAdd)
    def handle_link_add(self, ev):
        """
        Event handler indicating a link between two switches has been added
        """
    
        link = ev.link
        src_switch=link.src.dpid
        src_port_no=link.src.port_no
        dst_switch=link.dst.dpid
        dst_port_no=link.dst.port_no
        #self.logger.warn("Added Link:  switch%s/%s (%s) -> switch%s/%s (%s)",
                         #src_port.dpid, src_port.port_no, src_port.hw_addr,
                         #dst_port.dpid, dst_port.port_no, dst_port.hw_addr)

        # TODO:  Update network topology and flow rules
        self.tm.add_link(src_switch,src_port_no,dst_switch,dst_port_no)


    @set_ev_cls(event.EventLinkDelete)
    def handle_link_delete(self, ev):
        """
        Event handler indicating when a link between two switches has been deleted
        """
        link = ev.link
        src_port = link.src
        dst_port = link.dst

        # self.logger.warn("Deleted Link:  switch%s/%s (%s) -> switch%s/%s (%s)",
        #                   src_port.dpid, src_port.port_no, src_port.hw_addr,
        #                   dst_port.dpid, dst_port.port_no, dst_port.hw_addr)



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


    def send_to_thread(self):
        graph = self.tm.network_graph 
        
        
        # Serialize the graph using pickle
        serialized_graph = pickle.dumps(graph)

        # Create a socket connection and send the serialized graph
        try:
            print("sending topology")
            self.guiSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.guiSocket.connect((self.ipRyuApp, 7001))
            self.guiSocket.send(serialized_graph)
            self.guiSocket.close()
        except Exception as e:
            print("Error sending graph:", e)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """
        Event handler for the packet in event. Sets up the proper forwanding rules on the shortest path.
        """
        self.logger.debug("packet received!")
        if ev.msg.msg_len < ev.msg.total_len: #check if the packet is truncated
            self.logger.debug("packet truncated: only %s of %s bytes",
                            ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto      #set up the main objects in order to set up the forwarding rule
        parser = datapath.ofproto_parser
        in_port = msg.in_port

        
        

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        src=eth.src
        


        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # Ignore LLDP packet: ignoring the link layer discovery packets from the switches
            return
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            arp_packet = pkt.get_protocol(arp.arp)
            if arp_packet:
                if arp_packet.opcode == arp.ARP_REQUEST:
                    # Handle ARP request
                    self.logger.info("Received ARP request from %s for %s", src, arp_packet.dst_ip)
                    # calling the handle_arp_request function to generate an ARP reply
                    res=self.handle_arp_request(datapath, in_port, eth, arp_packet)
                    



                elif arp_packet.opcode == arp.ARP_REPLY:
                    # Handle ARP reply (just printing that is actually received by the sender)
                    self.logger.info("Received ARP reply from %s", src)
                    
             

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        #print(f"datapath tracked:{datapath}")
        src_dpid = self.tm.dpid_hostLookup(src)
        dst_dpid = self.tm.dpid_hostLookup(dst)
        self.mac_to_port.setdefault(dpid, {})

        if dst_dpid is not None:
            self.logger.info("packet in %s %s %s %s %s", dpid, src, dst, dst_dpid, in_port)

        # Call the TopoManager to get the shortest path between source and destination switches 
        if str(src_dpid) in self.tm.topo and str(dst_dpid) in self.tm.topo:
                    #after checking that the src and destination ar in our topo dictionary we call the shortest path on the topo manager
                    
                    
                    path = self.tm.get_shortest_path(str(src_dpid),str(dst_dpid))
                    self.logger.info(f"setting flow rules in path:{path}")
                    #we check if the path has a lenght >= 2 to ensure it is valid
                    if path is not None and len(path) >= 2:
                                self.logger.info(f"lenght of path:{len(path)}")
                                for i in range(0, len(path)): #we add one to lenght to iterate properly on every switch
                                    #if it is the last switch the logic needs to be different
                                    
                                    if(i==0):
                                        first=path[i]
                                        second=path[i+1]
                                        print(f"setting the first element")
                                        out_port=self.tm.get_output_port(first,second)
                                        in_port=self.tm.get_host_port_on_switch(str(src), str(first))
                                        self.check_rule(first,in_port,out_port)
                                        actions=[parser.OFPActionOutput(in_port)]
                                        match=ofproto_v1_0_parser.OFPMatch(in_port=out_port)
                                        self.add_flow(datapath,match,actions)
                                        self.tm.add_rule_to_dict(first,in_port,out_port)
                                        actions=[parser.OFPActionOutput(out_port)]
                                        match=ofproto_v1_0_parser.OFPMatch(in_port=in_port)
                                        self.add_flow(datapath,match,actions)
                                        self.tm.add_rule_to_dict(first, out_port, in_port)
                                        continue
                                        
                                    if(i==len(path)-1):
                                         last=path[i]
                                         prev=path[i-1]
                                         self.logger.info(f"trying to set flow for {last} to connect to host")
                                         #retrieving the out_port of the previous element to set in the last as the in_port
                                         in_port=self.tm.get_output_port(last,prev)
                                         out_port=self.tm.get_host_port_on_switch(str(dst),str(last))
                                         if in_port is not None:                                   #we take the previous switch outport -> existing_out_port=self.tm.get_rule_from_dict(prv,msg.in_port)
                                              self.check_rule(last,1,in_port)
                                                   
                                              actions=[parser.OFPActionOutput(out_port)]                   #and we set it as the last one switch as the in_port
                                              match=ofproto_v1_0_parser.OFPMatch(in_port=in_port)  #then we set the out_port of the last one
                                              self.add_flow(self.tm.get_device_by_name(last).get_dp(),match,actions)                 
                                              self.tm.add_rule_to_dict(last,out_port,in_port)
                                              actions=[parser.OFPActionOutput(in_port)]
                                              match=ofproto_v1_0_parser.OFPMatch(in_port=out_port)         #bidirectional flow
                                              self.add_flow(self.tm.get_device_by_name(last).get_dp(), match,actions)
                                              self.tm.add_rule_to_dict(last,in_port,out_port)
                                              
                                              self.logger.warn(f"rule state:{self.tm.flow_rules}")
                                              break
                                         
                                    #otherwise the logic is straightforward: retrieve the previous and next switch
                                    else:
                                        prev=path[i-1]
                                        current = path[i]
                                        next = path[i+1]
                                        self.logger.info(f"trying to set flow between {prev}, {current} and {next}")
                                        #getting the out port to set on the prv switch
                                        in_port = self.tm.get_output_port(current, prev)
                                        out_port=self.tm.get_output_port(current,next)
        
                                        if out_port is not None:
        
                                            
                                            
                                            # Create match object
                                            
                                            self.check_rule(current,in_port,out_port)
                                            match = ofproto_v1_0_parser.OFPMatch(in_port=in_port)
                                            actions = [parser.OFPActionOutput(out_port)]
                                            self.add_flow(self.tm.get_device_by_name(current).get_dp(), match, actions)
                                            actions=[parser.OFPActionOutput(in_port)]
                                            match=ofproto_v1_0_parser.OFPMatch(in_port=out_port) #bidirectional flow
                                            self.add_flow(self.tm.get_device_by_name(current).get_dp(),match , actions)
                                            self.tm.add_rule_to_dict(current,in_port,out_port)
                                            self.tm.add_rule_to_dict(current,out_port,in_port)
                                            self.logger.warn(f"rule state:{self.tm.flow_rules}")
                                        
                                
                            


    def handle_arp_request(self, datapath, in_port, eth, arp_packet):
        # Check if the destination IP is in your topology manager's hosts
        if arp_packet.dst_ip in self.tm.host_ip_lookup:
            dst_mac = self.tm.host_ip_lookup[arp_packet.dst_ip]
            self.logger.info(f"Received ARP request for {arp_packet.dst_ip} from {arp_packet.src_ip}")
            self.logger.info(f"Sending ARP reply to {arp_packet.src_ip} with MAC address: {dst_mac}")
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
            
        else:
            # If the destination IP is not known in the network, you can either flood the ARP request
            # or drop it. Here, I will simply drop the ARP request.
            return



        
    def add_flow(self, datapath, match, actions):
        """
        Function for adding flows on a given datapath, match and actions.
        Parameters:
            datapath: the datapath on which we are going to set the rules
            match: the object containing the in_port to match
            actions: the object containing the out_port to forward to
        Returns:
            None
        """
        ofproto = ofproto_v1_0
        parser = ofproto_v1_0_parser

        flow_mod = parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=ofproto.OFP_DEFAULT_PRIORITY,
            actions=actions,
             
        )
        datapath.send_msg(flow_mod)
    
    def check_rule(self, switch, in_port, out_port):
         existing_rule=self.tm.get_rule_from_dict(switch,in_port)
         if existing_rule is not None and (existing_rule!=out_port):
              self.logger.warn(f"found already existing rule on in_port:{in_port} for switch:{switch} on out_port:{existing_rule}")
              del self.tm.flow_rules[switch]
              self.delete_flow_rule(self.tm.get_device_by_name(switch).get_dp(),in_port)
         existing_rule=self.tm.get_rule_from_dict(switch,out_port)
         if existing_rule is not None and (existing_rule!=in_port):
              self.logger.warn(f"found already existing rule on in_port:{out_port} for switch:{switch} on out_port:{existing_rule}")
              del self.tm.flow_rules[switch]
              self.delete_flow_rule(self.tm.get_device_by_name(switch).get_dp(),out_port)

    def delete_flow_rule(self, datapath, in_port):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Create a match for the existing rule based on in_port and out_port
        match = parser.OFPMatch(in_port=in_port)

        # Create a flow mod message to delete the rule
        flow_mod = parser.OFPFlowMod(
            datapath=datapath,
            command=ofproto.OFPFC_DELETE,
            match=parser.OFPMatch()
        )

        # Send the flow mod message to the switch
        datapath.send_msg(flow_mod)

        








if __name__ == '__main__':
    from ryu.cmd import main

    # Run the Ryu controller
    app_manager.run_eventlet(ShortestPathSwitching)

