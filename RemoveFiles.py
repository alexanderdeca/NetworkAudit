#!/usr/bin/env python3

# created by Alexander Deca - Deca Consulting 06/07/2023
# please note there is a requirements file -> pip install -r requirements.txt
# this script iterates over a directory and deletes files with _diff.txt

import os

directory_path = 'output'

# Recursive function to iterate over files and subdirectories
def delete_files_with_diff_txt(directory):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            
            # Check if the file is a regular file and if it contains "_diff.txt" in its name
            if "_diff.txt" in filename:
                # Delete the file
                os.remove(file_path)
                print(f"Deleted file: {file_path}")

# Call the function to delete files in the directory and its subdirectories
delete_files_with_diff_txt(directory_path)
