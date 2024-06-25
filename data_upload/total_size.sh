#!/bin/bash

# Initialize a variable to hold the total size in kilobytes
total_size_kb=0

# Loop over the range of scan numbers
for scan_number in $(seq 516 575); do
    # Use a wildcard to match any file that fits the pattern
    for file in FOURD_*_*_*_00${scan_number}.h5; do
        # Check if the file exists
        if [[ -f $file ]]; then
            # Get the size of the file in kilobytes and add it to the total size
            file_size_kb=$(du -k "$file" | cut -f1)
            total_size_kb=$((total_size_kb + file_size_kb))
            echo "$file $file_size_kb KB"
        fi
    done
done

# Convert the total size to gigabytes (1 GB = 1024^2 KB)
total_size_gb=$(echo "scale=2; $total_size_kb / (1024^2)" | bc)

# Print the total size in gigabytes
echo "Total size of all matching datasets: ${total_size_gb} GB"
