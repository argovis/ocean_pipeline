import numpy, argparse, glob, pandas
from wodpy import wod
from helpers import helpers

# argument setup
parser = argparse.ArgumentParser()
parser.add_argument("--data_dir", type=str, help="directory with ASCII WOD data")
args = parser.parse_args()

files = glob.glob(args.data_dir + '/*')

julds = [[] for i in range(12)]
lats = [[] for i in range(12)]
lons = [[] for i in range(12)]
filetypes = [[] for i in range(12)]
temps = [[] for i in range(12)]
psals = [[] for i in range(12)]
pressures = [[] for i in range(12)]

for file in files:
    
    fid = open(file)
    p = wod.WodProfile(fid)
    while True:
        # extract and QC filter in situ measurements
        pindex = p.var_index(25)
        temp,psal,pres = helpers.filterQCandPressure(p.t(), p.s(), p.p(), p.t_level_qc(originator=False), p.s_level_qc(originator=False), p.var_level_qc(pindex), [0], 10000000)
        if len(pres) == 0:
            print(p.uid(), 'no data passing QC')
            if p.is_last_profile_in_file(fid):
                break
            else:
                p = wod.WodProfile(fid)
            continue
        
        filetype = file.split('/')[-1][0:3]
        juld = helpers.mljul(p.year(),p.month(),p.day(),p.time())
        month = p.month()
        lat = p.latitude()
        lon = helpers.remap_longitude(p.longitude())

        julds[month-1].append(juld)
        lats[month-1].append(lat)
        lons[month-1].append(lon)
        filetypes[month-1].append(filetype)
        temps[month-1].append(temp)
        psals[month-1].append(psal)
        pressures[month-1].append(pres)

        if p.is_last_profile_in_file(fid):
            break
        else:
            p = wod.WodProfile(fid)

dataframes = [
    pandas.DataFrame({
        'juld': julds[i],
        'longitude': lons[i],
        'latitude': lats[i],
        'temperature': temps[i],
        'salinity': psals[i],
        'pressure': pressures[i],
        'filetype': filetypes[i]
    }) for i in range(12)
]

for i in range(12):
    dataframes[i].to_parquet(f"{args.data_dir}/{i+1}_QC0_profiles.parquet", engine='pyarrow')
