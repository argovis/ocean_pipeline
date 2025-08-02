import scipy.io, requests, xarray, numpy, time
from ftplib import FTP
from urllib.parse import urlparse
import os

year=2008
month='12'
psc_input_files = 'matlab_selection_example/intTemp_{month}_{year}_15_300.mat'
argovis_input_files = '/projects/wimi7695/localgp_validate/potential_temperature_{month}_{year}_15_300.mat'

def download_ftp_file(ftp, nc_url):
    parsed = urlparse(nc_url)
    remote_path = parsed.path
    filename = os.path.basename(remote_path)

    with open(filename, 'wb') as f:
        ftp.retrbinary(f'RETR {remote_path}', f.write)

    return filename

def find_nc_file(nc_url):
    return '/scratch/alpine/wimi7695/argo_doi_2025/202501-ArgoData/' + nc_url[34:] # slice off 'ftp://ftp.ifremer.fr/ifremer/argo/'

fn = psc_input_files.format(year=year, month=month)
psc_mat = scipy.io.loadmat(fn)
psc_longs = psc_mat['profLongAggrMonth'].tolist()[0]
psc_lats = psc_mat['profLatAggrMonth'].tolist()[0]
psc_juld = psc_mat['profJulDayAggrMonth'].tolist()[0]
psc_float = psc_mat['profFloatIDAggrMonth'].tolist()[0]
psc_cycle = psc_mat['profObsIDAggrMonth'].tolist()[0]
psc_cycle = [str(x).zfill(3) for x in psc_cycle]
#tempint = psc_mat['profVariableAggrMonth'].tolist()[0]

fn = argovis_input_files.format(year=year, month=month)
argovis_mat = scipy.io.loadmat(fn)
argovis_longs = argovis_mat['profLongAggrMonth'].tolist()[0]
argovis_lats = argovis_mat['profLatAggrMonth'].tolist()[0]
argovis_juld = argovis_mat['profJulDayAggrMonth'].tolist()[0]
argovis_float = argovis_mat['profFloatIDAggrMonth'].tolist()[0]
argovis_cycle = argovis_mat['profObsIDAggrMonth'].tolist()
#tempint = argovis_mat['profVariableAggrMonth'].tolist()[0]

# identify profiles unique to each set
# can't rely on profile ID alone since PSC didn't preserve 'D'ecending tag.
# don't bank on timestamp either, sometimes they get updated without a QC reflection
argo_fingerprint = [[argovis_float[i], argovis_cycle[i], argovis_longs[i], argovis_lats[i]] for i,_ in enumerate(argovis_float)]
psc_fingerprint = [[psc_float[i], psc_cycle[i], psc_longs[i], psc_lats[i]] for i,_ in enumerate(psc_float)]
remove_argo = []
remove_psc = []
thresh = 0.0001
for i in range(len(argo_fingerprint)):
    for j in range(len(psc_fingerprint)):
        a = argo_fingerprint[i]
        p = psc_fingerprint[j]
        if int(a[0]) == int(p[0]) and a[1][0:3] == p[1] and (abs(a[2]-p[2])%360)<thresh and abs(a[3]-p[3])<thresh:
            remove_argo.append(i)
            remove_psc.append(j)
unique_argovis = [a for i,a in enumerate(argo_fingerprint) if i not in remove_argo]
unique_psc = [p for i,p in enumerate(psc_fingerprint) if i not in remove_psc]

# construct argovis-style IDs for each and form lists of profiles unique to each selection based on this
#psc_ids = [str(psc_float[i]) + '_' + str(psc_cycle[i]) for i,_ in enumerate(psc_float)]
#argovis_ids = [(str(argovis_float[i]) + '_' + str(argovis_cycle[i])).strip() for i,_ in enumerate(argovis_float)]
#unique_psc = [p for p in psc_ids if p not in argovis_ids]
#unique_argovis = [p for p in argovis_ids if p not in psc_ids]

