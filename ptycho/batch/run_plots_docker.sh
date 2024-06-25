#!/bin/bash

cd $(dirname "$0")
source ./set_environment.sh

docker run --rm \
    --mount type=bind,source=${WORKING_DIR}/../ptycho,target=/analysis/ptycho \
    --mount type=bind,source=${COUNTED_DATA_DIR},target=/mnt/counted_data \
    --mount type=bind,source=${OUTPUTS_DIR},target=/analysis/outputs \
    --mount type=bind,source=${SCRIPTS_DIR},target=/analysis/scripts \
    --mount type=bind,source=${CONFIG_DIR},target=/analysis/config \
    --mount type=bind,source=${PTYCHO_NPY_DIR},target=/analysis/outputs/ptycho_npy \
    samwelborn/streaming-paper-plots:latest \
        python /analysis/scripts/plots.py