#!/bin/bash

podman-hpc build -t samwelborn/streaming-paper-ptycho:latest .
podman-hpc migrate samwelborn/streaming-paper-ptycho:latest
podman-hpc build -t samwelborn/streaming-paper-ptycho-plots:latest -f Dockerfile.plots .
podman-hpc migrate samwelborn/streaming-paper-ptycho-plots:latest