# psc didn't preserve the 'D' tag; match on lat/lon/timestamp
#remove_argovis_id = []
#remove_psc_id = []
#for i, id in enumerate(argovis_ids):
#    if not id[-1] == 'D':
#        continue
#    if not id[0:-1] in psc_ids:
#        continue
#    argo_idx = argovis_ids.index(id)
#    psc_idxs = [i for i, val in enumerate(psc_ids) if val == id[0:-1]]

#    for psc_idx in psc_idxs:
#        thresh = 0.0001
#        if abs(psc_lats[psc_idx] - argovis_lats[argo_idx]) < thresh and abs((psc_longs[psc_idx] - argovis_longs[argo_idx])%360) < thresh and abs(psc_juld[psc_idx] - argovis_juld[argo_idx]) < thresh:
#            remove_argovis_id.append(id)
#            remove_psc_id.append(id[0:-1])
#unique_psc = [x for x in unique_psc if x not in remove_psc_id]
#unique_argovis = [x for x in unique_argovis if x not in remove_argovis_id]

# check argovis unique profiles
#ftp = FTP(timeout=60)
#ftp.set_debuglevel(2)
#ftp.connect('ftp.ifremer.fr')
#ftp.login()
print('Number of profiles chosen by Argovis to check: ', len(unique_argovis))
apex = []     # is this an apex float?
nanpres = []  # was there a nan anywhere in the pressure vector?
negpres = []  # is there a negative pressure anywhere in the profile?
badoldqc = [] # do pres, temp, psal, positionqc or juldqc from the DOI netcdf file exhibit a QC>2?
missingvalues = [] # are any two of pres, temp, psal different lengths after removing nulls?
fnf = [] # netcdf file not found in the DOI archive
ooo = [] # levels were found out of order in the netcdf
rtupdate = [] # argovis saw a delayed mode file, psc saw a realtime file in the doi archive
unqualified_profiles = [] # none of the above
for a in unique_argovis:
    id = str(a[0]) + '_' + a[1].strip()
    time.sleep(2)
    profile = requests.get('https://argovis-api.colorado.edu/argo', params = {'id': id}).json()
    if len(profile) == 1:
        nc = profile[0]['source']
        nc = [x for x in nc if 'argo_core' in x['source']][0]['url']
        #fn = download_ftp_file(ftp, nc)
        fn = find_nc_file(nc)

        try:
            xar = xarray.open_dataset(fn)
        except Exception as e:
            # maybe the archive has a realtime version?
            try:
                xar=xarray.open_dataset(fn.replace('profiles/D', 'profiles/R'))
                # is there actually a match for this in the psc data with a slightly differnt lon/lat?
                lon = xar['LONGITUDE'].to_dict()['data'][0]
                lat = xar['LATITUDE'].to_dict()['data'][0]
                float = xar['PLATFORM_NUMBER'].to_dict()['data'][0]
                cycle = xar['CYCLE_NUMBER'].to_dict()['data'][0]
                rtmatch = None
                for i, p in enumerate(unique_psc):
                    if int(p[0]) == int(float) and int(p[1][0:3]) == int(cycle) and (abs(p[2]-lon)%360)<thresh and abs(p[3]-lat)<thresh:
                        rtmatch = i
                if not rtmatch == None:
                    rtupdate.append(id)
                    del unique_psc[rtmatch]
                    continue
            except:
                fnf.append(fn.split('/')[-1])
                continue
        pressure_var = 'PRES'
        temp_var = 'TEMP'
        psal_var = 'PSAL'
        DATA_MODE = xar['DATA_MODE'].to_dict()['data'][0].decode('UTF-8')
        if DATA_MODE in ['A', 'D']:
            pressure_var = 'PRES_ADJUSTED'
            temp_var = 'TEMP_ADJUSTED'
            psal_var = 'PSAL_ADJUSTED'

        pres_scrub = [x for x in xar[pressure_var].to_dict()['data'][0] if not x==None]
        temp_scrub = [x for x in xar[temp_var].to_dict()['data'][0] if not x==None]
        psal_scrub = [x for x in xar[psal_var].to_dict()['data'][0] if not x==None]
        pres = xar[pressure_var].to_dict()['data'][0]
        pres_qc = xar[pressure_var+'_QC'].to_dict()['data'][0]
        temp_qc = xar[temp_var+'_QC'].to_dict()['data'][0]
        psal_qc = xar[psal_var+'_QC'].to_dict()['data'][0]

        if 20 in xar['PRES_ADJUSTED_ERROR'].to_dict()['data'][0]:
            apex.append(id)
        elif any(numpy.isnan(x) for x in pres):
            nanpres.append(id)
        elif any(p<0 for p in pres):
            negpres.append(id)
        elif any(int(qc.decode())>2 for qc in pres_qc) or any(int(qc.decode())>2 for qc in temp_qc) or any(int(qc.decode())>2 for qc in psal_qc) or int(xar['JULD_QC'].to_dict()['data'][0].decode())>2 or int(xar['POSITION_QC'].to_dict()['data'][0].decode())>2:
            badoldqc.append(id)
        elif len(pres_scrub) != len(temp_scrub) or len(pres_scrub) != len(psal_scrub):
            missingvalues.append(id)
        elif not all(x < y for x, y in zip(pres, pres[1:])):
            ooo.append(id)
        else:
            unqualified_profiles.append(id)
    else:
        print('problems', id, profile)
