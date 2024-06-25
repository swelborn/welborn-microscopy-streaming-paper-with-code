#!/bin/bash

# This script is placed in the directory that contains the files
files_to_tar=""

# Loop over the range of scan numbers
for scan_number in $(seq 516 575); do
    # Use a wildcard to match any file that fits the pattern
    for file in FOURD_*_*_*_00${scan_number}_binned_calibrated.h5; do
        # Check if the file exists
        if [[ -f $file ]]; then
            echo "Adding $file to the tar archive."
            files_to_tar="${files_to_tar} ${file}"
        fi
    done
    for file in scan${scan_number}.dm4; do
        if [[ -f $file ]]; then
            echo "Adding $file to the tar archive."
            files_to_tar="${files_to_tar} ${file}"
        fi
    done
done

# Create the tar archive
if [[ ! -z "$files_to_tar" ]]; then
    tar -cvf - $files_to_tar | pigz --best -v -p 100 > processed_data.tar.gz 
else
    echo "No files match the pattern and scan number range."
fi
