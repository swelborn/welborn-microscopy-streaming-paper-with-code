import os
import pathlib
import re
import hashlib
from multiprocessing import Pool

def calculate_md5(file_path):
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return file_path, hash_md5.hexdigest()

def find_files(directory, pattern):
    """Find all files in a directory matching the given pattern."""
    regex = re.compile(pattern)
    matching_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if regex.match(file):
                matching_files.append(os.path.join(root, file))
    return matching_files

def save_md5sums(file_list, output_file, num_processes=4):
    """Save MD5 checksums of files to a text file using multiprocessing."""
    with Pool(processes=num_processes) as pool:
        results = pool.map(calculate_md5, file_list)
    
    with open(output_file, "w") as f:
        for file, md5sum in results:
            filename = pathlib.Path(file).name
            f.write(f"{filename}: {md5sum}\n")

if __name__ == "__main__":
    # Directory containing the files
    directory = "/pscratch/sd/s/swelborn/streaming-paper/counted_data"  # Update this path to your directory
    # Pattern to match files
    pattern = r'^FOURD_\d{6}_\d{4}_\d{5}_\d{5}\.h5$'
    # Output file to save the MD5 checksums
    output_file = "md5sums.txt"
    # Number of processes to use for multiprocessing
    num_processes = 20

    # Find matching files
    matching_files = find_files(directory, pattern)
    # Save MD5 checksums to the output file using multiprocessing
    save_md5sums(matching_files, output_file, num_processes)

    print(f"MD5 checksums saved to {output_file}")
