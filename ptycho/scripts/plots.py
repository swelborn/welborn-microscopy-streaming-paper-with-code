import os
import re
import sys
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import ncempy
import numpy as np
import py4DSTEM
from scipy import ndimage

sys.path.append("/analysis/")
from ptycho.schemas import Config
from ptycho.utils import load_and_validate_config_json

# This is due to a bug in py4dstem - we can't load a dataset that was created
# using a GPU on a CPU-based machine
# see https://github.com/py4dstem/py4DSTEM/issues/540
gpu_on = False
try:
    import cupy as cp

    gpu_on = True
except:
    print("Cupy couldn't be imported, using ptycho NPY files...")


def load_hdf5_data(config: Config, processed_path: Path, orig_path: Path):
    extracted_data = {}
    middle_group = f"bin_{config.binning.bin_diffraction_factor}"
    base_datapath = f"{orig_path.stem}/{middle_group}/{orig_path.stem}/"

    ptycho_npy_path = config.outputs.ptycho_npy_dir / (
        str(orig_path.stem) + "_rotated_object.npy"
    )
    extracted_data["ptycho"] = np.load(ptycho_npy_path)

    with h5py.File(processed_path, "r") as f:

        extracted_data["parallax_aberration_A1x"] = float(
            f[base_datapath + "parallax/aberration_A1x"][()].item()
        )
        extracted_data["parallax_aberration_A1y"] = float(
            f[base_datapath + "parallax/aberration_A1y"][()].item()
        )
        extracted_data["parallax_aberration_C1"] = float(
            f[base_datapath + "parallax/aberration_C1"][()].item()
        )
        extracted_data["parallax_rotation_Q_to_R_rads"] = float(
            f[base_datapath + "parallax/rotation_Q_to_R_rads"][()].item()
        )
        extracted_data["parallax_recon_phase_corrected"] = np.array(
            f[base_datapath + "parallax/recon_phase_corrected"]
        )

    return extracted_data


def get_paths(config: Config):
    """
    Loads multiple datasets in a given range and returns a list of dictionaries containing the extracted data.
    """
    base_path = config.experiment.data_base_path

    # Function to extract the sort key from the filename
    def sort_key(filename):
        match = re.search(r"(\d+)_binned_calibrated", filename)
        if match:
            return int(match.group(1))
        else:
            return 0  # Default sort key

    def remove_suffix(filename):
        return filename.replace("_binned_calibrated", "")

    # List the contents of the current directory
    directory_contents = os.listdir(base_path)

    # Filter the files that start with "FOURD"
    processed_paths = [
        f for f in directory_contents if f.endswith("_binned_calibrated.h5")
    ]

    # Sort the files based on the last number before "_binned_calibrated"
    processed_paths = sorted(processed_paths, key=sort_key)

    # The list sorted_fourd_files now contains the paths sorted as required
    counted_paths = [base_path / Path(remove_suffix(path)) for path in processed_paths]
    processed_paths = [base_path / Path(path) for path in processed_paths]

    return processed_paths, counted_paths


def extract_shifts(config: Config, extracted_datas):
    stack = [np.angle(e["ptycho"]) for e in extracted_datas]
    image3d = np.stack(stack, axis=0)
    image3d_smooth = np.zeros_like(image3d)
    for ii, im in enumerate(image3d):
        image3d_smooth[ii, :, :] = ndimage.gaussian_filter(im, 2)
    alg, shifts = ncempy.eval.stack_align(
        image3d_smooth[:, 20:-20, 20:-20],
        upsample_factor=50,
        align_type="dynamic",
        method="cross",
    )
    shiftx = shifts[:, 1]
    shifty = shifts[:, 0]
    return shiftx, shifty


def return_scaled_histogram_ordering(array, vmin=None, vmax=None, normalize=False):
    """
    Utility function for calculating min and max values for plotting array
    based on distribution of pixel values

    Parameters
    ----------
    array: np.array
        array to be plotted
    vmin: float
        lower fraction cut off of pixel values
    vmax: float
        upper fraction cut off of pixel values
    normalize: bool
        if True, rescales from 0 to 1

    Returns
    ----------
    scaled_array: np.array
        array clipped outside vmin and vmax
    vmin: float
        lower value to be plotted
    vmax: float
        upper value to be plotted
    """

    if vmin is None:
        vmin = 0.02
    if vmax is None:
        vmax = 0.98

    vals = np.sort(array.ravel())
    ind_vmin = np.round((vals.shape[0] - 1) * vmin).astype("int")
    ind_vmax = np.round((vals.shape[0] - 1) * vmax).astype("int")
    ind_vmin = np.max([0, ind_vmin])
    ind_vmax = np.min([len(vals) - 1, ind_vmax])
    vmin = vals[ind_vmin]
    vmax = vals[ind_vmax]

    if vmax == vmin:
        vmin = vals[0]
        vmax = vals[-1]

    scaled_array = array.copy()
    scaled_array = np.where(scaled_array < vmin, vmin, scaled_array)
    scaled_array = np.where(scaled_array > vmax, vmax, scaled_array)

    if normalize:
        scaled_array -= scaled_array.min()
        scaled_array /= scaled_array.max()
        vmin = 0
        vmax = 1

    return scaled_array, vmin, vmax


