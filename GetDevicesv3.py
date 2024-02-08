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
ROUTER = ['ISR4331B']
ASWITCH = ['WSC3650', 'C9300L24', 'C9300L48']
CSWITCH = ['WSC3850', 'C930024S']
HOSTS = "hosts_haren.csv"

# Environment Variables
SSH_USER = os.getenv("SSH_USER")
SSH_PWD = os.getenv("SSH_PWD")

logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check if all required environment variables are set
if not all([SSH_USER, SSH_PWD]):
    logger.error("One or more environment variables are not set")
    exit(1)

# Image URLs for graph nodes
icons = {
    "ROUTER": "icons/router.png",
    "CSWITCH": "icons/core.png",
    "ASWITCH": "icons/switch.png",
}

# Function to create a dictionary with hostname as key and type (with '-' removed) as value
def create_host_type_dict(filename):
    host_type_dict = {}
    try:
        with open(filename, "r") as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                device_type = row["type"].replace("-", "").upper()
                host_type_dict[row["name"]] = device_type
    except FileNotFoundError:
        logger.error(f"{filename} file not found.")
    except Exception as e:
        logger.error(f"Error occurred while reading the {filename} file: {str(e)}")
    return host_type_dict

# Function to establish a connection to a device
def establish_connection(device):
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

# Function to close a connection
def close_connection(conn):
    if conn:
        conn.close()

# Function to get neighbors
def get_neighbors(device):
    conn = establish_connection(device)
    if not conn:
        logger.warning(f"No connection could be established for {device['hostname']}.")
        return []

    ntc = {
        "iosxe": "cisco_ios",
        "nxos": "cisco_nxos",
        "iosxr": "cisco_ios_xr"
    }.get(device["platform"])

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

    # Group neighbors by their hostname (neighbor device) and collect multiple interfaces
    neighbor_dict = {}

    for neighbor in neighbors:
        neighbor_name = neighbor["neighbor"].split(".")[0].lower()
        type_device = device["type"].replace("-", "")
        
        # Add type_device to the neighbor_dict
        neighbor_dict.setdefault(neighbor_name, {"interfaces": [], "type_device": type_device})["interfaces"].append((neighbor["local_interface"], neighbor["neighbor_interface"]))

    # Return the list of neighbors with type_device
    # return [{"neighbor": name, "interfaces": data["interfaces"], "type": data["type_device"]} for name, data in neighbor_dict.items()]
    print([{"neighbor": name, "interfaces": data["interfaces"], "type": data["type_device"]} for name, data in neighbor_dict.items()])

# Function to extract location
def extract_location(location):
    try:
        location = HOSTS.split("_", 1)[1].rsplit(".", 1)[0]
    except IndexError:
        return "unknown-location"
    return location

# Function to build network topology
def build_network_topology(devices):
    #G = nx.Graph()
    added_devices = set()
    neighbor_interfaces = {}

    for device in devices:
        print(device)
        neighbors = get_neighbors(device)
        print(neighbors)
        # hostname = neighbors["hostname"].split(".")[0].lower()
        # if hostname not in added_devices:
        #     G.add_node(hostname, image=icon_key)
        #     added_devices.add(hostname)

    #     for neighbor in neighbors:
    #         remote_device = neighbor["neighbor"].split(".")[0].lower()

    #         # Iterate through all interfaces between the same devices
    #         for local_interface, remote_interface in neighbor["interfaces"]:

    #             if remote_device not in added_devices:
    #                 G.add_node(remote_device) #, image=icon_key)
    #                 added_devices.add(remote_device)

    #             # Create a unique edge key for each interface pair
    #             edge_key_with_interfaces = (hostname, remote_device, local_interface, remote_interface)

    #             # Add the edge between devices with interfaces as edge attributes
    #             G.add_edge(hostname, remote_device, key=edge_key_with_interfaces, local_interface=local_interface, remote_interface=remote_interface)

    #             # if hostname not in neighbor_interfaces:
    #             #     neighbor_interfaces[hostname] = {}
    #             # if remote_device not in neighbor_interfaces:
    #             #     neighbor_interfaces[remote_device] = {}

    #             # neighbor_interfaces[hostname].setdefault(remote_device, []).append(local_interface)
    #             # neighbor_interfaces[remote_device].setdefault(hostname, []).append(remote_interface)

    # return G

# Function to visualize network topology
def visualize_network_topology(network_topology):
    nt = Network(notebook=True, width="1500px", height="1000px")

    if not network_topology.nodes():
        logger.error("Network topology graph has no nodes to visualize!")
        return

    for node in network_topology.nodes(data=True):
        print(node)
        # print(node[1]['image'])
        icon_key = node[1]['image']
        image_path = icons.get(icon_key, icons['router'])
        if not image_path:
            logger.error(f"Image path not found for {node[0]} with icon key {icon_key}")
        nt.add_node(node[0], title=node[0], image=image_path, shape='image')

    for (u, v, edge_key), attr in network_topology.edges(data=True, keys=True):
        if not all(key in attr for key in ['local_interface', 'remote_interface']):
            logger.error(f"Edge attribute keys missing for edge ({u}, {v}): {attr}")
        local_interface = attr['local_interface']
        remote_interface = attr['remote_interface']
        label = f"{u} ({local_interface}) - {v} ({remote_interface})"
        print(f"Edge: ({u}, {v}), Key: {edge_key}, Label: {label}")  # Add this line for debugging

        nt.add_edge(u, v, title=label)

    nt.show_buttons(filter_=['physics'])
    location = extract_location(HOSTS)
    nt.show(location + '_network_topology.html')

# Main function
def main():
    devices = []
    try:
        with open(HOSTS, "r") as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                devices.append(row)
    except FileNotFoundError:
        logger.error("hosts_haren.csv file not found.")
        return
    except Exception as e:
        logger.error(f"Error occurred while reading the hosts_haren.csv file: {str(e)}")
        return

    try:
        host_type_dict = create_host_type_dict(HOSTS)

        # Now you have a dictionary (host_type_dict) with hostname as key and type (with '-' removed) as value
        for hostname, device_type in host_type_dict.items():
            print(f"Hostname: {hostname}, Device Type: {device_type}")
    
        # network_topology = build_network_topology(devices)
        # visualize_network_topology(network_topology)
    except Exception as e:
        logger.error(f"Error occurred in main flow: {str(e)}")

if __name__ == "__main__":
    main()
