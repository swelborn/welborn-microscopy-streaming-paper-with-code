#!/bin/bash

#SBATCH --qos=debug
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --time=00:30:00
#SBATCH --job-name=binning_insitu_datasets
#SBATCH --exclusive
#SBATCH --account=m3795

srun -n 1 -N 1 \
    podman-hpc run \
        -v ${WORKING_DIR}/../ptycho:/analysis/ptycho \
        -v ${COUNTED_DATA_DIR}:/mnt/counted_data \
        -v ${SCRIPTS_DIR}:/analysis/scripts \
        -v ${CONFIG_DIR}:/analysis/config \
        samwelborn/streaming-paper-ptycho:latest \
            python /analysis/scripts/bin.py \
            --config_file="/analysis/config/general_config.json"