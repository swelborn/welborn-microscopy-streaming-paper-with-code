import argparse
import datetime
import sys
import time
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List

import emdfile as emd
import py4DSTEM
import stempy.io as stio
from stempy.contrib import get_scan_path


sys.path.append("/analysis")

from ptycho.schemas import Config
from ptycho.utils import check_memory_usage, load_and_validate_config_json


def process_scan(
    scan_path: Path,
    scan_id: int,
    scan_num: int,
    config: Config,
    relative_acquisition_time: datetime.timedelta,
    vacuum_probe: py4DSTEM.Array,
) -> None:
    while check_memory_usage():
        print("Memory usage above 90%. Waiting...")
        time.sleep(10)  # Wait for 10 seconds before checking again

    # Load the sparse 4D Camera dataset
    stempy_sparse_array: stio.SparseArray = stio.SparseArray.from_hdf5(scan_path)

    # Remove flyback row and first column
    stempy_sparse_array = stempy_sparse_array[:, :-1, :, :]
    stempy_sparse_array = stempy_sparse_array[1:, :, :, :]

    # Crop real space
    x_min = config.crop_full_data.x_min
    x_max = config.crop_full_data.x_max
    y_min = config.crop_full_data.y_min
    y_max = config.crop_full_data.y_max
    stempy_sparse_array = stempy_sparse_array[y_min:y_max, x_min:x_max, :, :]

    # Bin
    stempy_sparse_array_binned: stio.SparseArray = stempy_sparse_array.bin_frames(
        config.binning.bin_diffraction_factor
    )
    datacube: py4DSTEM.DataCube = py4DSTEM.DataCube(
        stempy_sparse_array_binned.to_dense(), name=scan_path.stem
    )

    # Calibration
    probe_radius_pixels, probe_qx0, probe_qy0 = datacube.get_probe_size(
        vacuum_probe.data, plot=False, thresh_upper=0.95
    )
    r_pixel_size: float = config.microscope.r_pixel_size
    r_pixel_units: str = config.microscope.r_pixel_units
    convergence_semiangle: float = config.microscope.convergence_semiangle
    q_pixel_size: float = convergence_semiangle / probe_radius_pixels
    q_pixel_units: str = config.microscope.q_pixel_units

    file_metadata = {
        "scan_num": scan_num,
        "distiller_id": scan_id,
        "relative_acquisition_time": relative_acquisition_time.seconds,
    }
    preprocessing_metadata = {
        "stempy_frame_bin_factor": config.binning.bin_diffraction_factor,
        "removed_first_column": True,
        "removed_flyback_row": True,
        "crop_Rx_start": x_min,
        "crop_Rx_end": x_max,
        "crop_Ry_start": y_min,
        "crop_Ry_end": y_max,
        "probe_qx0": probe_qx0,
        "probe_qy0": probe_qy0,
        "probe_radius_pixels": probe_radius_pixels,
    }

    datacube.metadata = emd.Metadata(name="file_metadata", data=file_metadata)
    datacube.metadata = emd.Metadata(
        name="preprocessing_metadata", data=preprocessing_metadata
    )

    datacube.calibration.set_R_pixel_size(r_pixel_size)
    datacube.calibration.set_R_pixel_units(r_pixel_units)
    datacube.calibration.set_Q_pixel_size(q_pixel_size)
    datacube.calibration.set_Q_pixel_units(q_pixel_units)

    # Create emd root
    root = emd.Root(name=scan_path.stem)

    # Add node
    node = emd.Node(name=f"bin_{config.binning.bin_diffraction_factor}")
    root.tree(node)
    node.tree(graft=datacube)
    node.tree(graft=vacuum_probe)
    output_filename: Path = scan_path.with_stem(scan_path.stem + "_binned_calibrated")

    py4DSTEM.save(output_filename, root, mode="o")


def main() -> None:
    # Argument parsing
    parser = argparse.ArgumentParser(description="Process 4D STEM data.")
    parser.add_argument(
        "--config_file",
        type=str,
        default="/analysis/config/general_config.json",
        help="Path to the configuration file.",
    )
    args = parser.parse_args()

    # Load and validate configuration
    config: Config = load_and_validate_config_json(Path(args.config_file))

    # Find scan paths/numbers
    scan_paths: List[Path] = []
    scan_ids: List[int] = []
    scan_nums: List[int] = []
    relative_acquisition_times: List[datetime.timedelta] = []

    # Fill in the lists
    min_scan_num = config.experiment.min_scan_num
    max_scan_num = config.experiment.max_scan_num
    base_path = config.experiment.data_base_path
    for scan_num in range(min_scan_num, max_scan_num + 1):
        scan_path, scan_num, scan_id = get_scan_path(
            base_path, scan_num=scan_num, version=1
        )
        if scan_path and scan_num and scan_id:
            scan_paths.append(scan_path)
            scan_nums.append(scan_num)
            scan_ids.append(scan_id)
            seconds_offset = (
                scan_num - min_scan_num
            ) * config.experiment.seconds_between_scans
            relative_acquisition_time = datetime.timedelta(seconds=seconds_offset)
            relative_acquisition_times.append(relative_acquisition_time)

    # Get probe
    fp_probe: Path = config.calibration.vacuum_probe_emd_path
    probe: py4DSTEM.Array = py4DSTEM.read(fp_probe)

    # Run the process_scan function in parallel for each scan path and associated haadf path
    futures: List[Future] = []
    with ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(
                process_scan,
                scan_paths[i],
                scan_ids[i],
                scan_nums[i],
                config,
                relative_acquisition_times[i],
                probe,
            )
            for i in range(len(scan_paths))
        ]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"An exception occurred during parallel execution: {e}")


if __name__ == "__main__":
    main()
