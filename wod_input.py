# note that WOD makes downloading data month by month a bit cumbersome without a scriptable API;
# so this script uses --year and --month flags to pick out profiles that are in the month of interest.
# of course, this will lead to a lot of wasted time unpacking the same profiles over and over if long time periods are in the data_dir inputs.
# happy medium: download yearly data from WOD, give each its own data_dir.
import numpy, argparse, glob, pandas
from wodpy import wod
from helpers import helpers

def parse_list(s):
    return [int(x) for x in s.split(',')]

def strlist(s):
    return [str(x) for x in s.split(',')]

# argument setup
parser = argparse.ArgumentParser()
parser.add_argument("--data_dir", type=str, help="directory with ASCII WOD data")
parser.add_argument("--year", type=int, help="year to consider")
parser.add_argument("--month", type=int, help="month to consider")
parser.add_argument("--filetypes", type=strlist, help="WOD file types as a CSV string, like 'PFL,MRB,CTD'....")
parser.add_argument("--temperature_qc", type=parse_list, help="temperature QC flag to accept")
parser.add_argument("--salinity_qc", type=parse_list, help="salinity QC flag to accept")
parser.add_argument("--pressure_qc", type=parse_list, help="pressure QC flag to accept")
args = parser.parse_args()

files = []
for filetype in args.filetypes:
    files.extend(glob.glob(args.data_dir + '/*'+filetype+'*'))

julds = []
lats = []
lons = []
filetypes = []
temps = []
psals = []
pressures = []
temps_qc = []
psals_qc = []
pressures_qc = []
flags = []
uids = []

for file in files:

    fid = open(file)
    p = wod.WodProfile(fid)
    if p.year() != args.year or p.month() != args.month:
        continue
    while True:
        # extract and QC filter in situ measurements
        pindex = p.var_index(25)
        temp,psal,pres,temp_qc,psal_qc,pres_qc = helpers.filterQCandPressure(p.t(), p.s(), p.p(), p.t_level_qc(originator=False), p.s_level_qc(originator=False), p.var_level_qc(pindex), args.pressure_qc, args.temperature_qc, args.salinity_qc, 10000000)
        if len(pres) == 0:
            print(p.uid(), 'no data passing QC')
            if p.is_last_profile_in_file(fid):
                break
            else:
                p = wod.WodProfile(fid)
            continue

        # assign the worst QC flag of x and pressure to x where x is temperature or salinity
        temp_qc = helpers.merge_qc([temp_qc, pres_qc])
        psal_qc = helpers.merge_qc([psal_qc, pres_qc])

        filetype = file.split('/')[-1][0:3]
        juld = helpers.mljul(p.year(),p.month(),p.day(),p.time())
        month = p.month()
        lat = p.latitude()
        lon = helpers.remap_longitude(p.longitude())
        uid = p.uid()

        julds.append(juld)
        lats.append(lat)
        lons.append(lon)
        filetypes.append(filetype)
        temps.append(temp)
        psals.append(psal)
        pressures.append(pres)
        temps_qc.append(temp_qc)
        psals_qc.append(psal_qc)
        pressures_qc.append(pres_qc)
        flags.append(0)
        uids.append(uid)

        if p.is_last_profile_in_file(fid):
            break
        else:
            p = wod.WodProfile(fid)

dataframe =
    pandas.DataFrame({
        'uid': uids,
        'juld': julds,
        'longitude': lons,
        'latitude': lats,
        'temperature': temps,
        'temperature_qc': temps_qc,
        'salinity': psals,
        'salinity_qc': psals_qc,
        'pressure': pressures,
        'pressure_qc': pressures_qc,
        'filetype': filetypes,
        'flag': flags
    })


dataframe.to_parquet(f"{args.data_dir}/{args.month}_p{'_'.join([str(x) for x in args.pressure_qc])}_t{'_'.join([str(x) for x in args.temperature_qc])}_s{'_'.join([str(x) for x in args.salinity_qc])}_profiles.parquet", engine='pyarrow')
