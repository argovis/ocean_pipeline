import numpy, argparse, pandas, scipy
from helpers import helpers

parser = argparse.ArgumentParser()
parser.add_argument("--input_file", type=str, help="parquet file to convert")
parser.add_argument("--output_file", type=str, help="name of output file, with path.")
parser.add_argument("--variable", type=str, help="variable to extract")
args = parser.parse_args()

df = pandas.read_parquet(args.input_file, engine='pyarrow')

dict = {
    'profVariableAggrMonth': [float(x[0]) for x in df.to_dict(orient='list')['salinity_interpolation']],
    'profLatAggrMonth': df.to_dict(orient='list')['latitude'],
    'profLongAggrMonth': df.to_dict(orient='list')['longitude'],
    'profFloatIDAggrMonth': [0]*len(df.to_dict(orient='list')['longitude']),
    'profObsIDAggrMonth': df.to_dict(orient='list')['uid'],
    'profJulDayAggrMonth': df.to_dict(orient='list')['juld'],
    'profUncertaintyAggrMonth': [float("nan")]*len(df.to_dict(orient='list')['longitude']),
}

scipy.io.savemat(args.output_file, dict)