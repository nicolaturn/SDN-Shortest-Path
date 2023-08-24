# SDN Controller with Shortest Path Switching

This branch of the project contains the implementation of an SDN (Software-Defined Networking) controller utilizing shortest path switching logic. The controller is developed using the Ryu framework and is designed to manage network topologies.

## Table of Contents

- [Overview](#overview)
- [Files and Components](#files-and-components)
- [Usage](#usage)
- [Prerequisites](#prerequisites)
- [Running the Controller](#running-the-controller)
- [Running Mininet](#running-mininet)
- [Running the GUI](#running-the-GUI)
- [Testing communication](#testing-communication)
- [Contributing](#contributing)

## Overview

This branch focuses on deploying a simple server to manage a GET request from a client. Both the client and the server are running on Mininet's hosts and the Controller implements a Shortest Path Algorithm inside the topology to allow communication. Also, the controller leverages Ryu, a popular SDN framework, to facilitate the logic required for efficient path selection and switching within a network topology. The GUI provides testing functionality such as buttons to deploy different topologies, the graph of the current network, a terminal to launch mininet commands and the output of the running controller.

## Files and Components

This branch consists of the following key files:

1. `shortest_path_switching.py`: This file contains the Ryu controller logic responsible for implementing shortest path switching within the network.

2. `topology_manager.py`: The `topology_manager` application is designed to manage topology events and handle updates to the network structure.

3. `run_mininet.py`: This file holds the network topologies that can be emulated using Mininet.

4. `scriptClient.py`: This file is the script to make an HTTP GET request to a server inside a Mininet host.

5. `scriptServer.py`: This file is the script to make a Simple Server start inside a Mininet Host.

6. `custom_cli.py` : This file is a custom CLI interface to add useful commands inside the Mininet CLI.

7. `sdnGUI.py` : This file holds the testing GUI.

## Prerequisites

Before using the SDN controller and running Mininet topologies, ensure you have the following prerequisites installed:

- Ryu Framework
- Mininet
- Networkx
- Arping
- Matplotlib
- PIL

## Usage

To use the SDN controller and simulate network topologies:

1. Clone this repository to your local machine.
2. Install the required dependencies as mentioned in the [Prerequisites](#prerequisites) section.

It's suggested to use Comnetsemu for a proper enviroment setup, as Mininet needs to be run as root.

## Running the Controller

Run the Ryu controller by executing the following command:

```bash
ryu-manager --observe-links shortest_path_switching.py
```

## Running Mininet
Run mininet by executing the following command:

```bash
sudo python3 run_mininet.py "topology type" "additional number of hosts"
```

## Running the GUI

Run the GUI by exectuing the  following command: 

```bash
python3 sdnGUI.py
```
This will launch the GUI, intended to test the software. When one of the `start topology` buttons is pressed, the GUI performs a cleanup of the previous enviroment, launches the Controller and then starts the Mininet topology. A network of the graph is displayed on the top left corner of the screen, the output of the controller is printed on the read-only terminal in the top right corner and the Mininet terminal is located in the bottom right corner.


## Testing Communication

To test the communication between a pair of hosts:


1. Run `<src> ping <dst>` to test a simple ping command.

2. Run `start_web_server <dst>`to start a server on the specified destination.

3. Run `simulate_client_request <src> <url>` to make an HTTP GET request at the specified URL.


## Contributing

The project team is composed by:

[@nicoloeffe](https://github.com/nicoloeffe)
[@giuliomuraro](https://github.com/GiulioMuraro)
[@nicolaturn](https://github.com/nicolaturn)


