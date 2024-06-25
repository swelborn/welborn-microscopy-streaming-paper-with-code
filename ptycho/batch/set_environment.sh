#!/bin/bash

# Initialize and export environment variables

THIS_SCRIPT_DIR=$(dirname "$0")
export WORKING_DIR=$(realpath "${THIS_SCRIPT_DIR}")
CONFIG_DIR=$(realpath "${WORKING_DIR}/../config")
export PATHS_CONFIG_PATH=$(realpath "${CONFIG_DIR}/external_paths.json")

# Read variables from the JSON file using jq
export COUNTED_DATA_DIR=$(jq -r '.counted_data_dir' ${PATHS_CONFIG_PATH})
export OUTPUTS_DIR=$(jq -r '.outputs_dir' ${PATHS_CONFIG_PATH})
export SCRIPTS_DIR=$(jq -r '.scripts_dir' ${PATHS_CONFIG_PATH})
export CONFIG_DIR=$(jq -r '.config_dir' ${PATHS_CONFIG_PATH})
export PTYCHO_NPY_DIR=$(jq -r '.ptycho_npy_dir' ${PATHS_CONFIG_PATH})

# Validate that the variables were set correctly
if [ -z "$COUNTED_DATA_DIR" ] \
    || [ -z "$OUTPUTS_DIR" ] \
    || [ -z "$SCRIPTS_DIR" ] \
    || [ -z "$CONFIG_DIR" ] \
    || [ -z "$PTYCHO_NPY_DIR" ] \
    ; then
    echo "Error: Failed to read necessary paths from JSON configuration."
    exit 1
fi

# Print out the environment variables in a readable format
echo "----------------------------------------------"
echo "Environment Variables:"
echo "----------------------------------------------"
echo "WORKING_DIR: $WORKING_DIR"
echo "PATHS_CONFIG_PATH: $PATHS_CONFIG_PATH"
echo "COUNTED_DATA_DIR: $COUNTED_DATA_DIR"
echo "OUTPUTS_DIR: $OUTPUTS_DIR"
echo "SCRIPTS_DIR: $SCRIPTS_DIR"
echo "CONFIG_DIR: $CONFIG_DIR"
echo "PTYCHO_NPY_DIR: $PTYCHO_NPY_DIR"
echo "----------------------------------------------"
