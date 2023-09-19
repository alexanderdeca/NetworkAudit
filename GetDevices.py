#!/usr/bin/env python3

# created by Alexander Deca - Deca Consulting 06/07/2023
# please note there is a requirements file -> pip install -r requirements.txt
# input csv file format is ip_address,hostname,platform

import csv
import logging
from scrapli.driver.core import IOSXEDriver, NXOSDriver, IOSXRDriver
import networkx as nx
import matplotlib.pyplot as plt
import os
from ntc_templates.parse import parse_output


# Constants
SSH_PORT = int(os.getenv("SSH_PORT", 22))

# Environment Variables 
SSH_USER = os.getenv("SSH_USER")
SSH_PWD = os.getenv("SSH_PWD")

logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check if all required environment variables are set
if not all([SSH_USER, SSH_PWD, SSH_PORT]):
    logger.error("One or more environment variables are not set")
    exit(1)

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
            logger.error(f"Connection to {device['name']} is not alive.")
    except Exception as e:
        logger.error(f"Error occurred while establishing connection with {device['ip_address']}: {str(e)}")

    return None

def close_connection(conn):
    if conn:
        conn.close()

def get_neighbors(device):
    conn = establish_connection(device)
    if not conn:
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
            for item in parsed_output:
                # print(item)
                neighbors.append(item)
        else:
            logger.warning("No neighbor information found.")

    except Exception as e:
        logger.error(f"Error occurred while getting neighbors for {device['name']}: {str(e)}")

    close_connection(conn)
    return neighbors

def build_network_topology(devices):
    G = nx.Graph()
    added_devices = set()  # Set to store unique device names

    for device in devices:
        neighbors = get_neighbors(device)

        # Extract the hostname portion of the device name and convert to lowercase
        hostname = device["name"].split(".")[0].lower()

        # Add the device to the graph if it hasn't been added before
        if hostname not in added_devices:
            G.add_node(hostname)
            added_devices.add(hostname)

        for neighbor in neighbors:
            remote_device = neighbor["neighbor"].split(".")[0].lower()  # Extract and convert neighbor's hostname to lowercase

            local_interface = neighbor["local_interface"]
            remote_interface = neighbor["neighbor_interface"]

            # Add the edge between devices if the remote device hasn't been added before
            if remote_device not in added_devices:
                G.add_node(remote_device)
                added_devices.add(remote_device)

            # Check if the edge already exists, if yes, append the interface to the existing list
            if G.has_edge(hostname, remote_device):
                G[hostname][remote_device]["local_interface"].append(local_interface)
                G[hostname][remote_device]["remote_interface"].append(remote_interface)
            else:
                G.add_edge(hostname, remote_device, local_interface=[local_interface], remote_interface=[remote_interface])

    return G


def visualize_network_topology(network_topology):
    pos = nx.circular_layout(network_topology)
    plt.figure(figsize=(20, 12))
    nx.draw(network_topology, pos, with_labels=True, node_size=500, node_color="lightblue", font_size=8)

    edge_labels = nx.get_edge_attributes(network_topology, "remote_interface")
    nx.draw_networkx_edge_labels(network_topology, pos, edge_labels=edge_labels, font_size=6)

    for u, v, attr in network_topology.edges(data=True):
        x = pos[u][0] * 0.25 + pos[v][0] * 0.75
        y = pos[u][1] * 0.25 + pos[v][1] * 0.75
        plt.text(x, y, attr["local_interface"], ha="center", va="center", fontsize=6, color="red")

    plt.show()

def main():
    devices = []
    with open("hosts.csv", "r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            devices.append(row)

    network_topology = build_network_topology(devices)
    visualize_network_topology(network_topology)

if __name__ == "__main__":
    main()