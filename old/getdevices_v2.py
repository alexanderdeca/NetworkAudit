#!/usr/bin/env python3

# created by Alexander Deca - Deca Consulting 06/07/2023
# please note there is a requirements file -> pip install -r requirements.txt

import csv
import logging
from scrapli.driver.core import IOSXEDriver, NXOSDriver, IOSXRDriver
import networkx as nx
import matplotlib.pyplot as plt
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            auth_username=device["username"],
            auth_password=device["password"],
            auth_strict_key=False,
            ssh_config_file="~/.ssh/config",
        )
        conn.open()
        if conn.isalive():
            return conn
        else:
            logger.error(f"Connection to {device['name']} is not alive.")
    except Exception as e:
        logger.error(f"Error occurred while establishing connection with {device['name']}: {str(e)}")

    return None

def close_connection(conn):
    if conn:
        conn.close()

def get_neighbors(device):
    conn = establish_connection(device)
    if not conn:
        return []

    neighbors = []
    try:
        show_command = "show cdp neighbors"
        response_neighbors = conn.send_command(show_command).result
        lines = response_neighbors.splitlines()

        # Find the index of the line starting with "Device ID"
        start_index = next((i for i, line in enumerate(lines) if line.startswith("Device ID")), None)
        if start_index is not None:
            for line in lines[start_index + 1:]:
                line = line.strip()
                if line and not line.startswith("Total"):
                    columns = re.split(r"\s{2,}|\t", line)
                    print(len(columns))
                    if len(columns) == 5:
                        columns.insert(4, 'unknown')  # Insert an empty entry at the 4th place
                        print(columns)
                    neighbor = {
                        "neighbor": columns[0],
                        "local_interface": columns[1],
                        "hold_time": columns[2],
                        "capability": columns[3],
                        "platform": columns[4],
                        "neighbor_interface": columns[5],
                    }
                    neighbors.append(neighbor)
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

            local_interface_parts = neighbor["local_interface"].split()
            local_interface = " ".join(local_interface_parts)

            remote_interface_parts = neighbor["neighbor_interface"].split()
            remote_interface = " ".join(remote_interface_parts)

            # Add the edge between devices if the remote device hasn't been added before
            if remote_device not in added_devices:
                G.add_node(remote_device)
                added_devices.add(remote_device)
            G.add_edge(hostname, remote_device, local_interface=local_interface, remote_interface=remote_interface)

    return G

def visualize_network_topology(network_topology):
    pos = nx.shell_layout(network_topology)
    plt.figure(figsize=(12, 8))
    nx.draw(network_topology, pos, with_labels=True, node_size=800, node_color="lightblue", font_size=8)

    edge_labels = nx.get_edge_attributes(network_topology, "local_interface")
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