# pipeline to this point must have generated a dataframe with columns 'latitude', 'longitude', 'juld', and whatever is named in the --variable argument.
# 'float', 'cycle', and 'uncertainty' are optional and will be propagated if provided.

import numpy, argparse, pandas, scipy
from helpers import helpers

def csv_to_list(val):
    if val is None or val.strip() == '':
        return []
    return [s.strip() for s in val.split(',')]

parser = argparse.ArgumentParser()
parser.add_argument("--input_file", type=str, help="parquet file to convert")
parser.add_argument("--output_file", type=str, help="name of output file, with path.")
parser.add_argument("--variable", type=str, help="variable to extract")
parser.add_argument("--auxfields", nargs='?', type=csv_to_list, default=[], const='', help="CSV list of input dataframe column names to pass along into the matlab file.")
args = parser.parse_args()

df = pandas.read_parquet(args.input_file, engine='pyarrow')

# data may or may not have float, cycle, or uncertainty
obsid = [0]*len(df.to_dict(orient='list')['longitude'])
try:
    obsid = df.to_dict(orient='list')['cycle']
except:
    pass
floatid = [0]*len(df.to_dict(orient='list')['longitude'])
try:
    floatid = df.to_dict(orient='list')['float']
except:
    pass
uncertainty = [0]*len(df.to_dict(orient='list')['longitude'])
try:
    uncertainty = df.to_dict(orient='list')['uncertainty']
except:
    pass

dict = {
    'profVariableAggrMonth': [float(x[0]) for x in df.to_dict(orient='list')[args.variable]],
    'profLatAggrMonth': df.to_dict(orient='list')['latitude'],
    'profLongAggrMonth': df.to_dict(orient='list')['longitude'],
    'profFloatIDAggrMonth': floatid,
    'profObsIDAggrMonth': obsid,
    'profJulDayAggrMonth': df.to_dict(orient='list')['juld'],
    'profUncertaintyAggrMonth': uncertainty,
}

for field in args.auxfields:
    try:
        dict[field] = df.to_dict(orient='list')[field]
    except:
        print(f'no such field: {field}')

scipy.io.savemat(args.output_file, dict)
