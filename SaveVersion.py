#!/usr/bin/env python3

# created by Alexander Deca - Deca Consulting 06/07/2023
# please note there is a requirements file -> pip install -r requirements.txt
# csv outout file format : File,Hostname,Platform,Software Version,Software Image

import os
import csv
from ntc_templates.parse import parse_output

def parse_cisco_show_output(output):
    # Parse the show command output using ntc-templates
    result = parse_output(platform="cisco_ios", command="show version", data=output)
    print(result)

    # Extract hostname, platform, software version, and software image
    hostname = result[0]["hostname"]
    platform = result[0]["hardware"][0]
    software_version = result[0]["version"]
    software_image = result[0]["software_image"]

    return hostname, platform, software_version, software_image

def review_directory(directory, output_file):
    # Create a CSV file for writing
    with open(output_file, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["File", "Hostname", "Platform", "Software Version", "Software Image"])

        # Iterate over subdirectories in the given directory
        for root, dirs, files in os.walk(directory):
            for file in files:
                # Check if the file is a show command output file
                if file.startswith("show_version") and file.endswith(".txt"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r") as f:
                        output = f.read()
                        # Parse the show command output
                        hostname, platform, software_version, software_image = parse_cisco_show_output(output)
                        # Write the extracted information to the CSV file
                        writer.writerow([file, hostname, platform, software_version, software_image])

# Specify the directory path containing the subdirectories with show command output
directory_path = "output_2023-07-25"

# Specify the output CSV file path
output_csv_file = "SaveVersion.csv"

# Review the directory and save the output in CSV format
review_directory(directory_path, output_csv_file)
