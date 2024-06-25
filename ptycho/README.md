# Data processing

## Build images

You have to build the images. There is a utility script `podman_hpc_build.sh` to do this. This will take a bit because I use mpi to run the jobs in parallel.

Here are the commands, if for some reason `podman_hpc_build.sh` doesn't work:

```bash
podman-hpc build -t samwelborn/streaming-paper-ptycho:latest .
podman-hpc migrate samwelborn/streaming-paper-ptycho:latest
podman-hpc build -t samwelborn/streaming-paper-ptycho-plots:latest -f Dockerfile.plots .
podman-hpc migrate samwelborn/streaming-paper-ptycho-plots:latest
```

## Change data paths

Change the data paths in `config/external_paths.json`

```json
{
    "counted_data_dir": "/pscratch/sd/s/swelborn/streaming-paper/counted_data", // this is where the raw downloaded data is located
    "outputs_dir": "/path/to/this/repo/code/ptycho/outputs", // you can change this to wherever, but just put it in the repo under ptycho/outputs
    "scripts_dir": "/path/to/this/repo/code/ptycho/scripts", // this needs to be where you installed this repo
    "batch_scripts_dir": "/path/to/this/repo/code/ptycho/batch", // this needs to be where you installed this repo
    "config_dir": "/path/to/this/repo/code/ptycho/config", // this needs to be where you installed this repo
    "ptycho_npy_dir": "/path/to/this/repo/code/ptycho/outputs/ptycho_npy" // you can change this to wherever, but just put it in the repo under ptycho/outputs/ptycho_npy
}
```

## Run

Run the entire processing pipeline by:

```sh
cd batch
chmod u+x run_all.sh
./run_all.sh
```
