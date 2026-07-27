import glob, os, sys, pandas, xarray, argparse, numpy, datetime
from helpers import helpers

parser = argparse.ArgumentParser()
parser.add_argument("--data_dir", type=str, help="directory with Argovis JSON")
parser.add_argument("--year", type=int, help="year to consider")
parser.add_argument("--month", type=int, help="month to consider")
parser.add_argument("--var", type=str, help="variable name to read from me4oh input")
parser.add_argument("--level_index", type=int, help="index of level on [0,2]")
parser.add_argument("--output_file", type=str, help="name of output file, with path.")
args = parser.parse_args()

fn = f'{args.data_dir}/ofam3-jra55.all.EN.4.1.1.f.profiles.g10.{args.year}{args.month:02d}.update.nc'
xar = xarray.open_dataset(fn)

lons = xar['ts_lon'].to_dict()['data']
lats = xar['ts_lat'].to_dict()['data']
ymd = xar['en4_ymd'].to_dict()['data']
dn = [helpers.datetime_to_datenum(datetime.datetime(*[int(x) for x in ymd_i])) for ymd_i in ymd]
vals = xar[args.var].to_dict()['data']
vals = [[x[args.level_index]] for x in vals]

df = pandas.DataFrame({
    'longitude': lons,
    'latitude': lats,
    'juld': dn,
    'float': [-1] * len(vals),
    'cycle': ['xxxx'] * len(vals),
    args.var: vals,
    'flag': [0] * len(vals),
})

df.to_parquet(args.output_file, engine='pyarrow')
