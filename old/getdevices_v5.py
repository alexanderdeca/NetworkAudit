#!/usr/bin/env python3

# created by Alexander Deca - Deca Consulting 06/07/2023
# please note there is a requirements file -> pip install -r requirements.txt

#!/usr/bin/env python3

# created by Alexander Deca - Deca Consulting 06/07/2023
# please note there is a requirements file -> pip install -r requirements.txt

#!/usr/bin/env python3

# created by Alexander Deca - Deca Consulting 06/07/2023
# please note there is a requirements file -> pip install -r requirements.txt

import csv
import logging
from scrapli.driver.core import IOSXEDriver, NXOSDriver, IOSXRDriver
from py4j.java_gateway import JavaGateway
gateway = JavaGateway(classpath="/Users/adeca/gephi-toolkit-0.10.0-all.jar") 
import tempfile
import shutil
import os

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
    gateway = JavaGateway()  # Start the Java Gateway
    gephi = gateway.jvm.org.gephi.project.GephiProject()  # Create a Gephi project

    added_devices = set()  # Set to store unique device names

    for device in devices:
        neighbors = get_neighbors(device)

        # Extract the hostname portion of the device name and convert to lowercase
        hostname = device["name"].split(".")[0].lower()

        # Add the device as a node in Gephi
        gephi.addNode(hostname)

        # Add the device to the set of added devices
        added_devices.add(hostname)

        for neighbor in neighbors:
            remote_device = neighbor["neighbor"].split(".")[0].lower()  # Extract and convert neighbor's hostname to lowercase

            local_interface_parts = neighbor["local_interface"].split()
            local_interface = " ".join(local_interface_parts)

            remote_interface_parts = neighbor["neighbor_interface"].split()
            remote_interface = " ".join(remote_interface_parts)

            # Add the remote device as a node in Gephi
            gephi.addNode(remote_device)

            # Add an edge between the devices
            gephi.addEdge(hostname, remote_device, local_interface, remote_interface)

    # Export the Gephi project to a temporary file
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, "network.gephi")
    gephi.saveProject(temp_file)

    # Open the temporary file in Gephi for visualization
    os.system(f"gephi {temp_file}")

    # Clean up the temporary directory
    shutil.rmtree(temp_dir)

def main():
    devices = []
    with open("hosts_telio.csv", "r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            devices.append(row)

    build_network_topology(devices)

if __name__ == "__main__":
    main()