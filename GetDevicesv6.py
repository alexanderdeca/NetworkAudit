#!/usr/bin/env python3

# created by Alexander Deca - Deca Consulting 06/07/2023
# please note there is a requirements file -> pip install -r requirements.txt
# input csv file format is ip_address,hostname,platform,type

import csv
import logging
import os
from ntc_templates.parse import parse_output
from pyvis.network import Network
from scrapli.driver.core import IOSXEDriver, NXOSDriver, IOSXRDriver
import networkx as nx

# Constants
SSH_PORT = int(os.getenv("SSH_PORT", 22))
ROUTER = ['ISR4331B', 'C897VAK9']
ASWITCH = ['WSC3650', 'C9300L24', 'C9300L48']
CSWITCH = ['WSC3850','C930024S']
HOSTS = "hosts_brugge.csv"

# Environment Variables
SSH_USER = os.getenv("SSH_USER")
SSH_PWD = os.getenv("SSH_PWD")

# Initialize logging
logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
# logging.basicConfig(filename='error.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check if all required environment variables are set
if not all([SSH_USER, SSH_PWD, SSH_PORT]):
    logger.error("One or more environment variables are not set")
    exit(1)

# Create dictionary from the different platform types for using the correct image for graph nodes
platform = {value: 'aswitch' for value in ASWITCH}
platform.update({value: 'cswitch' for value in CSWITCH})
platform.update({value: 'router' for value in ROUTER})

# Image URLs for graph nodes
icons = {
    "router": "icons/router.png",
    "cswitch": "icons/core.png",
    "aswitch": "icons/switch.png",
    "PC": "icons/pc.png",
}

def establish_connection(device):
    """Establishes a connection to a network device."""
    driver = None
    if device["platform"] == "iosxe":
        driver = IOSXEDriver
    elif device["platform"] == "nxos":
        driver = NXOSDriver
    elif device["platform"] == "iosxr":
        driver = IOSXRDriver
    else:
        logger.error(f"Unsupported platform: {device['platform']}")
        return None

    try:
        conn = driver(
            host=device["ip_address"],
            auth_username=SSH_USER,
            auth_password=SSH_PWD,
            auth_strict_key=False,
            ssh_config_file="~/.ssh/config",
        )
        conn.open()
        if conn.isalive():
            return conn
        else:
            logger.error(f"Connection to {device['hostname']} is not alive.")
    except Exception as e:
        logger.error(f"Error occurred while establishing connection with {device['ip_address']}: {str(e)}")
        return None

def close_connection(conn):
    """Closes a connection to a network device."""
    if conn:
        conn.close()

def lookup_icon(type_device):
    """Returns the appropriate icon for a given device type."""
    icon_key = platform.get(type_device, "router")
    return icon_key

def extract_location(location):
    """Extracts location from the hostname."""
    try:
        # Attempt to extract the location by splitting on underscore and period.
        location = HOSTS.split("_", 1)[1].rsplit(".", 1)[0]
    except IndexError:
        # If splitting fails, return a message indicating an issue.
        return "unknown-location"
    return location

def get_neighbors(device):
    """Fetches neighboring devices for a given device."""
    conn = establish_connection(device)
    if not conn:
        logger.warning(f"No connection could be established for {device['hostname']}.")
        return []
    if device["platform"] == "iosxe":
        ntc = "cisco_ios"
    elif device["platform"] == "nxos":
        ntc = "cisco_nxos"
    elif device["platform"] == "iosxr":
        ntc = "cisco_ios_xr"
    else:
        logger.error(f"Unsupported platform: {device['platform']}")
    neighbors = []
    try:
        show_command = "show cdp neighbors"
        response_neighbors = conn.send_command(show_command).result
        parsed_output = parse_output(platform=ntc, command="show cdp neighbors", data=response_neighbors)
        
        if parsed_output is not None:
            neighbors.extend(parsed_output)
        else:
            logger.warning(f"No neighbor information found for {device['hostname']}.")
    except Exception as e:
        logger.error(f"Error occurred while getting neighbors for {device['hostname']}: {str(e)}")
    finally:
        close_connection(conn)
    return neighbors

