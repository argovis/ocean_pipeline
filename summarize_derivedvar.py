import os, glob, datetime
import numpy as np
import scipy.io
import xarray as xr
from helpers import helpers

# Directory containing the .mat files
mat_dir = "/scratch/alpine/wimi7695/argo_doi_2025/sorted/weddell"

# Variables we want to keep
vars_to_keep = ["longitude", "latitude", "juld", "float", "cycle", "position_qc", "juld_qc"]

# Accumulators for each variable
accum = {var: [] for var in vars_to_keep}

# Loop over all .mat files in the directory
for fpath in glob.glob(os.path.join(mat_dir, "*.mat")):
    data = scipy.io.loadmat(fpath)
    for var in vars_to_keep:
        if var in data:
            # Flatten and convert to 1D list/array
            val = np.ravel(data[var])
            accum[var].append(val)
        else:
            print(f"Warning: {var} not found in {fpath}")

# Concatenate along a single dimension
combined = {var: np.concatenate(accum[var]) for var in vars_to_keep}
n_profiles = len(combined["longitude"])  # assume same length for all

ds = xr.Dataset(
    {
        "longitude": (("profile",), combined["longitude"]),
        "latitude": (("profile",), combined["latitude"]),
        "juld": (("profile",), combined["juld"]),
        "float": (("profile",), combined["float"]),
        "cycle": (("profile",), combined["cycle"]),
        "position_qc": (("profile",), combined["position_qc"]),
        "juld_qc": (("profile",), combined["juld_qc"]),
    },
    coords={"profile": np.arange(n_profiles)}
)

def argodate(dt):
    epoch = datetime.datetime(1950, 1, 1, 0, 0, 0)
    return (dt - epoch).total_seconds() / 86400.0

#ds['juld'] = helpers.datenum_to_datetime(ds['juld'])
ds['juld'] = ('profile', [argodate(helpers.datenum_to_datetime(x)) for x in ds['juld'].values])
ds['juld'].attrs['standard_name'] = "time"
ds['juld'].attrs['units'] = "days since 1950-01-01 00:00:00 UTC"

output_nc = "/scratch/alpine/wimi7695/argo_doi_2025/sorted/weddell/combined_profiles.nc"
ds.to_netcdf(output_nc)

