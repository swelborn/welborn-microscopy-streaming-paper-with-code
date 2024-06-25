# Use the nvidia/cuda base image
FROM nvidia/cuda:11.7.1-devel-ubuntu22.04

# Set environment variables to non-interactive (this prevents some prompts)
ENV DEBIAN_FRONTEND noninteractive

# Update package list, install wget, and clean up
RUN apt-get update -y && \
    apt-get install -y wget \
    libarchive13 \
    build-essential \
    gfortran \
    libcurl4 \
    wget \
    ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Define the installer variable for Miniconda
ENV installer=Miniconda3-py310_23.5.2-0-Linux-x86_64.sh

# Download and install Miniconda
RUN wget https://repo.anaconda.com/miniconda/$installer && \
    /bin/bash $installer -b -p /opt/miniconda3          && \
    rm -rf $installer

# Update PATH environment variable
ENV PATH=/opt/miniconda3/bin:$PATH

# Install mpi
ARG mpich=4.0.2
ARG mpich_prefix=mpich-$mpich

RUN \
    wget https://www.mpich.org/static/downloads/$mpich/$mpich_prefix.tar.gz && \
    tar xvzf $mpich_prefix.tar.gz                                           && \
    cd $mpich_prefix                                                        && \
    FFLAGS=-fallow-argument-mismatch FCFLAGS=-fallow-argument-mismatch ./configure            && \
    make -j 30                                                              && \
    make install                                                            && \
    make clean                                                              && \
    cd ..                                                                   && \
    rm -rf $mpich_prefix

# Copy the environment.yml file into the image
COPY ./environment.yml /environment.yml

RUN conda install -n base conda-libmamba-solver && conda config --set solver libmamba && \
    conda env update -n base -f /environment.yml && rm -f /environment.yml

WORKDIR /analysis

COPY ptycho/ /anlysis/ptycho/
COPY scripts/ /analysis/scripts/
COPY config/ /analysis/config/

RUN find ./scripts -type f -name "*.sh" -exec chmod +x {} \; 

RUN mkdir -p /analysis/outputs/plots && mkdir -p /analysis/outputs/movies