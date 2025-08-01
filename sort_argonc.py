# usage: python sort_argonc.py <origin dir> <target dir>
# origin dir should be a DAC-specific folder from an argo DOI archive (https://www.seanoe.org/data/00311/42182/), for example /whatever_root_dir/202501-ArgoData/dac/aoml
# target dir should be an empty dir where folders of profile .nc will be sorted into directories /<target dir>/YYYY_MM

import glob, os, shutil, sys, warnings
import xarray
from helpers import helpers

print(sys.argv[1])

source_dir = sys.argv[1]
target_base_dir = sys.argv[2]

for filepath in glob.glob(os.path.join(source_dir, '*', 'profiles', '*.nc')):
    xar = helpers.safe_open_dataset(filepath)
    try:
        date = xar['JULD'].to_dict()['data'][0]
        year = date.year
        month = date.month
    except Exception:
        print(f'bad timestamp, cant sort {filepath}')
        continue

    month_dir = os.path.join(target_base_dir, f'{year:04d}_{month:02d}')
    os.makedirs(month_dir, exist_ok=True)

    shutil.copy2(filepath, os.path.join(month_dir, os.path.basename(filepath)))

