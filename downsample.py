# rejects are flagged with the <float id>_<cycle> of the profile the reject was dropped in favor of.

import numpy, argparse, pandas, scipy, os
from helpers import helpers

parser = argparse.ArgumentParser()
parser.add_argument("--input_file", type=str, help="parquet file with longitude, latitude, and juld")
parser.add_argument("--output_file", type=str, help="name of output file, with path.")
args = parser.parse_args()

df = pandas.read_parquet(args.input_file, engine='pyarrow')

if len(df):
    binsize = 0.1 # 0.5
    df['lon_bin'] = numpy.floor(df['longitude'] / binsize)
    df['lat_bin'] = numpy.floor(df['latitude'] / binsize)
    df['week_bin'] = numpy.floor(df['juld'] / 7)
    df['day_bin'] = numpy.floor(df['juld'])

    group_cols = ['lon_bin', 'lat_bin', 'day_bin']
    winner_idx = (df.groupby(group_cols, sort=False).apply(lambda g: helpers.choose_profile(g).name)).to_numpy()

    # use the group winner's float_cycle as the flag value for rejected profiles
    winners = df.loc[winner_idx, group_cols + ['float', 'cycle']].copy()
    winners['flag'] = winners['float'].astype(str) + "_" + winners['cycle'].astype(str)
    winners = winners[group_cols + ['flag']]
    reject_cols = ['float', 'cycle', 'longitude', 'latitude', 'juld'] + group_cols
    rejects = df.loc[~df.index.isin(winner_idx), reject_cols].merge(winners, on=group_cols, how='left')
    rejects = rejects.drop(columns=group_cols).reset_index(drop=True)
    df = df.loc[winner_idx].reset_index(drop=True)

    #rejects = df.loc[~df.index.isin(winner_idx)].reset_index(drop=True)
    #rejects['flag'] = 1
    #df = df.loc[winner_idx].reset_index(drop=True)
else:
    # empty result to not break the pipeline
    rejects = pandas.DataFrame(columns=['float', 'cycle', 'longitude', 'latitude', 'juld', 'flag'])

rejects.columns.name = None
rejects.to_parquet(os.path.join(args.output_file.split('.')[0] + '_rejects.parquet'), engine='pyarrow')
df.columns.name = None
df.to_parquet(args.output_file, engine='pyarrow')
