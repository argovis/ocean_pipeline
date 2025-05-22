import numpy, h5py, argparse, datetime, pandas
from helpers import helpers

# argument setup
parser = argparse.ArgumentParser()
parser.add_argument("--input_file", type=str, help="original giant matlab blob")
parser.add_argument("--year", type=int, help="year to process")
args = parser.parse_args()

f = h5py.File(args.input_file,'r')
nProf = int(f['nProf'][:][0][0])

julds = [[] for _ in range(12)]
lats = [[] for _ in range(12)]
lons = [[] for _ in range(12)]
filetypes = [[] for _ in range(12)]
temps = [[] for _ in range(12)]
psals = [[] for _ in range(12)]
pressures = [[] for _ in range(12)]
temps_qc = [[] for _ in range(12)]
psals_qc = [[] for _ in range(12)]
pressures_qc = [[] for _ in range(12)]
flags = [[] for _ in range(12)]
floats = [[] for _ in range(12)]
cycles = [[] for _ in range(12)]

# bulk load metadata fields
lat_array = f['profLatAggr'][:]
lon_array = f['profLongAggr'][:]
juld_array = f['profJulDayAggr'][:]
float_array = f['profFloatIDAggr'][:]
cycle_array = f['profCycleNumberAggr'][:]

for i in range(nProf):
    if (i%1000 == 0):
        print(i)

    # cope with one year at a time
    dt = helpers.datenum_to_datetime(f['profJulDayAggr'][i][0])
    year = dt.year
    if year != args.year:
        continue

    month_idx = dt.month - 1

    temp_ref = f['profTempAggr'][i][0]
    temp = f[temp_ref][0]
    psal_ref = f['profPsalAggr'][i][0]
    psal = f[psal_ref][0]
    pres_ref = f['profPresAggr'][i][0]
    pres = f[pres_ref][0]
    temp_qc = [0]*len(temp)
    psal_qc = [0]*len(psal)
    pres_qc = [0]*len(pres)
    filetype = 'argo_psc'
    juld = juld_array[i][0]
    lat = lat_array[i][0]
    lon = helpers.remap_longitude(lon_array[i][0])
    float = int(float_array[i][0])
    cycle = int(cycle_array[i][0])

    julds[month_idx].append(juld)
    lats[month_idx].append(lat)
    lons[month_idx].append(lon)
    filetypes[month_idx].append(filetype)
    temps[month_idx].append(temp)
    psals[month_idx].append(psal)
    pressures[month_idx].append(pres)
    temps_qc[month_idx].append(temp_qc)
    psals_qc[month_idx].append(psal_qc)
    pressures_qc[month_idx].append(pres_qc)
    flags[month_idx].append(0)
    floats[month_idx].append(float)
    cycles[month_idx].append(cycle)

for i in range(12):
    df = pandas.DataFrame({
        'float': floats[i],
        'cycle': cycles[i],
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
    })

    df.to_parquet(f"data/{args.year}/{str(i+1)}_p0_t0_s0_1_profiles.parquet", engine='pyarrow')

