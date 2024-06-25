import os
import hashlib
from multiprocessing import Pool
import pathlib

def read_md5sums(file_path):
    """Read MD5 checksums from a file and return as a dictionary."""
    md5_dict = {}
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split(': ')
            if len(parts) == 2:
                md5_dict[parts[0]] = parts[1]
    return md5_dict

def calculate_md5(file_path):
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return file_path, hash_md5.hexdigest()

def compare_md5(file_info):
    """Compare MD5 checksum of a file with the expected checksum."""
    file_path, expected_md5 = file_info
    _, actual_md5 = calculate_md5(file_path)
    return file_path, expected_md5 == actual_md5, actual_md5

def main(md5sums_file, directory, output_file, num_processes=4):
    # Read expected MD5 checksums
    expected_md5s = read_md5sums(md5sums_file)
    
    # Create list of files to check with their expected checksums
    file_list = []
    for file_name, expected_md5 in expected_md5s.items():
        file_path = os.path.join(directory, file_name)
        if os.path.exists(file_path):
            file_list.append((file_path, expected_md5))

    # Compare MD5 checksums using multiprocessing
    with Pool(processes=num_processes) as pool:
        results = pool.map(compare_md5, file_list)
    
    # Write comparison results to the output file
    with open(output_file, "w") as f:
        for file_path, is_match, actual_md5 in results:
            status = "MATCH" if is_match else "MISMATCH"
            f.write(f"{file_path}: {status} (expected: {expected_md5s[os.path.basename(file_path)]}, actual: {actual_md5})\n")


if __name__ == "__main__":
    
    HERE = pathlib.Path(__file__).parent
    # Path to the file containing the expected MD5 checksums
    md5sums_file = str(HERE / "md5sums.txt")
    # Directory containing the downloaded and extracted files
    directory = "/pscratch/sd/s/swelborn/streaming-paper/counted_data/untarred"  # Update this path to your directory
    # Output file to save the comparison results
    output_file = "comparison_results.txt"
    # Number of processes to use for multiprocessing
    num_processes = 20

    main(md5sums_file, directory, output_file, num_processes)
    print(f"Comparison results saved to {output_file}")
