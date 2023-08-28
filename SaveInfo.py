#!/usr/bin/env python3

# created by Alexander Deca - Deca Consulting 06/07/2023
# please note there is a requirements file -> pip install -r requirements.txt
# this script iterates over a # of commands that will be executed on the network
# device and saves the output to txt file
# input csv file format is ip_address,username,password,name,platform

import csv
import logging
import os
from scrapli.driver.core import IOSXEDriver, NXOSDriver, IOSXRDriver
from datetime import datetime

now = datetime.now()
date = now.strftime("%Y-%m-%d")

logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the CSV file path containing the device details
csv_file = 'hosts_telio.csv'

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
        hostname_line = 0  # Line index for NX-OS
    elif device["platform"] == "iosxr":
        driver = IOSXRDriver
        hostname_line = 2  # Line index for IOS XR

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
            # Get the hostname from the device["name"]
            hostname = device["name"]
            
            # Create a directory with the hostname if it doesn't exist
            output_directory = f"output_{date}/{hostname}_output"
            if not os.path.exists(output_directory):
                os.makedirs(output_directory)
            
            # Read the commands from the CSV file
            commands = []
            with open('commands.csv', 'r') as commands_file:
                commands_reader = csv.reader(commands_file)
                header = next(commands_reader)
                for command_row in commands_reader:
                    commands.append(command_row[0])
          
            # Execute each command and save the output or error message
            for command in commands:
                command_result = conn.send_command(command)
                output_filename = f"{output_directory}/{command.replace(' ', '_')}.txt"
                with open(output_filename, 'w') as output_file:
                    if command_result.failed:
                        output_file.write(f"Error executing command: {command_result.result}")
                    else:
                        output_file.write(command_result.result)
            
                logger.info(f"Commands executed successfully for {device['name']}. Output saved in {output_directory}.")
        else:
            logger.error(f"Connection to {device['name']} is not alive.")
    except Exception as e:
        logger.error(f"Error occurred while establishing connection with {device['ip_address']}: {str(e)}")