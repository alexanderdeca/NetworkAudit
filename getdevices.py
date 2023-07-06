#!/usr/bin/env python3

# created by Alexander Deca - Deca Consulting 06/07/2023
# please note there is a requirements file -> pip install -r requirements.txt

import csv
from scrapli.driver.core import IOSXEDriver, NXOSDriver, IOSXRDriver
import networkx as nx
import matplotlib.pyplot as plt

def get_neighbors(device):
    driver = None
    show_command = None
    if device["platform"] == "iosxe":
        driver = IOSXEDriver
        show_command = "show cdp neighbors"
    elif device["platform"] == "nxos":
        driver = NXOSDriver
        show_command = "show cdp neighbors"
    elif device["platform"] == "iosxr":
        driver = IOSXRDriver
        show_command = "show lldp neighbors"
    else:
        print(f"Unsupported platform: {device['platform']}")
        return [], []

    with driver(
        host=device["ip_address"],
        auth_username=device["username"],
        auth_password=device["password"],
        auth_strict_key=False,
    ) as conn:
        conn.open()
        response_neighbors = conn.send_command(show_command)
        response_port_channels = conn.send_command("show port-channel summary")
        conn.close()

    neighbors = response_neighbors.result
    port_channels = response_port_channels.result

    return neighbors, port_channels

def build_network_topology(devices):
    G = nx.Graph()
    for device in devices:
        neighbors, port_channels = get_neighbors(device)

        for neighbor in neighbors:
            local_device = device["name"]
            local_interface = neighbor["local_interface"]
            remote_device = neighbor["neighbor"]
            remote_interface = neighbor["neighbor_interface"]
            G.add_edge(local_device, remote_device, local_interface=local_interface, remote_interface=remote_interface)

        for port_channel in port_channels:
            local_device = device["name"]
            local_interface = port_channel["interface"]
            remote_device = port_channel["neighbor"]
            remote_interface = port_channel["neighbor_interface"]
            G.add_edge(local_device, remote_device, local_interface=local_interface, remote_interface=remote_interface, is_port_channel=True)

    return G

devices = []
with open("hosts.csv", "r") as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        devices.append(row)

network_topology = build_network_topology(devices)
pos = nx.spring_layout(network_topology)
plt.figure(figsize=(12, 8))
nx.draw(network_topology, pos, with_labels=True, node_size=800, node_color="lightblue", font_size=8)

edge_labels = nx.get_edge_attributes(network_topology, "local_interface")
nx.draw_networkx_edge_labels(network_topology, pos, edge_labels=edge_labels, font_size=6)

for u, v, attr in network_topology.edges(data=True):
    if attr.get("is_port_channel"):
        x = pos[u][0] * 0.25 + pos[v][0] * 0.75
        y = pos[u][1] * 0.25 + pos[v][1] * 0.75
        plt.text(x, y, attr["local_interface"], ha="center", va="center", fontsize=6, color="red")

plt.show()