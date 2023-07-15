#!/usr/bin/env python3

# created by Alexander Deca - Deca Consulting 06/07/2023
# please note there is a requirements file -> pip install -r requirements.txt

import os
import csv
from ntc_templates.parse import parse_output
import manuf

def parse_cisco_show_output(output):
    # Parse the show command output using ntc-templates
    result = parse_output(platform="cisco_ios", command="show mac address-table", data=output)
   
    parsed_results = []  # List to store parsed results

    mlookup = manuf.MacParser()

    for entry in result:
        mac_address = entry["destination_address"]
        interface = entry["destination_port"][0]
        mac_type = entry["type"][0]
        vlan = entry["vlan"]
        vendor = mlookup.get_manuf(mac_address)

        if mac_type == 'S':
            mac_type = "Static"
        elif mac_type == 'D':
            mac_type = "Dynamic"

        if vendor is None:
            vendor = "N/A"

        parsed_results.append([mac_address, interface, mac_type, vlan, vendor])
    return parsed_results


def review_directory(directory, output_file):
    # Create a CSV file for writing
    with open(output_file, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["host","mac_address", "interface", "mac_type", "vlan", "vendor"])

        # Iterate over subdirectories in the given directory
        for root, dirs, files in os.walk(directory):
            for file in files:
                # Check if the file is a show command output file
                if file.startswith("show_mac") and file.endswith(".txt"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r") as f:
                        output = f.read()
                        parsed_results = parse_cisco_show_output(output)

                        # Write the extracted information to the CSV file
                        for entry in parsed_results:
                            writer.writerow([root.split("/")[1].split("_")[0]] + entry)

# Specify the directory path containing the subdirectories with show command output
directory_path = "output"

# Specify the output CSV file path
output_csv_file = "MacInfo.csv"

# Review the directory and save the output in CSV format
review_directory(directory_path, output_csv_file)