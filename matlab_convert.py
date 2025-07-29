import numpy, argparse, pandas, scipy
from helpers import helpers

parser = argparse.ArgumentParser()
parser.add_argument("--input_file", type=str, help="parquet file to convert")
parser.add_argument("--output_file", type=str, help="name of output file, with path.")
parser.add_argument("--variable", type=str, help="variable to extract")
args = parser.parse_args()

df = pandas.read_parquet(args.input_file, engine='pyarrow')

# wod and argo label profiles differently
obsid = [0]*len(df.to_dict(orient='list')['longitude'])
try:
    obsid = df.to_dict(orient='list')['uid'] # wod
except:
    pass
try:
    obsid = df.to_dict(orient='list')['cycle'] # argovis
except:
    pass
floatid = [0]*len(df.to_dict(orient='list')['longitude'])
try:
    floatid = df.to_dict(orient='list')['float'] # argovis
except:
    pass

dict = {
    'profVariableAggrMonth': [float(x[0]) for x in df.to_dict(orient='list')[args.variable]],
    'profLatAggrMonth': df.to_dict(orient='list')['latitude'],
    'profLongAggrMonth': df.to_dict(orient='list')['longitude'],
    'profFloatIDAggrMonth': floatid,
    'profObsIDAggrMonth': obsid,
    'profJulDayAggrMonth': df.to_dict(orient='list')['juld'],
    'profUncertaintyAggrMonth': [float("nan")]*len(df.to_dict(orient='list')['longitude']),
}

if 'direction' in df.columns:
    # argonc preserves directions separately, carry it along
    dict['argo_profile_direction'] = df.to_dict(orient='list')['direction']

scipy.io.savemat(args.output_file, dict)
