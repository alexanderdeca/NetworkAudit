#!/usr/bin/env python3

# created by Alexander Deca - Deca Consulting 06/07/2023
# please note there is a requirements file -> pip install -r requirements.txt
# this script fetches the correct hostname and updates the input csv file
# input csv file format is ip_address,name,platform

import os
import csv
import logging
from scrapli.driver.core import IOSXEDriver, NXOSDriver, IOSXRDriver

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

# Define the CSV file path containing the device details
csv_file = 'hosts_arlon.csv'

# Create a list to store the devices
devices = []

# Read the CSV file and populate the devices list
with open(csv_file, 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        devices.append(row)

# Iterate over the devices
    for device in devices:
        # Connect to the device using Scrapli
        driver = None
        if device["platform"] == "iosxe":
            driver = IOSXEDriver
            hostname_line = 0  # Line index for IOS XE
        elif device["platform"] == "nxos":
            driver = NXOSDriver
            hostname_line = 0 # Line index for NX-OS
        elif device["platform"] == "iosxr":
            driver = IOSXRDriver
            hostname_line = 2  # Line index for IOS XR

       
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
                # Send the command to retrieve the hostname
                response = conn.send_command('show running-config | include hostname')

                # Split the response into lines
                lines = response.result.splitlines()
                print(lines)

                # Extract the hostname from the appropriate line
                hostname = lines[hostname_line].split()[1]

                # Update the 'hostname' field in the device dictionary
                device['hostname'] = hostname

                # Close the SSH session
                conn.close()

                # Update the input CSV file with the hostname
                fieldnames = ['ip_address',  'hostname', 'platform', 'type']
                with open(csv_file, 'w', newline='') as file:
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(devices)

                # Print a success message
                print(f'Hostname information updated in {csv_file} successfully.')
            else:
                logger.error(f"Connection to {device['name']} is not alive.")

        except Exception as e:
            logger.error(f"Error occurred while establishing connection with {device['ip_address']}: {str(e)}")
       