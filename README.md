# Network Automation Scripts

This repository contains a collection of Python scripts for network automation tasks. These scripts utilize the `scrapli` library for SSH connections, `networkx` for network topology visualization, and various other libraries for parsing and processing data from network devices.

## Prerequisites

Make sure you have Python 3 installed. You can install the required libraries using the provided `requirements.txt` file:

```
pip install -r requirements.txt
```

## Script Descriptions

### 1. `network_topology.py`

This script fetches CDP/LLDP neighbor information from network devices specified in a CSV file and builds a network topology. It then visualizes the topology using `networkx` and `matplotlib`.

**Usage:**
1. Modify the CSV file `hosts.csv` to include the details of network devices.
2. Run the script:
   ```
   python network_topology.py
   ```

### 2. `update_hostname.py`

This script connects to network devices, retrieves the hostname, and updates the hostname in the input CSV file.

**Usage:**
1. Modify the CSV file `hosts.csv` to include the details of network devices.
2. Run the script:
   ```
   python update_hostname.py
   ```

### 3. `parse_mac_info.py`

This script parses MAC address table information from network devices' show commands and saves the results in a CSV file.

**Usage:**
1. Place show command output files in the `output` directory.
2. Run the script:
   ```
   python parse_mac_info.py
   ```

### 4. `delete_diff_files.py`

This script iterates over directories and deletes files with "_diff.txt" in their names.

**Usage:**
1. Modify the `directory_path` variable in the script if needed.
2. Run the script:
   ```
   python delete_diff_files.py
   ```

### 5. `compare_directories.py`

This script compares two directories containing files and generates diff files for differences.

**Usage:**
1. Modify the `main_directory1` and `main_directory2` variables in the script.
2. Run the script:
   ```
   python compare_directories.py
   ```

### 6. `execute_commands.py`

This script connects to network devices, executes commands, and saves the command output in files.

**Usage:**
1. Modify the CSV file `hosts.csv` to include the details of network devices.
2. Place the commands to be executed in the `commands.csv` file.
3. Run the script:
   ```
   python execute_commands.py
   ```

### 7. `save_version_info.py`

This script parses version information from network devices' show version commands and saves the results in a CSV file.

**Usage:**
1. Place show command output files in the `output_YYYY-MM-DD` directory.
2. Run the script:
   ```
   python save_version_info.py
   ```

## Author

Alexander Deca - Deca Consulting
Date: 06/07/2023
For remarks/questions info@deca-consulting.be

## Note

These scripts are provided as-is and may require adjustments based on your network environment and device configurations. Please review and modify the scripts as needed before using them in production environments.
