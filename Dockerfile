FROM ubuntu:20.04

RUN apt-get update && apt-get install -y wget ca-certificates \
    git curl vim python3-dev python3-pip \
    libfreetype6-dev libhdf5-dev

RUN pip3 install tensorflow numpy pandas sklearn matplotlib  pyyaml h5py
RUN pip3 install keras --no-deps