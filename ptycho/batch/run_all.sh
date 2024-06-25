#!/bin/bash

cd $(dirname "$0")
source ./set_environment.sh

# Create vacuum probe
podman-hpc run --rm \
    -v ${WORKING_DIR}/../ptycho:/analysis/ptycho \
    -v ${COUNTED_DATA_DIR}:/mnt/counted_data \
    -v ${SCRIPTS_DIR}:/analysis/scripts \
    -v ${CONFIG_DIR}:/analysis/config \
    samwelborn/streaming-paper-ptycho:latest \
        python /analysis/scripts/vacuum_probe.py

# Bin all datasets
jobid_bin=$(sbatch --parsable ./bin.sh)

# DPC/Parallax/Ptycho
jobid_dpc=$(sbatch --parsable --dependency=afterok:$jobid_bin ./dpc_parallax_ptycho.sh)

# Loop to check the status of the job with ID stored in jobid_dpc
while [ "$(squeue -j $jobid_dpc --noheader)" ]; do
  echo "Job $jobid_dpc is still running or queued."
  sleep 30 
done

# Create plots
podman-hpc run --rm --gpu \
    -v ${WORKING_DIR}/../ptycho:/analysis/ptycho \
    -v ${COUNTED_DATA_DIR}:/mnt/counted_data \
    -v ${OUTPUTS_DIR}:/analysis/outputs \
    -v ${SCRIPTS_DIR}:/analysis/scripts \
    -v ${CONFIG_DIR}:/analysis/config \
    -v ${PTYCHO_NPY_DIR}:/analysis/outputs/ptycho_npy \
    samwelborn/streaming-paper-ptycho:latest \
        python /analysis/scripts/rotate_ptychos.py

# Create plots
podman-hpc run --rm --gpu \
    -v ${WORKING_DIR}/../ptycho:/analysis/ptycho \
    -v ${COUNTED_DATA_DIR}:/mnt/counted_data \
    -v ${OUTPUTS_DIR}:/analysis/outputs \
    -v ${SCRIPTS_DIR}:/analysis/scripts \
    -v ${CONFIG_DIR}:/analysis/config \
    -v ${PTYCHO_NPY_DIR}:/analysis/outputs/ptycho_npy \
    samwelborn/streaming-paper-ptycho:latest \
        python /analysis/scripts/plots.py