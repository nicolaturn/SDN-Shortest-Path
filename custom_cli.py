# custom_cli.py

from mininet.cli import CLI
from mininet.log import error

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
            url = args[1]

            # Simulate a client request by executing the client script
            client_cmd = f"python3 scriptClient.py {url}"
            res = self.mn[host_name].cmd(client_cmd)
            print(res)

    
    