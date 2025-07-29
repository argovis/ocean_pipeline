# argovis json files should be named *.json under --data-dir, which is assumed to correspond to a single month.
import numpy, argparse, glob, pandas, json, datetime
from helpers import helpers

# argument setup
parser = argparse.ArgumentParser()
parser.add_argument("--data_dir", type=str, help="directory with Argovis JSON")
parser.add_argument("--year", type=int, help="year to consider")
parser.add_argument("--month", type=int, help="month to consider")
parser.add_argument("--psc_filter", type=bool, help="whether or not to apply PSC-style profile filtering")
args = parser.parse_args()

files = glob.glob(args.data_dir + '/*json')

# files loop months
for file in files:
    print(args.data_dir, file)

    year=args.year
    month=args.month
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
        source = data[i]['source']

        if args.psc_filter:
            # PSC-esue filtering
            ## must have only QC 1 or 2 for every single pressure, temperature and salinity level
            if not all(x in (1, 2, None) for x in temp_qc):
                continue
            if not all(x in (1, 2, None) for x in psal_qc):
                continue
            if not all(x in (1, 2, None) for x in pres_qc):
                continue
            ## must have good geolocation and timestamp qc
            if geolocation_qc not in (1,2) or timestamp_qc not in (1,2):
                continue
            ## must have more than one level
            if len(pres) < 2:
                continue
            ## must not have any negative pressures
            ###if any(p < 0 for p in pres):
            ###        continue
            ### cludge to try and only count negative pressure from core levels:
            pres_core = [x for x, m in zip(pres, temp_qc) if not m==None]
            if any(p<0 for p in pres_core):
                continue
            ## non-null temp and psal lengths must match pressure
            temp_scrub = [x for x in temp if not x==None]
            psal_scrub = [x for x in psal if not x==None]
            pres_scrub = [x for x in pres if not x==None]
            if len(pres_scrub) != len(temp_scrub) or len(pres_scrub) != len(psal_scrub):
                if len(source) == 1: # can only do this test for core profiles, argovis' merging makes this impossible to check in this way for bgc profiles.
                    continue
            mangled_pressure = False
            for level_idx in range(len(pres) - 1):
                if pres[level_idx] is not None and pres[level_idx + 1] is not None:
                    ## pressure levels must be ascending
                    if pres[level_idx + 1] <= pres[level_idx]:
                        mangled_pressure = True
                    ## gaps larger than 200 dbar are not allowed
                    if pres[level_idx + 1] - pres[level_idx] > 200:
                        mangled_pressure = True
            if mangled_pressure:
                continue
            ## at least 100 dbar in extent
            if pres[0] is not None and pres[-1] is not None and (pres[-1] - pres[0] < 100):
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
