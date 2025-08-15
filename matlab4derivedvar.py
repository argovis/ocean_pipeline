import numpy, argparse, pandas, scipy, tarfile, os
from helpers import helpers

parser = argparse.ArgumentParser()
parser.add_argument("--input_file", type=str, help="parquet file to convert")
parser.add_argument("--output_file", type=str, help="name of output file, with path.")
args = parser.parse_args()

df = pandas.read_parquet(args.input_file, engine='pyarrow')

# make archive of original profile files surviving to this point
filepaths = df.to_dict(orient='list')['filepath']
with tarfile.open(os.path.splitext(args.output_file)[0] + ".tgz", "w:gz") as tar:
    for path in filepaths:
        tar.add(path, arcname=path.split("/")[-1])

# main matlab output file
dict = {
    'latitude': df.to_dict(orient='list')['latitude'],
    'longitude': df.to_dict(orient='list')['longitude'],
    'juld': df.to_dict(orient='list')['juld'],
    'position_qc': df.to_dict(orient='list')['positionqc'],
    'juld_qc': df.to_dict(orient='list')['juldqc'],
    'float': df.to_dict(orient='list')['float'],
    'cycle': df.to_dict(orient='list')['cycle'],
    'data_mode': df.to_dict(orient='list')['datamode'],
    'longitude': df.to_dict(orient='list')['longitude'],
    'pressure': [float(x[0]) for x in df.to_dict(orient='list')['pressure']],
    'temperature': [float(x[0]) for x in df.to_dict(orient='list')['temperature']],
    'salinity': [float(x[0]) for x in df.to_dict(orient='list')['salinity']],
    'potential_density': [float(x[0]) for x in df.to_dict(orient='list')['potential_density']],
    'potential_temperature': [float(x[0]) for x in df.to_dict(orient='list')['potential_temperature']],
    'absolute_salinity': [float(x[0]) for x in df.to_dict(orient='list')['absolute_salinity']],
    'conservative_temperature': [float(x[0]) for x in df.to_dict(orient='list')['conservative_temperature']],
}

scipy.io.savemat(args.output_file, dict)
