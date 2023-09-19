#!/usr/bin/env python3

# created by Alexander Deca - Deca Consulting 06/07/2023
# please note there is a requirements file -> pip install -r requirements.txt
# this script iterates over 2 directories and runs a diff between the files
# within that directory

import os
import difflib
import logging

# Set up logging

logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def perform_diff(file1_path, file2_path, diff_directory):
    """Performs diff between two files and saves the differences"""
    try:
        with open(file1_path, 'r') as file1:
            file1_content = file1.readlines()

        with open(file2_path, 'r') as file2:
            file2_content = file2.readlines()

        # Perform the diff
        diff = difflib.unified_diff(file1_content, file2_content, fromfile=file1_path, tofile=file2_path)

        # Create the diff directory if it doesn't exist
        os.makedirs(diff_directory, exist_ok=True)

        # Output the differences to a file within the diff directory
        diff_file_path = os.path.join(diff_directory, os.path.basename(file1_path) + "_diff.txt")
        with open(diff_file_path, "w") as output_file:
            output_file.write(f"Differences between {file1_path} and {file2_path}:\n")
            for line in diff:
                output_file.write(line)
    except Exception as e:
        logger.error(f"Error occurred while processing files: {str(e)}")

def compare_directories(directory1, directory2, parent_diff_directory):
    """Compares files in two directories"""
    try:
        files1 = os.listdir(directory1)
        files2 = os.listdir(directory2)
    except Exception as e:
        logger.error(f"Error occurred while accessing directories: {str(e)}")
        return

    # Create the diff directory for the current directories
    diff_directory = os.path.join(parent_diff_directory, os.path.basename(directory1) + "_diff")

    for file in files1:
        file1_path = os.path.join(directory1, file)
        file2_path = os.path.join(directory2, file)

        if os.path.isdir(file1_path) and os.path.isdir(file2_path):
            compare_directories(file1_path, file2_path, diff_directory)
        elif os.path.isfile(file1_path) and os.path.isfile(file2_path):
            perform_diff(file1_path, file2_path, diff_directory)
        else:
            logger.error(f"File '{file}' is not present in both directories or is of different types.")

    for file in files2:
        if file not in files1:
            logger.error(f"File '{file}' is only present in directory 2.")

# Main directories to compare
main_directory1 = 'output_dir1'
main_directory2 = 'output_dir2'

# Directory to store the diff files
parent_diff_directory = 'diff'

compare_directories(main_directory1, main_directory2, parent_diff_directory)