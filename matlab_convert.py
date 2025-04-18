import numpy, argparse, pandas, scipy
from helpers import helpers

parser = argparse.ArgumentParser()
parser.add_argument("--input_file", type=str, help="parquet file to convert")
parser.add_argument("--output_file", type=str, help="name of output file, with path.")
parser.add_argument("--variable", type=str, help="variable to extract")
args = parser.parse_args()

df = pandas.read_parquet(args.input_file, engine='pyarrow')

#dict_keys(['uid', 'juld', 'longitude', 'latitude', 'temperature', 'temperature_qc', 'salinity', 'salinity_qc', 'pressure', 'pressure_qc', 'filetype', 'flag'])
print(df.to_dict(orient='list')['flag'])
