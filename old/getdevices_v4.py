#!/usr/bin/env python3

# created by Alexander Deca - Deca Consulting 06/07/2023
# please note there is a requirements file -> pip install -r requirements.txt

#!/usr/bin/env python3

# created by Alexander Deca - Deca Consulting 06/07/2023
# please note there is a requirements file -> pip install -r requirements.txt

import csv
import logging
from scrapli.driver.core import IOSXEDriver, NXOSDriver, IOSXRDriver
import graph_tool.all as gt
import matplotlib.pyplot as plt
from ntc_templates.parse import parse_output

logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
# logging.basicConfig(level=logging.INFO)
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
                print(item)
                neighbors.append(item)
        else:
            logger.warning("No neighbor information found.")

    except Exception as e:
        logger.error(f"Error occurred while getting neighbors for {device['name']}: {str(e)}")

    close_connection(conn)
    return neighbors

def build_network_topology(devices):
    G = gt.Graph(directed=False)
    added_devices = set()  # Set to store unique device names
    device_name_to_vertex = {}  # Mapping of device names to graph vertices

    for device in devices:
        neighbors = get_neighbors(device)

        # Extract the hostname portion of the device name and convert to lowercase
        hostname = device["name"].split(".")[0].lower()

        # Add the device to the graph if it hasn't been added before
        if hostname not in added_devices:
            v = G.add_vertex()
            device_name_to_vertex[hostname] = v
            added_devices.add(hostname)

        for neighbor in neighbors:
            remote_device = neighbor["neighbor"].split(".")[0].lower()  # Extract and convert neighbor's hostname to lowercase

            local_interface_parts = neighbor["local_interface"].split()
            local_interface = " ".join(local_interface_parts)

            remote_interface_parts = neighbor["neighbor_interface"].split()
            remote_interface = " ".join(remote_interface_parts)

            # Add the edge between devices if the remote device hasn't been added before
            if remote_device not in added_devices:
                v = G.add_vertex()
                device_name_to_vertex[remote_device] = v
                added_devices.add(remote_device)

            u = device_name_to_vertex[hostname]
            v = device_name_to_vertex[remote_device]
            G.add_edge(u, v)

    return G

def visualize_network_topology(network_topology):
    pos = gt.sfdp_layout(network_topology)  # Layout algorithm for Graph-tool
    plt.figure(figsize=(20, 12))
    gt.graph_draw(network_topology, pos=pos, vertex_text=network_topology.vertex_index, vertex_size=10, edge_pen_width=1.2)

    plt.show()

def main():
    devices = []
    with open("hosts_telio.csv", "r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            devices.append(row)

    network_topology = build_network_topology(devices)
    visualize_network_topology(network_topology)

if __name__ == "__main__":
    main()