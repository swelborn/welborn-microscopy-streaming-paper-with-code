import sys
from pathlib import Path

import numpy as np
import py4DSTEM
from stempy.contrib import get_scan_path

sys.path.append("/analysis/")
from ptycho.schemas import Config
from ptycho.utils import load_and_validate_config_json


def load_ptycho_and_save_rotated(base_path: Path, scan_path: Path):
    """
    Loads HDF5 data given a scan path and returns a dictionary containing the extracted data.
    """
    output_filename: Path = scan_path.with_stem(scan_path.stem + "_binned_calibrated")
    middle_group = "bin_16"
    datapath = f"{scan_path.stem}/{middle_group}/{scan_path.stem}/ptycho/ptychographic_reconstruction"

    ptycho = py4DSTEM.read(
        output_filename,
        datapath=datapath,
    )
    obj = ptycho.object
    rotated_object = ptycho._crop_rotate_object_fov(obj)
    rotated_save_path = base_path / f"{scan_path.stem}_rotated_object.npy"
    np.save(rotated_save_path, rotated_object)


def load_multiple_datasets(
    base_path: Path, min_scan_num: int, max_scan_num: int, out_path: Path
):
    scan_paths = []
    for scan_num in range(min_scan_num, max_scan_num + 1):
        scan_path, scan_num, scan_id = get_scan_path(
            base_path, scan_num=scan_num, version=1
        )
        if scan_path and scan_num and scan_id:
            scan_paths.append(scan_path)

    for scan_path in scan_paths:
        load_ptycho_and_save_rotated(out_path, scan_path)


def main() -> None:
    config: Config = load_and_validate_config_json(
        Path("/analysis/config/general_config.json")
    )

    # Data Parameters
    processed_dir = config.experiment.data_base_path
    min_scan_num = config.experiment.min_scan_num
    max_scan_num = config.experiment.max_scan_num

    # Load Data
    load_multiple_datasets(
        processed_dir, min_scan_num, max_scan_num, config.outputs.ptycho_npy_dir
    )


if __name__ == "__main__":
    main()
