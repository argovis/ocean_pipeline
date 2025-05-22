FROM python:3.9

RUN apt-get update -y ; apt-get install -y nano
RUN pip install wodpy numpy pandas scipy gsw pytest xarray pyarrow juliandate h5py
