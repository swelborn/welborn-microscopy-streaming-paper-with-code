import argparse
import logging
import sys
from pathlib import Path
from typing import List

import cupy as cp
import h5py
import py4DSTEM
from mpi4py import MPI
from stempy.contrib import get_scan_path

sys.path.append("/analysis")


from ptycho.schemas import DPC, AnalysisConfig, Config
from ptycho.utils import (
    check_for_invalid_values,
    check_for_zero_slices,
    load_and_validate_analysis_json,
    load_and_validate_config_json,
    replace_invalid_values,
    replace_zero_slices,
)

# Configure logging to file
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Configure logging to stdout
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logging.getLogger("").addHandler(console_handler)


def save_data(scan_path, config, output_filename, save_parallax_items, save_matrix):
    try:
        with h5py.File(output_filename, "a") as f:
            middle_group: str = f"bin_{config.binning.bin_diffraction_factor}"

            # Save items in save_matrix
            for k, v in save_matrix.items():
                logging.info(f"Saving {k} for {scan_path.stem}.")
                group_path = f"{scan_path.stem}/{middle_group}/{scan_path.stem}/{k}"
                logging.info(f"Group path: {group_path}")
                # Check if the group already exists and delete it
                if group_path in f:
                    del f[group_path]

                # Create the new group
                group = f.create_group(group_path)

                # Save the new dataset
                v.to_h5(group)

            # Save items in save_parallax_items
            group_path = f"{scan_path.stem}/{middle_group}/{scan_path.stem}/parallax"

            # Check if the group already exists and delete it
            if group_path in f:
                del f[group_path]

            # Create the new group
            group = f.create_group(group_path)

            for k, v in save_parallax_items.items():
                # Create the new dataset
                group.create_dataset(k, data=v)

            logging.info(f"Data saved successfully for {scan_path.stem}.")

    except Exception as e:
        logging.error(f"An error occurred while saving data for {scan_path}: {e}")


def process_scan(
    scan_path: Path,
    config: Config,
    analysis_config: AnalysisConfig,
) -> None:
    # Load the binned dataset
    output_filename: Path = scan_path.with_stem(scan_path.stem + "_binned_calibrated")

    logging.info(f"Reading datacube file: {output_filename}")
    datacube: py4DSTEM.DataCube = py4DSTEM.read(output_filename).tree(scan_path.stem)
    invalid_values = check_for_invalid_values(scan_path.stem, datacube.data)

    # invalid values and zero slices from datacube
    if invalid_values:
        logging.info(f"invalid values file: {output_filename}")
        datacube.data = replace_invalid_values(datacube.data, invalid_values)

    all_zero_slices = check_for_zero_slices(scan_path.stem, datacube.data)
    if all_zero_slices:
        logging.info(f"all zeros file: {output_filename}")
        datacube.data = replace_zero_slices(datacube.data, all_zero_slices)

    device: str = analysis_config.compute.device
    energy: int = config.microscope.beam_energy
    probe_radius_pixels = datacube.metadata["preprocessing_metadata"][
        "probe_radius_pixels"
    ]

    # BF/DF can be done, but no need for purpose of this paper.
    # expand_BF = analysis_config.bf_df.expand_BF
    # probe_qx0 = datacube.metadata["preprocessing_metadata"]["probe_qx0"]
    # probe_qy0 = datacube.metadata["preprocessing_metadata"]["probe_qy0"]
    # center = (probe_qx0, probe_qy0)
    # radius_BF = probe_radius_pixels + expand_BF
    # radii_DF = (probe_radius_pixels + expand_BF, analysis_config.bf_df.extra_radius)

    # datacube.get_virtual_image(
    #     mode="circle",
    #     geometry=(center, radius_BF),
    #     name="bright_field",
    #     shift_center=False,
    # )
    # datacube.get_virtual_image(
    #     mode="annulus",
    #     geometry=(center, radii_DF),
    #     name="dark_field",
    #     shift_center=False,
    # )

    # DPC
    logging.info(f"Performing DPC file: {output_filename}")
    dpc = py4DSTEM.process.phase.DPCReconstruction(
        datacube=datacube, energy=energy, device=device
    ).preprocess(force_com_rotation=analysis_config.dpc.preprocess.force_com_rotation)

    dpc = dpc.reconstruct(
        reset=analysis_config.dpc.reconstruct.reset,
        q_highpass=analysis_config.dpc.reconstruct.q_highpass,
        store_iterations=analysis_config.dpc.reconstruct.store_iterations,
    )

    # Parallax
    logging.info(f"Performing parallax file: {output_filename}")
    datacube_cropped = datacube.copy()
    datacube_cropped.crop_R(
        (
            analysis_config.parallax.crop_R.x_min,
            analysis_config.parallax.crop_R.x_max,
            analysis_config.parallax.crop_R.y_min,
            analysis_config.parallax.crop_R.y_max,
        )
    )
    parallax = py4DSTEM.process.phase.ParallaxReconstruction(
        datacube=datacube_cropped,
        energy=energy,
        device=device,
        object_padding_px=analysis_config.parallax.instantiation.object_padding_px,
    ).preprocess(
        threshold_intensity=analysis_config.parallax.preprocess.threshold_intensity,
        edge_blend=analysis_config.parallax.preprocess.edge_blend,
        defocus_guess=analysis_config.parallax.preprocess.defocus_guess,
        rotation_guess=analysis_config.parallax.preprocess.rotation_guess,
    )

    parallax = parallax.reconstruct(
        reset=analysis_config.parallax.reconstruct.reset,
        min_alignment_bin=analysis_config.parallax.reconstruct.min_alignment_bin,
        max_iter_at_min_bin=analysis_config.parallax.reconstruct.max_iter_at_min_bin,
        running_average=analysis_config.parallax.reconstruct.running_average,
        plot_aligned_bf=False,
        plot_convergence=False,
    )

    parallax.aberration_fit()
    parallax.aberration_correct()

    # Ptycho
    logging.info(f"Performing ptycho file: {output_filename}")
    defocus = -parallax.aberration_C1

    ptycho = py4DSTEM.process.phase.SingleslicePtychographicReconstruction(
        datacube=datacube,
        device=device,
        energy=energy,
        semiangle_cutoff=17.1,
        defocus=0,
    ).preprocess(
        force_com_transpose=analysis_config.ptycho.preprocess.force_com_transpose,
        force_com_rotation=analysis_config.ptycho.preprocess.force_com_rotation,
        fit_function=analysis_config.ptycho.preprocess.fit_function,
        plot_center_of_mass=False,
    )

    ptycho = ptycho.reconstruct(
        reset=analysis_config.ptycho.reconstruct.reset,
        max_iter=analysis_config.ptycho.reconstruct.max_iter,
        step_size=analysis_config.ptycho.reconstruct.step_size,
        max_batch_size=ptycho._num_diffraction_patterns // 2,
        q_lowpass=analysis_config.ptycho.reconstruct.q_lowpass,
        store_iterations=analysis_config.ptycho.reconstruct.store_iterations,
    )

    save_parallax_items: dict = {
        "recon_phase_corrected": parallax.recon_phase_corrected,
        "_scan_sampling": parallax._scan_sampling,
        "rotation_Q_to_R_rads": parallax.rotation_Q_to_R_rads,
        "aberration_A1x": parallax.aberration_A1x,
        "aberration_A1y": parallax.aberration_A1y,
        "aberration_C1": parallax.aberration_C1,
    }

    # No need to save dpc
    save_matrix: dict = {"ptycho": ptycho}

    save_data(scan_path, config, output_filename, save_parallax_items, save_matrix)


