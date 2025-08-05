import glob, os, sys, pandas, xarray, argparse
from helpers import helpers

# argument setup
def parse_list(s):
    return [int(x) for x in s.split(',')]

parser = argparse.ArgumentParser()
parser.add_argument("--year", type=int, help="Year to consider")
parser.add_argument("--month", type=int, help="Month to consider")
parser.add_argument("--temperature_qc", type=parse_list, help="temperature QC flags to accept")
parser.add_argument("--salinity_qc", type=parse_list, help="salinity QC flags to accept")
parser.add_argument("--pressure_qc", type=parse_list, help="pressure QC flags to accept")
parser.add_argument("--data_dir", type=str, help="directory with Argovis JSON")
parser.add_argument("--output_file", type=str, help="name of output file, with path.")
args = parser.parse_args()

year = args.year
month = f'{args.month:02d}'

source_dir = args.data_dir

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
floats = []
cycles = []
flags = []

for fn in glob.glob(os.path.join(source_dir, '*.nc')):
    print(fn)

    #xar = xarray.open_dataset(fn)
    xar = helpers.safe_open_dataset(fn)

    # extract variables
    N_PARAM = xar.sizes['N_PARAM']
    if N_PARAM < 3:
        print('nparam')
        continue
    JULD = xar['JULD'].to_dict()['data'][0]
    JULD_QC = xar['JULD_QC'].to_dict()['data'][0]
    JULD_QC = int(JULD_QC) if type(JULD_QC) is bytes else None
    LONGITUDE = xar['LONGITUDE'].to_dict()['data'][0]
    LATITUDE = xar['LATITUDE'].to_dict()['data'][0]
    POSITION_QC = xar['POSITION_QC'].to_dict()['data'][0]
    POSITION_QC = int(POSITION_QC) if type(POSITION_QC) is bytes else None
    PLATFORM_NUMBER = int(xar['PLATFORM_NUMBER'].to_dict()['data'][0])
    CYCLE_NUMBER = int(xar['CYCLE_NUMBER'].to_dict()['data'][0])
    DIRECTION = xar['DIRECTION'].to_dict()['data'][0].decode('UTF-8')
    cycle = str(CYCLE_NUMBER).zfill(3)
    if DIRECTION == 'D':
        cycle += 'D'
    DATA_MODE = xar['DATA_MODE'].to_dict()['data'][0].decode('UTF-8')
    filetype = 'argo_nc_https://www.seanoe.org/data/00311/42182#116315/'
    presvar = 'PRES'
    tempvar = 'TEMP'
    psalvar = 'PSAL'
    if DATA_MODE in ['A', 'D']:
        presvar = 'PRES_ADJUSTED'
        tempvar = 'TEMP_ADJUSTED'
        psalvar = 'PSAL_ADJUSTED'
    pres = xar[presvar].to_dict()['data'][0]
    temp = xar[tempvar].to_dict()['data'][0]
    psal = xar[psalvar].to_dict()['data'][0]
    pres_qc = [int(qc) if type(qc) is bytes else None for qc in xar[presvar+'_QC'].to_dict()['data'][0]]
    temp_qc = [int(qc) if type(qc) is bytes else None for qc in xar[tempvar+'_QC'].to_dict()['data'][0]]
    psal_qc = [int(qc) if type(qc) is bytes else None for qc in xar[psalvar+'_QC'].to_dict()['data'][0]]
    PRES_ADJUSTED_ERROR = xar['PRES_ADJUSTED_ERROR'].to_dict()['data'][0]

    # drop lousy profiles (PSC style)
    ## data qc filter
    if not all(x in args.temperature_qc or x is None for x in temp_qc):
        print('tempqc')
        continue
    if not all(x in args.salinity_qc or x is None for x in psal_qc):
        print('psalqc')
        continue
    if not all(x in args.pressure_qc or x is None for x in pres_qc):
        print('presqc')
        continue
    ## must have good geolocation and timestamp qc
    if POSITION_QC not in (1,2) or JULD_QC not in (1,2):
        print('position/time qc')
        continue
    ## must have more than one level
    if len(pres) < 2:
        print('len')
        continue
    ## must not have any negative pressures
    if any(p < 0 for p in pres):
        print('negpres')
        continue
    ## must have non-silly location
    if LATITUDE > 90 or LATITUDE < -90 or LONGITUDE > 180 or LONGITUDE < -180:
        print('lat lon range')
        continue
    ## non-null temp and psal lengths must match pressure
    temp_scrub = [x for x in temp if not x==None]
    psal_scrub = [x for x in psal if not x==None]
    pres_scrub = [x for x in pres if not x==None]
    if len(pres_scrub) != len(temp_scrub) or len(pres_scrub) != len(psal_scrub):
        print('length mismatch')
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
        print('mangled pressure')
        continue
    ## at least 100 dbar in extent
    if pres[0] is not None and pres[-1] is not None and (pres[-1] - pres[0] < 100):
        print('100 dbar')
        continue
    ## no startup cycles
    if CYCLE_NUMBER == 0:
        print('startup')
        continue
    ## no funky APEX floats
    if 20 in PRES_ADJUSTED_ERROR:
        print('apex')
        continue

    # append to dataframe
    julds.append(helpers.datetime_to_datenum(JULD))
    lats.append(LATITUDE)
    lons.append(LONGITUDE)
    filetypes.append(filetype)
    temps.append(temp)
    psals.append(psal)
    pressures.append(pres)
    temps_qc.append(temp_qc)
    psals_qc.append(psal_qc)
    pressures_qc.append(pres_qc)
    floats.append(PLATFORM_NUMBER)
    cycles.append(cycle)
    flags.append(0)

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

df.to_parquet(args.output_file, engine='pyarrow')
