# replaces qc_filter.py for pre-qc-filtered monthly files dl'ed from argovis.
# argovis json files should be named and sorted yyyy/yyyy-mm.json under --data-dir
import numpy, argparse, glob, pandas, json, datetime
from helpers import helpers

# argument setup
parser = argparse.ArgumentParser()
parser.add_argument("--data_dir", type=str, help="directory with Argovis JSON")
args = parser.parse_args()

files = glob.glob(args.data_dir + '/*json')

# files loop months
for file in files:

    year=int(file.split('/')[-1][0:4])
    month=int(file.split('/')[-1][5:7])
    data = json.load(open(file, 'r'))

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
    #uids = []
    floats = []
    cycles = []

    # loops profiles

    for i in range(len(data)):

        temp = data[i]['data'][data[i]['data_info'][0].index('temperature')]
        psal = data[i]['data'][data[i]['data_info'][0].index('salinity')]
        pres = data[i]['data'][data[i]['data_info'][0].index('pressure')]
        temp_qc = data[i]['data'][data[i]['data_info'][0].index('temperature_argoqc')]
        psal_qc = data[i]['data'][data[i]['data_info'][0].index('salinity_argoqc')]
        pres_qc = data[i]['data'][data[i]['data_info'][0].index('pressure_argoqc')]

        dt = datetime.datetime.strptime(data[i]['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ")
        filetype = 'argovis'
        juld = helpers.mljul(dt.year,dt.month,dt.day,dt.hour + dt.minute/60 + dt.second/60/60)
        lat = data[i]['geolocation']['coordinates'][1]
        lon = helpers.remap_longitude(data[i]['geolocation']['coordinates'][0])
        #uid = p.uid()
        float = int(data[i]['_id'].split('_')[0])
        cycle = int(data[i]['_id'].split('_')[1])

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
        #uids.append(uid)
        floats.append(float)
        cycles.append(cycle)

        data[i] = None

    df = pandas.DataFrame({
        'float': floats,
        'cycle': cycles,
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


    # qc encoding hard coded for now
    df.to_parquet(f"{args.data_dir}/{month}_p0_t0_s0_1_profiles.parquet", engine='pyarrow')
