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
