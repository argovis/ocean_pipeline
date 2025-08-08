import glob, os, sys, pandas, xarray, argparse, numpy, datetime
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

rejects = pandas.DataFrame(columns=['float', 'cycle', 'longitude', 'latitude', 'position_qc', 'juld_qc', 'startup', 'APEX', 'pressure_sort', 'no_realtime', 'require_delayed'])

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

    # drop lousy profiles
    position_qc = False
    juld_qc = False
    startup = False
    apex = False
    pressure_sort = False
    no_realtime = False
    require_delayed = False
    ## QC 1 position
    if POSITION_QC != 1:
        position_qc = True
    ## QC 1 time
    if JULD_QC != 1:
        juld_qc = True
    ## no startup cycles
    if CYCLE_NUMBER == 0:
        startup = True
    ## bad APEX floats
    if 20 in PRES_ADJUSTED_ERROR:
        apex = True
    ## pressure out of order, more than 2.4dbar
    if any(x[0] - x[1] > 2.4 for x in zip(pres, pres[1:])):
        pressure_sort = True
    ## no realtime variables ever
    #if DATA_MODE == 'R':
    #    no_realtime = True
    ## delayed mode only 5+ years in the past
    if JULD < datetime.datetime(2020,1,1) and DATA_MODE != 'D':
        require_delayed = True
    ## if any of these are true, reject the profile
    if position_qc or juld_qc or startup or apex or pressure_sort or no_realtime or require_delayed:
        rejects.loc[len(rejects)] = {
            'float': PLATFORM_NUMBER,
            'cycle': cycle,
            'longitude': LONGITUDE,
            'latitude': LATITUDE,
            'position_qc': position_qc,
            'juld_qc': juld_qc,
            'startup': startup,
            'APEX': apex,
            'pressure_sort': pressure_sort,
            'no_realtime': no_realtime,
            'require_delayed': require_delayed
        }
        continue

    # filter off bad levels
    levels = list(zip(pres, pres_qc, temp, temp_qc, psal, psal_qc))
    dump_levels = []
    for i, level in enumerate(levels):
        lvl_pres, lvl_pres_qc, lvl_temp, lvl_temp_qc, lvl_psal, lvl_psal_qc = level
        ## must have pressure and temperature
        if lvl_pres in [None, numpy.nan] or lvl_temp in [None, numpy.nan]:
            dump_levels.append(i)
        ## must have acceptable QC for all measurements
        if lvl_pres_qc not in args.pressure_qc or lvl_temp_qc not in args.temperature_qc or lvl_psal_qc not in args.salinity_qc:
            dump_levels.append(i)
        ## no negative pressures
        if lvl_pres<0:
            dump_levels.append(i)
    levels = [lvl for i, lvl in enumerate(levels) if i not in dump_levels]
    pres = [lvl[0] for lvl in levels]
    temp = [lvl[2] for lvl in levels]
    psal = [lvl[4] for lvl in levels]
    pres_qc = [lvl[1] for lvl in levels]
    temp_qc = [lvl[3] for lvl in levels]
    psal_qc = [lvl[5] for lvl in levels]

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

rejects.to_parquet(os.path.join(source_dir, os.path.basename(args.output_file).split('.')[0] + '_rejects.parquet'), engine='pyarrow')
df.to_parquet(args.output_file, engine='pyarrow')
