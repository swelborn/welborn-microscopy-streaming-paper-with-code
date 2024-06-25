# Data upload/download

## Raw data upload to Zenodo

- Used `tar_raw_files.sh` to make `counted_data.tar.gz`
- This tar was split and uploaded to zenodo via: <https://github.com/jhpoelen/zenodo-upload>
  - You can see the script that was used to upload in `upload_counted_zenodo.sh`
- Used `tar_processed_files.sh` to make `processed_data.tar.gz` - this includes processed data (from ptychography)
- Used `upload_processed_zenodo.sh` to upload `processed_data.tar.gz` to zenodo
- The total size of the raw, reduced data before compression is: 125.11 GB

## Downloading data

- Download all 3 parts of raw data from zenodo from the following DOIs:
  - Part 0: 10.5281/zenodo.10023519
  - Part 1: 10.5281/zenodo.10023521
  - Part 2: 10.5281/zenodo.10023523

- You can use zenodo_get python package (google it) to do this, or you can probably just use wget with the links.

## Extracting data

- Wherever you downloaded, run the following (will take some time):

```sh
cat counted_data_part_00.tar.gz counted_data_part_01.tar.gz counted_data_part_02.tar.gz > counted_data.tar.gz
pigz -d -c counted_data.tar.gz | tar xvf -
```

- Once you have downloaded and extracted, check md5sums. First edit the path in the `check_md5.py` to point to the directory where you downloaded.

```sh
python check_md5.py
```

- This will check the md5sums and output a file named comparison_results.txt. In that file you should see that all of the files `MATCH`.
