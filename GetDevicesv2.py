#!/usr/bin/env python3

# created by Alexander Deca - Deca Consulting 06/07/2023
# please note there is a requirements file -> pip install -r requirements.txt
# input csv file format is ip_address,hostname,platform

import csv
import logging
import os
import asyncio
from ntc_templates.parse import parse_output
from pyvis.network import Network
from scrapli.driver.core import IOSXEDriver, NXOSDriver, IOSXRDriver
import networkx as nx

# Constants
SSH_PORT = int(os.getenv("SSH_PORT", 22))
ROUTER = ['ISR4331B']
ASWITCH = ['WSC3650', 'C9300L24', 'C9300L48']
CSWITCH = ['WSC3850','C930024S']

# Environment Variables
SSH_USER = os.getenv("SSH_USER")
SSH_PWD = os.getenv("SSH_PWD")

logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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


async def establish_connection(device):
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
        await conn.open()
        if conn.isalive():
            return conn
        else:
            logger.error(f"Connection to {device['name']} is not alive.")
    except Exception as e:
        logger.error(f"Error occurred while establishing connection with {device['ip_address']}: {str(e)}")

    return None

async def get_neighbors(device):
    conn = await establish_connection(device)
    if not conn:
        return []

    neighbors = []
    try:
        show_command = "show cdp neighbors"
        response_neighbors = await conn.send_command(show_command)
        parsed_output = parse_output(platform=device["platform"], command="show cdp neighbors", data=response_neighbors.result)
        if parsed_output is not None:
            neighbors.extend(parsed_output)
        else:
            logger.warning("No neighbor information found.")
    except Exception as e:
        logger.error(f"Error occurred while getting neighbors for {device['name']}: {str(e)}")

    conn.close()
    return neighbors

async def build_network_topology(devices):
    G = nx.Graph()
    added_devices = set()
    
    tasks = [get_neighbors(device) for device in devices]
    all_neighbors = await asyncio.gather(*tasks)

    for device, neighbors in zip(devices, all_neighbors):
        hostname = device["hostname"].split(".")[0].lower()
        type_device = device["type"].replace("-", "")
        icon_key = platform[type_device]

        if hostname not in added_devices:
            G.add_node(hostname, image=icon_key)
            added_devices.add(hostname)

        for neighbor in neighbors:
            remote_device = neighbor["neighbor"].split(".")[0].lower()
            local_interface = neighbor["local_interface"]
            remote_interface = neighbor["neighbor_interface"]

            if remote_device not in added_devices:
                G.add_node(remote_device, image=icon_key)
                added_devices.add(remote_device)

            G.add_edge(hostname, remote_device, local_interface=local_interface, remote_interface=remote_interface)

    return G

def visualize_network_topology(network_topology):
    nt = Network(notebook=True)

    for node in network_topology.nodes(data=True):
        icon_key = node[1]['image']
        image_path = icons[icon_key]
        nt.add_node(node[0], title=node[0], image=image_path, shape='image')

    for u, v, attr in network_topology.edges(data=True):
        label = f"{attr['local_interface']} - {attr['remote_interface']}"
        nt.add_edge(u, v, title=label)

    nt.show_buttons(filter_=['physics'])
    nt.set_options("""
    var options = {
      "nodes": {
        "borderWidth": 2
      },
      "edges": {
        "color": {
          "inherit": true
        },
        "smooth": false
      },
      "physics": {
        "barnesHut": {
          "centralGravity": 0.1,
          "springLength": 200,
          "springConstant": 0.04
        },
        "minVelocity": 0.75
      }
    }
    """)
    
    nt.show('network_topology.html')

async def main():
    devices = []
    with open("hosts.csv", "r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            devices.append(row)

    network_topology = await build_network_topology(devices)
    visualize_network_topology(network_topology)

if __name__ == "__main__":
    asyncio.run(main())