import numpy, argparse, glob, pandas
from wodpy import wod
from helpers import helpers

def parse_list(s):
    return [int(x) for x in s.split(',')]

# argument setup
parser = argparse.ArgumentParser()
parser.add_argument("--data_dir", type=str, help="directory with ASCII WOD data")
parser.add_argument("--temperature_qc", type=parse_list, nargs='+', help="temperature QC flag to accept")
parser.add_argument("--salinity_qc", type=parse_list, nargs='+', help="salinity QC flag to accept")
parser.add_argument("--pressure_qc", type=parse_list, nargs='+', help="pressure QC flag to accept")
args = parser.parse_args()

files = glob.glob(args.data_dir + '/*')

julds = [[] for i in range(12)]
lats = [[] for i in range(12)]
lons = [[] for i in range(12)]
filetypes = [[] for i in range(12)]
temps = [[] for i in range(12)]
psals = [[] for i in range(12)]
pressures = [[] for i in range(12)]
temps_qc = [[] for i in range(12)]
psals_qc = [[] for i in range(12)]
pressures_qc = [[] for i in range(12)]
flags = [[] for i in range(12)]
uids = [[] for i in range(12)]

for file in files:

    fid = open(file)
    p = wod.WodProfile(fid)
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

        julds[month-1].append(juld)
        lats[month-1].append(lat)
        lons[month-1].append(lon)
        filetypes[month-1].append(filetype)
        temps[month-1].append(temp)
        psals[month-1].append(psal)
        pressures[month-1].append(pres)
        temps_qc[month-1].append(temp_qc)
        psals_qc[month-1].append(psal_qc)
        pressures_qc[month-1].append(pres_qc)
        flags[month-1].append(0)
        uids[month-1].append(uid)

        if p.is_last_profile_in_file(fid):
            break
        else:
            p = wod.WodProfile(fid)

dataframes = [
    pandas.DataFrame({
        'uid': uids[i],
        'juld': julds[i],
        'longitude': lons[i],
        'latitude': lats[i],
        'temperature': temps[i],
        'temperature_qc': temps_qc[i],
        'salinity': psals[i],
        'salinity_qc': psals_qc[i],
        'pressure': pressures[i],
        'pressure_qc': pressures_qc[i],
        'filetype': filetypes[i],
        'flag': flags[i]
    }) for i in range(12)
]

for i in range(12):
    dataframes[i].to_parquet(f"{args.data_dir}/{i+1}_p{'_'.join([str(x) for x in args.pressure_qc])}_t{'_'.join([str(x) for x in args.temperature_qc])}_s{'_'.join([str(x) for x in args.salinity_qc])}_profiles.parquet", engine='pyarrow')
