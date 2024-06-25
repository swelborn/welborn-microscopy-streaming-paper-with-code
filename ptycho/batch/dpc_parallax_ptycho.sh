#!/bin/bash

#SBATCH --qos=debug
#SBATCH --constraint=gpu
#SBATCH --nodes=2
#SBATCH --time=00:30:00
#SBATCH --job-name=dpc_parallax_ptycho
#SBATCH --exclusive
#SBATCH --account=m3795

srun -n 8 -c 32 -G 8 --gpus-per-task=1 \
    podman-hpc run --mpi --gpu \
        -v ${WORKING_DIR}/../ptycho:/analysis/ptycho \
        -v ${COUNTED_DATA_DIR}:/mnt/counted_data \
        -v ${SCRIPTS_DIR}:/analysis/scripts \
        -v ${CONFIG_DIR}:/analysis/config \
        samwelborn/streaming-paper-ptycho:latest \
            python /analysis/scripts/dpc_parallax_ptycho.py \
            --config_file="/analysis/config/general_config.json" \
            --analysis_config_file="/analysis/config/dpc_parallax_ptycho_params.json"