import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import stempy.contrib as contrib

# Assuming the location of the current script is the same as 'inputs.json'
HERE = Path(__file__).parent


def posix_to_datetime(file_path: Path) -> Optional[datetime]:
    """
    Reads the POSIX file creation time and converts it to a datetime format.

    Args:
        file_path (Path): The file path to get the creation time for.

    Returns:
        datetime: The datetime object representing the creation time.
    """
    try:
        # Get the file's creation time as a POSIX timestamp
        creation_time = file_path.stat().st_ctime

        # Convert the POSIX timestamp to a datetime object, aware of the UTC timezone
        datetime_obj = datetime.fromtimestamp(creation_time, tz=timezone.utc)
        return datetime_obj
    except OSError as e:
        print(f"Error getting creation time for {file_path}: {e}")
        return None


def list_files(directory: Path, extension: str) -> List[Path]:
    """
    Lists all files in a given directory with a specific extension.
    """
    return [
        file for file in directory.glob(f"*{extension}") if "_centered" not in str(file)
    ]


def match_files(
    dm4_dir: Path,
    hdf5_dir: Path,
    image_ext: str,
    data_ext: str,
    scan_range: Tuple[int, int],
) -> List[tuple[Path, Path]]:
    """
    Matches files in two directories based on sequence numbers in their names and filters them by a given scan range.
    """
    dm4_files = list_files(dm4_dir, image_ext)
    # files2 = list_files(hdf5_dir, data_ext)
    matched_files = []

    for dm4_file in dm4_files:
        scan_num = int(dm4_file.stem.split("scan")[-1])
        if scan_range[0] <= scan_num <= scan_range[1]:
            try:
                hdf5_file, _, _ = contrib.get_scan_path(hdf5_dir, scan_num=scan_num)
                matched_files.append((scan_num, dm4_file, hdf5_file))
            except FileNotFoundError:
                continue
            except ValueError:
                continue

    matched_files.sort(key=lambda x: int(x[0]))
    return matched_files


def write_to_csv(matched_data: List[Dict], csv_filename: Union[Path, str]):
    """
    Writes matched files information to a CSV, including new columns for creation dates and duration.
    """
    headers = [
        "Description",
        "Date",
        "ScanNo",
        "DM4 Path",
        "H5 Path",
        "Streaming",
        "DM4 DateTime",
        "HDF5 DateTime",
        "Duration (s)",
    ]

    with open(csv_filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for item in matched_data:
            writer.writerows(item["rows"])


def calculate_duration(dm4_path: Path, h5_path: Path) -> Optional[float]:
    """
    Calculate the duration in seconds between the creation times of a .dm4 file and its corresponding .h5 file.
    """
    dm4_datetime = posix_to_datetime(dm4_path)
    hdf5_datetime = posix_to_datetime(h5_path)

    if dm4_datetime and hdf5_datetime:
        duration_seconds = (hdf5_datetime - dm4_datetime).total_seconds()
        return duration_seconds
    return None


def process_datasets(datasets):
    """
    Processes datasets to match files, calculate durations, and write results to a CSV.
    """
    all_data = []

    for dataset in datasets:
        dm4_dir = Path(dataset["dm4_dir"])
        data_dir = Path(dataset["data_dir"])
        scan_range = tuple(dataset["scan_range"])

        data_extension: str = ".h5"
        if "data_extension" in dataset:
            data_extension = dataset["data_extension"]

        matched_files = match_files(
            dm4_dir, data_dir, ".dm4", data_extension, scan_range
        )

        rows = []
        for scan_num, dm4_path, h5_path in matched_files:
            duration_seconds = calculate_duration(dm4_path, h5_path)
            row = {
                "Description": dataset["description"],
                "Date": dataset["date"],
                "ScanNo": scan_num,
                "DM4 Path": dm4_path.as_posix(),
                "H5 Path": h5_path.as_posix(),
                "Streaming": dataset.get("streaming", False),
                "DM4 DateTime": (
                    posix_to_datetime(dm4_path).isoformat() if dm4_path else "N/A"
                ),
                "HDF5 DateTime": (
                    posix_to_datetime(h5_path).isoformat() if h5_path else "N/A"
                ),
                "Duration (s)": (
                    duration_seconds if duration_seconds is not None else "N/A"
                ),
            }
            rows.append(row)

        all_data.append({"rows": rows})

    write_to_csv(all_data, HERE / "matched_files.csv")


# Load datasets from 'inputs.json'
with open(HERE / "inputs.json", "r") as file:
    datasets = json.load(file)

# Process datasets
process_datasets(datasets)
