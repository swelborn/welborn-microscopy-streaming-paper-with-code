#!/bin/bash

cd $(dirname "$0")
source ./set_environment.sh

# Submit the job
sbatch ./dpc_parallax_ptycho.sh
