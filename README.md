# SDN Controller with Shortest Path Switching

This branch of the project contains the implementation of an SDN (Software-Defined Networking) controller utilizing shortest path switching logic. The controller is developed using the Ryu framework and is designed to manage network topologies composed of Docker container hosts.

## Table of Contents

- [Overview](#overview)
- [Files and Components](#files-and-components)
- [Usage](#usage)
- [Prerequisites](#prerequisites)
- [Running the Controller](#running-the-controller)
- [Running Mininet](#running-mininet)
- [Example](#example)
- [Contributing](#contributing)
- [License](#license)

## Overview

This SDN controller branch focuses on implementing shortest path switching within an SDN environment. The controller leverages Ryu, a popular SDN framework, to facilitate the logic required for efficient path selection and switching within a network topology.

## Files and Components

This branch consists of the following key files:

1. `shortest_path_switching.py`: This file contains the Ryu controller logic responsible for implementing shortest path switching within the network.

2. `topology_manager.py`: The `topology_manager` application is designed to manage topology events and handle updates to the network structure.

3. `run_mininet.py`: This file holds the network topologies that can be emulated using Mininet.

## Prerequisites

Before using the SDN controller and running Mininet topologies, ensure you have the following prerequisites installed:

- Ryu Framework
- Mininet
- Docker

## Usage

To use the SDN controller and simulate network topologies:

1. Clone this repository to your local machine.
2. Install the required dependencies as mentioned in the [Prerequisites](#prerequisites) section.

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


