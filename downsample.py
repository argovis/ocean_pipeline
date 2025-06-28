import numpy, argparse, pandas, scipy
from helpers import helpers

parser = argparse.ArgumentParser()
parser.add_argument("--input_file", type=str, help="parquet file with longitude, latitude, and juld")
parser.add_argument("--output_file", type=str, help="name of output file, with path.")
args = parser.parse_args()

df = pandas.read_parquet(args.input_file, engine='pyarrow')

pandas.set_option('display.max_rows', None)

binsize = 0.1 # 0.5
df['lon_bin'] = numpy.floor(df['longitude'] / binsize)
df['lat_bin'] = numpy.floor(df['latitude'] / binsize)
df['week_bin'] = numpy.floor(df['juld'] / 7)
df['day_bin'] = numpy.floor(df['juld'])

#df_filtered = df.groupby(['lon_bin', 'lat_bin', 'week_bin'], as_index=False).apply(helpers.choose_profile, include_groups=False).reset_index(drop=True)
#df_filtered = df_filtered.drop(['lon_bin', 'lat_bin', 'week_bin'], axis=1)
df_filtered = df.groupby(['lon_bin', 'lat_bin', 'day_bin'], as_index=False).apply(helpers.choose_profile, include_groups=False).reset_index(drop=True)
df_filtered = df_filtered.drop(['lon_bin', 'lat_bin', 'day_bin'], axis=1)

df_filtered.columns.name = None # unnecessary metadata breaks serialization

df_filtered.to_parquet(args.output_file, engine='pyarrow')
