#!/bin/bash

# Saved zenodo token in private folder in home dir
export ZENODO_TOKEN=$(cat ~/.zenodo/access_token_nersc)

# Split the tar archive into multiple 30GB files
split -b 30G -d --additional-suffix=.tar.gz \
    /pscratch/sd/s/swelborn/streaming-paper/counted_data/counted_data.tar.gz \
    "/pscratch/sd/s/swelborn/streaming-paper/counted_data/counted_data_part_"

ZENODO_0=10023519
ZENODO_1=10023521
ZENODO_2=10023523

/global/homes/s/swelborn/gits/zenodo-upload/zenodo_upload.sh $ZENODO_0 \
    /pscratch/sd/s/swelborn/streaming-paper/counted_data/counted_data_part_00.tar.gz

/global/homes/s/swelborn/gits/zenodo-upload/zenodo_upload.sh $ZENODO_1 \
    /pscratch/sd/s/swelborn/streaming-paper/counted_data/counted_data_part_01.tar.gz

/global/homes/s/swelborn/gits/zenodo-upload/zenodo_upload.sh $ZENODO_2 \
    /pscratch/sd/s/swelborn/streaming-paper/counted_data/counted_data_part_02.tar.gz