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
    print(args.data_dir, file)

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

        # variable extraction
        temp = data[i]['data'][data[i]['data_info'][0].index('temperature')]
        psal = data[i]['data'][data[i]['data_info'][0].index('salinity')]
        pres = data[i]['data'][data[i]['data_info'][0].index('pressure')]
        temp_qc = data[i]['data'][data[i]['data_info'][0].index('temperature_argoqc')]
        psal_qc = data[i]['data'][data[i]['data_info'][0].index('salinity_argoqc')]
        pres_qc = data[i]['data'][data[i]['data_info'][0].index('pressure_argoqc')]
        # temp_qc = [99]*len(temp)
        # psal_qc = [99]*len(psal)
        # pres_qc = [99]*len(pres)
        dt = datetime.datetime.strptime(data[i]['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ")
        filetype = 'argovis'
        juld = helpers.datetime_to_datenum(dt)
        lat = data[i]['geolocation']['coordinates'][1]
        lon = helpers.remap_longitude(data[i]['geolocation']['coordinates'][0])
        #uid = p.uid()
        float = int(data[i]['_id'].split('_')[0])
        cycle = data[i]['_id'].split('_')[1]
        geolocation_qc = data[i]['geolocation_argoqc']
        timestamp_qc = data[i]['timestamp_argoqc']

        # PSC-esue filtering
        ## must have good geolocation and timestamp qc
        if geolocation_qc != 1 or timestamp_qc != 1:
            continue
        ## must have more than one level
        if len(pres) < 2:
            continue
        ## temp and psal lengths must match pressure
        if len(pres) != len(temp) or len(pres) != len(psal):
            continue
        for level_idx in range(len(pres) - 1):
            ## pressure levels must be ascending
            if pres[level_idx + 1] <= pres[level_idx]:
                continue
            ## gaps larger than 200 dbar are not allowed
            if pres[level_idx + 1] - pres[level_idx] > 200:
                continue
        ## at least 100 dbar in extent
        if pres[-1] - pres[0] < 100:
            continue
        ## no startup cycles
        if cycle[0:3] == '000':
            continue

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