def plot_threepane(config: Config, extracted_datas):
    fig, axs = plt.subplots(2, 3, figsize=(6.5, 4))

    # Different bounds because of cropping in parallax, rotating in ptycho
    x_low = [70, 70]
    x_high = [300, 280]
    y_low = [10, 10]
    y_high = [240, 220]
    indexes: list = [0, 33, 56]

    def plot_parallax_ptycho(column, index):
        data = extracted_datas[index]
        ptycho = data["ptycho"]
        parallax = -data["parallax_recon_phase_corrected"]
        _, vmin_parallax, vmax_parallax = return_scaled_histogram_ordering(
            parallax, vmin=0.2, vmax=0.98
        )

        _, vmin_ptycho, vmax_ptycho = return_scaled_histogram_ordering(
            np.angle(ptycho), vmin=0.2, vmax=0.98
        )

        axs[0, column].imshow(
            parallax, cmap="magma", vmin=vmin_parallax, vmax=vmax_parallax
        )
        axs[1, column].imshow(
            np.angle(ptycho), cmap="magma", vmin=vmin_ptycho, vmax=vmax_ptycho
        )

    for axis, index in zip([0, 1, 2], indexes):
        plot_parallax_ptycho(axis, index)

    for row in np.arange(0, 2):
        for column in np.arange(0, 3):
            axs[row, column].axis("off")
            axs[row, column].set_xlim([x_low[row], x_high[row]])
            axs[row, column].set_ylim([y_high[row], y_low[row]])

    plt.tight_layout()
    fig.savefig(
        str(config.outputs.plots_dir / "parallax_ptycho_threepane.png"),
        dpi=600,
        bbox_inches="tight",
    )


def plot_aberrations(config: Config, extracted_datas, shifts):
    time_range = np.arange(0, 55, 55 / 60)
    parallax_aberration_A1x = [
        data["parallax_aberration_A1x"] for data in extracted_datas
    ]
    parallax_aberration_A1y = [
        data["parallax_aberration_A1y"] for data in extracted_datas
    ]
    parallax_aberration_C1 = [
        data["parallax_aberration_C1"] for data in extracted_datas
    ]

    # Create subplots
    fig, axs = plt.subplots(1, 3, figsize=(6.5, 2.25))
    linewidth = 0.75

    # C1
    axs[0].plot(
        time_range,
        parallax_aberration_C1,
        color=config.plot.red_color,
        linewidth=linewidth,
    )
    axs[0].legend(["Defocus"], fontsize=config.plot.tick_font_size, frameon=False)

    # A1X
    axs[1].plot(
        time_range,
        parallax_aberration_A1x,
        color=config.plot.blue_color,
        linewidth=linewidth,
    )

    # A1y
    axs[1].plot(
        time_range,
        parallax_aberration_A1y,
        color=config.plot.green_color,
        linewidth=linewidth,
    )

    axs[1].legend(["X", "Y"], fontsize=config.plot.tick_font_size, frameon=False)

    pixel_size = 0.039592798608737967  # nanometers, from ptycho.sampling
    # Shifts
    shiftx, shifty = shifts[0], shifts[1]
    axs[2].plot(
        time_range,
        shiftx * pixel_size,
        linewidth=linewidth,
        color=config.plot.blue_color,
    )

    axs[2].plot(
        time_range,
        shifty * pixel_size,
        linewidth=linewidth,
        color=config.plot.green_color,
    )

    for index in [0, 1, 2]:
        axs[index].tick_params(axis="both", labelsize=config.plot.tick_font_size)
        axs[index].set_xlabel("Time (min)", fontsize=config.plot.label_font_size)
        axs[index].set_xlim(-5, 60)
        if index != 2:
            axs[index].set_ylabel(
                "Aberration (\u212B)", fontsize=config.plot.label_font_size
            )
        else:
            axs[index].legend(
                ["X drift", "Y drift"],
                fontsize=config.plot.tick_font_size,
                frameon=False,
            )
            axs[index].set_ylabel("Distance (nm)", fontsize=config.plot.label_font_size)

    plt.tight_layout()
    plt.subplots_adjust(top=0.85)

    fig.savefig(
        str(config.outputs.plots_dir / "parallax_aberration_analysis.png"),
        dpi=600,
        bbox_inches="tight",
    )


def main() -> None:
    config = load_and_validate_config_json(Path("/analysis/config/general_config.json"))

    # Find all paths
    processed_paths, orig_paths = get_paths(config)

    extracted_datas = []
    for processed_path, orig_path in zip(processed_paths, orig_paths):
        extracted_datas.append(load_hdf5_data(config, processed_path, orig_path))

    shiftx, shifty = extract_shifts(config, extracted_datas)

    # Perform Visualizations
    plot_threepane(config, extracted_datas)
    plot_aberrations(config, extracted_datas, (shiftx, shifty))


if __name__ == "__main__":
    main()
