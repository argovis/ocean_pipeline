import numpy, argparse, pandas, scipy
from helpers import helpers

parser = argparse.ArgumentParser()
parser.add_argument("--input_file", type=str, help="parquet file with longitude, latitude, and juld")
args = parser.parse_args()

df = pandas.read_parquet(args.input_file, engine='pyarrow')

print(len(df))
pandas.set_option('display.max_rows', None)

df['lon_bin'] = numpy.floor(df['longitude'])
df['lat_bin'] = numpy.floor(df['latitude'])
df['week_bin'] = numpy.floor(df['juld'] / 7)
print(df.sort_values(by=['lon_bin', 'lat_bin', 'week_bin'], ascending=True))

df_filtered = df.groupby(['lon_bin', 'lat_bin', 'week_bin'], as_index=False).apply(helpers.choose_profile, include_groups=False).reset_index(drop=True)
df_filtered = df_filtered.drop(['lon_bin', 'lat_bin', 'week_bin'], axis=1)

print(len(df_filtered))

df_filtered.to_parquet(f"{args.input_file.split('.')[0]}_downsampled.parquet", engine='pyarrow')