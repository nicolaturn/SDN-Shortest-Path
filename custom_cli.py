# custom_cli.py

from mininet.cli import CLI
from mininet.log import error
from urllib.parse import urlparse
import socket
import requests

class CustomCLI(CLI):
    def do_simulate_communication(self, line):
        """
        Simulate communication between hosts to trigger ARP requests.
        Usage: simulate_communication <source_host> <destination_host>
        """
        args = line.split()

        if len(args) != 2:
            error("Usage: simulate_communication <source_host> <destination_host>\n")
        else:
            source_host = args[0]
            destination_host = args[1]
            
            # Simulate communication by sending a ping between hosts
            self.mn[source_host].cmd('ping -c 1 {}'.format(self.mn[destination_host].IP()))
            return
            
    def do_start_web_server(self, line):
        """
        Start a web server on the specified host
        Usage: start_web_server <host_name>
        """
        args=line.split()

        if len(args)!=1:
            error("Usage: start_web_server <host_name>\n")

        else:
            host_name=args[0]
            if host_name not in self.mn:
                error(f"Host {host_name} not found in the network!\n")
            else:
                host=self.mn[host_name]
                res=host.cmd("python3 -m scriptServer 80 &")
                print(f"Attempting to start the simple web server. Host IP: {host.IP()}. Result: {res.strip()}")

    
    def do_stop_web_server(self, line):
        """
        Stop the web server running on a host.
        Usage: stop_web_server <host_name>
        """
        args = line.split()

        if len(args) != 1:
            error("Usage: stop_web_server <host_name>\n")
        else:
            host_name = args[0]
            host = self.mn[host_name]

            # Stop the web server if it's running
            res = host.cmd("pkill -f 'python3 -m scriptServer 80'")
            if res:
                print(f"Web server on {host_name} has been stopped.")
            else:
                print(f"No running web server found on {host_name}.")
        
    
    def do_check_web_server(self, line):
        """
        Check if a web server is running on a host.
        Usage: check_web_server <host_name>
        """
        args = line.split()

        if len(args) != 1:
            error("Usage: check_web_server <host_name>\n")
        else:
            host_name = args[0]
            host = self.mn[host_name]

            # Check if a web server is running on the host
            res = host.cmd("pgrep -f 'python3 -m scriptServer 80'")
            if res:
                print(f"A web server is running on {host_name}.")
            else:
                print(f"No running web server found on {host_name}.")


        

    def do_simulate_client_request(self, line):
        """
        Simulate a client request to a web server.
        Usage: simulate_client_request <host_name> <url>
        """
        args = line.split()

        if len(args) != 2:
            error("Usage: simulate_client_request <host_name> <url>\n")
        else:
            host_name = args[0]
            src_host=self.mn[host_name].IP()
            url = args[1]
            parsed_url=urlparse(url)
            dst_host=parsed_url.hostname
            controller_ip="127.0.0.1"
            controller_uri=f"http://localhost:8080/comunication/{src_host}/{dst_host}"
            print(f"controller uri:{controller_uri}")
            print(f"retrieved server domain: {dst_host}")
            host=None
            for h in self.mn.values():
                if h.IP()==dst_host:
                    host=h
                    print(f"host retrieved by its ip:{host}")
                    break
            if host is None:
                print(f"no host retrieved at {dst_host}")
                return

            res=h.cmd("pgrep -f 'python3 -m scriptServer 80'")

            # Simulate a client request by executing the client script
            if res:
                controller_response=requests.get(controller_uri)
                print(controller_response)
                controller_response=requests.get("http://localhost:8080/test")
                print(controller_response)
                client_cmd = f"python3 scriptClient.py {url}"
                res = self.mn[host_name].cmd(client_cmd)
                print(res)
            else:
                print(f"Request not sent due to server unavailability")


    
    