def main():
    # Initialize MPI
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Argument parsing and configuration loading
    # Only the root process should do this
    if rank == 0:
        parser = argparse.ArgumentParser(description="Process 4D STEM data.")
        parser.add_argument(
            "--config_file",
            type=Path,
            default="/analysis/config/general_config.json",
            help="Path to the configuration file.",
        )
        parser.add_argument(
            "--analysis_config_file",
            type=Path,
            default="/analysis/config/dpc_parallax_ptycho_params.json",
            help="Path to the analysis configuration file.",
        )
        args = parser.parse_args()

        # Load and validate configuration
        config: Config = load_and_validate_config_json(Path(args.config_file))
        analysis_config: AnalysisConfig = load_and_validate_analysis_json(
            Path(args.analysis_config_file)
        )

        # Find scan paths
        scan_paths: List[Path] = []

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

        # Divide the scan_paths among all available ranks
        avg_num_scan_paths: int = len(scan_paths) // size
        remainder: int = len(scan_paths) % size
        num_datasets: List[int] = [
            avg_num_scan_paths + 1 if i < remainder else avg_num_scan_paths
            for i in range(size)
        ]
        displacements: List[int] = [sum(num_datasets[:i]) for i in range(size)]

        logging.info(f"Rank {rank} sending counts: {num_datasets}")
        logging.info(f"Rank {rank} sending displacements: {displacements}")
    else:
        scan_paths = []
        num_datasets = []
        displacements = []
        config = None  # type: ignore
        analysis_config = None  # type: ignore

    # Broadcast configurations to all ranks
    config = comm.bcast(config, root=0)
    analysis_config = comm.bcast(analysis_config, root=0)

    # Broadcast paths, counts, and displacements to all ranks
    num_datasets = comm.bcast(num_datasets, root=0)
    displacements = comm.bcast(displacements, root=0)
    scan_paths = comm.bcast(scan_paths, root=0)

    # Calculate the range of scan_paths for this rank
    start_idx = displacements[rank]
    end_idx = start_idx + num_datasets[rank]

    # Process the data
    for scan_path in scan_paths[start_idx:end_idx]:
        logging.info(f"Rank {rank} processing file: {scan_path.stem}")
        process_scan(scan_path, config, analysis_config)


if __name__ == "__main__":
    main()