print('Number of problematic APEX profiles: ', len(apex))
print('Number of profiles with suppresses pressure levels: ', len(nanpres))
print('Number of profiles with p<0: ', len(negpres))
print('Number of profiles with bad QC at the DOI nc: ', len(badoldqc))
print('Number of profiles with missing values at the DOI nc: ', len(missingvalues))
print('Number of profiles matching a realtime file from the DOI at a slightly different location: ', len(rtupdate))
print('Number of profiles without corresponding file in DOI archive: ', len(fnf))
print('Number of profiles without strictly ascending pressures: ', len(ooo))
print('Unqualified profile IDs: ', unqualified_profiles)

print('---------------------------------------------------------')

print('Number of profiles chosen by PSC to check:', len(unique_psc))
badqc = []
#updated = []
unqualified = []
for psc in unique_psc:
    time.sleep(2)
    startDate = str(year) + '-' + month + '-01T00:00:00Z'
    nextmonth = {'01':'02', '02':'03', '03':'04', '04':'05', '05':'06', '06':'07', '07':'08', '08':'09', '09':'10', '10':'11', '11':'12', '12':'01'}[month]
    nextyear = year
    if nextmonth=='01':
        nextyear = year+1
    endDate = str(nextyear) + '-' + nextmonth + '-01T00:00:00Z'
    profile = requests.get('https://argovis-api.colorado.edu/argo', params = {'center': str(psc[2])+','+str(psc[3]), 'radius':1, 'data': 'all', 'startDate': startDate, 'endDate': endDate}).json()
    if len(profile) == 1:
        nc = profile[0]['source']
        nc = [x for x in nc if 'argo_core' in x['source']][0]['url'].split('/')[-1]
        p = profile[0]
        if p['geolocation_argoqc'] > 2 or p['timestamp_argoqc'] > 2 or any(x>2 for x in p['data'][p['data_info'][0].index('pressure_argoqc')]) or any(x>2 for x in p['data'][p['data_info'][0].index('temperature_argoqc')]) or any(x>2 for x in p['data'][p['data_info'][0].index('salinity_argoqc')]):
            badqc.append(psc)
        #elif nc in fnf:
        #    updated.append(psc)
        else:
            unqualified.append(psc)
    else:
        print('problems', psc, profile)
print('Number of profiles with bad QC:', len(badqc))
#print('Number of profiles matching a file not found in the DOI archive:', len(updated))
print('Unqualified profiles:', unqualified)


print(fnf)
#print(updated)