def build_network_topology(devices):
    """Builds the network topology graph."""
    G = nx.MultiGraph()  # Use MultiGraph to support multiple edges
    added_devices = set()
    seen_connections = set()  # Track seen connections to prevent duplicates

    for device in devices:
        neighbors = get_neighbors(device)
        hostname = device["hostname"].split(".")[0].lower()
        type_device = device["type"].replace("-", "")
        icon_key = lookup_icon(type_device)

        # Add the device node if not already added
        if hostname not in added_devices:
            G.add_node(hostname, image=icon_key)
            added_devices.add(hostname)
            logger.debug(f"Adding Node: {hostname}, Icon: {icon_key}")

        # Iterate through each neighbor to add edges and neighbor nodes
        for neighbor in neighbors:
            remote_device = neighbor["neighbor"].split(".")[0].lower()
            remote_device_type = neighbor["platform"].replace("-", "")
            remote_icon_key = lookup_icon(remote_device_type)
            local_interface = neighbor["local_interface"]
            remote_interface = neighbor["neighbor_interface"]
            
            # Create a consistent identifier for the connection regardless of which device reported it
            connection_identifier = tuple(sorted([(hostname, local_interface), (remote_device, remote_interface)]))

            # Add the neighbor node if not already added
            if remote_device not in added_devices:
                G.add_node(remote_device, image=remote_icon_key)
                added_devices.add(remote_device)
                logger.debug(f"Adding Node: {remote_device}, Icon: {remote_icon_key}")

            # Add an edge if this connection has not been seen before
            if connection_identifier not in seen_connections:
                G.add_edge(hostname, remote_device, key=connection_identifier, local_interface=local_interface, remote_interface=remote_interface)
                seen_connections.add(connection_identifier)
                logger.debug(f"Adding Edge: {hostname} - {remote_device}, Interfaces: {local_interface} - {remote_interface}")

    return G



def visualize_network_topology(network_topology):
    """Visualizes the network topology using pyvis."""
    nt = Network(notebook=True, width="1500px", height="1000px")

    if not network_topology.nodes():
        logger.error("Network topology graph has no nodes to visualize!")
        return

    for node in network_topology.nodes(data=True):
        icon_key = node[1]['image']
        image_path = icons.get(icon_key, icons['router'])
        if not image_path:
            logger.error(f"Image path not found for {node[0]} with icon key {icon_key}")
        nt.add_node(node[0], title=node[0], image=image_path, shape='image')

    # Dictionary to track added edges to prevent duplicates
    added_edges = {}

    for u, v, key, data in network_topology.edges(data=True, keys=True):
        # Sort the node names to ensure a consistent key irrespective of the edge direction
        sorted_nodes = sorted([u, v])
        edge_key = (sorted_nodes[0], sorted_nodes[1])

        if edge_key not in added_edges:
            added_edges[edge_key] = set()

        # Create a unique identifier for each interface pair
        interface_id = f"{data['local_interface']}-{data['remote_interface']}"

        # Add the interface pair to the set if it's not already present
        added_edges[edge_key].add(interface_id)

    # Add edges to pyvis network with unique interface labels
    for edge_key, interface_set in added_edges.items():
        u, v = edge_key
        label = ', '.join(interface_set)
        nt.add_edge(u, v, title=label)

    nt.show_buttons(filter_=['physics'])
    location = extract_location(HOSTS)
    nt.show(location + '_network_topology.html')


def main():
    """Main execution function."""
    devices = []
    try:
        with open(HOSTS, "r") as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                devices.append(row)
    except FileNotFoundError:
        logger.error(f"{HOSTS} file not found.")
        return
    except Exception as e:
        logger.error(f"Error occurred while reading the {HOSTS} file: {str(e)}")
        return

    try:
        network_topology = build_network_topology(devices)
        visualize_network_topology(network_topology)
    except Exception as e:
        logger.error(f"Error occurred in main flow: {str(e)}")

if __name__ == "__main__":
    main()  