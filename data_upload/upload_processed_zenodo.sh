#!/bin/bash

# Saved zenodo token in private folder in home dir
export ZENODO_TOKEN=$(cat ~/.zenodo/access_token_nersc)

ZENODO_0=10023292

/global/homes/s/swelborn/gits/zenodo-upload/zenodo_upload.sh $ZENODO_0 \
    /pscratch/sd/s/swelborn/streaming-paper/counted_data/processed_data.tar.gz