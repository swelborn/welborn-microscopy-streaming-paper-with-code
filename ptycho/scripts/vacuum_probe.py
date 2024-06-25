import py4DSTEM
import py4DSTEM
import stempy.io as stio
import emdfile as emd

from pathlib import Path
import sys

sys.path.append("/analysis/")

from ptycho.schemas import Config
from ptycho.utils import load_and_validate_config_json


def main():
    config_path: Path = Path("/analysis/config/general_config.json")
    config: Config = load_and_validate_config_json(config_path)

    # File paths
    file_data: Path = config.calibration.vacuum_probe_raw_path

    # Import the sparse array
    stempy_sparse_array: stio.SparseArray = stio.SparseArray.from_hdf5(file_data)

    # Remove flyback row and first column
    stempy_sparse_array = stempy_sparse_array[:, :-1, :, :]
    stempy_sparse_array = stempy_sparse_array[1:, :, :, :]

    # Bin reciprocal space by some factor
    bin_factor: int = config.binning.bin_diffraction_factor
    stempy_sparse_array_binned: stio.SparseArray = stempy_sparse_array.bin_frames(
        bin_factor
    )
    datacube = stempy_sparse_array_binned.to_dense()

    # Put into datacube
    datacube: py4DSTEM.DataCube = py4DSTEM.DataCube(datacube)

    # Define the x and y limits
    x_start, x_end = config.crop_vacuum_probe.x_min, config.crop_vacuum_probe.x_max
    y_start, y_end = config.crop_vacuum_probe.y_min, config.crop_vacuum_probe.y_max

    probe_datacube = py4DSTEM.DataCube(
        datacube.data[y_start:y_end, x_start:x_end, :, :]
    )
    probe = probe_datacube.data.sum(axis=(0, 1))
    probe = py4DSTEM.Array(probe, name=config.calibration.vacuum_probe_emd_path.stem)

    probe.metadata = emd.Metadata(
        name="metadata",
        data={"x_start": x_start, "x_end": x_end, "y_start": y_start, "y_end": y_end},
    )
    py4DSTEM.save(config.calibration.vacuum_probe_emd_path, probe)


if __name__ == "__main__":
    main()
