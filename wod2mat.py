# usage: python <WOD ascii file directory> <year> <month> <pressure level of interest OR pressure range shallow,deep for integral> <'conservative' or 'potential' temperature switch>

import numpy, pandas, glob, datetime, scipy.io, sys, bisect, gsw
from wodpy import wod
import scipy.interpolate
import scipy.integrate

pandas.set_option('display.max_colwidth', None)
pandas.set_option('display.max_rows', None)

def mljul(year, month, day, time):
	# compute something appropriate to interpret as matlab's julian day

	# days between Jan 1 0 and Jan 1 1900
	julday = 693962

	delta = datetime.date(year,month,day) - datetime.date(1900,1,1)

	try:
		return julday + delta.days + time/24.0
	except:
		return julday + delta.days

def remap_longitude(longitude):
	# map longitudes onto [20,380)

	if longitude < 20:
		return longitude+360
	else:
		return longitude

def has_common_non_nan_value(list1, list2):
    for i in range(len(list1)):
        if not (list1[i] is None or list2[i] is None) and not (math.isnan(list1[i]) or math.isnan(list2[i])):
            return True
    return False

def find_bracket(lst, low_roi, high_roi):
    # lst: ordered list of floats
    # low_roi: lower bound of region of interest
    # high_roi: upper bound "
    # returns the indexes of the last element below and first element above the ROI

    low = 0
    high = len(lst) - 1
    low_index = -1

    while low <= high:
        mid = (low + high) // 2

        if lst[mid] < low_roi:
            low_index = mid
            low = mid + 1
        else:
            high = mid - 1

    low = 0
    high = len(lst) - 1
    high_index = -1

    while low <= high:
        mid = (low + high) // 2

        if lst[mid] > high_roi:
            high_index = mid
            high = mid - 1
        else:
            low = mid + 1

    return low_index, high_index

def pad_bracket(lst, low_roi, high_roi, buffer, places):
    # returns the indexes of the last element below and first element above an ROI padded with <buffer>, and containing at least <places> elements in the padding.

    tight_bracket = find_bracket(lst, low_roi, high_roi)
    buffer_bracket = find_bracket(lst, low_roi - buffer, high_roi + buffer)

    low = buffer_bracket[0]
    if tight_bracket[0] - buffer_bracket[0] < places:
        low = max(0, tight_bracket[0] - places)

    high = buffer_bracket[1]
    if buffer_bracket[1] - tight_bracket[1] < places:
        high = min(len(lst)-1, tight_bracket[1] + places)

    return low, high

def interpolate_and_integrate(pressures, temperatures, low_roi, high_roi):
	# perform a trapezoidal integration with pressures=x and temperatures=y, from pressure==low_roi to high_roi

	levels = numpy.arange(pressures[0], pressures[-1], 0.2) # fine level spectrum
	t_interp = scipy.interpolate.pchip_interpolate(pressures, temperatures, levels)

	integration_region = find_bracket(levels, low_roi, high_roi)
	p_integration = levels[integration_region[0]+1 : integration_region[1]]
	t_integration = t_interp[integration_region[0]+1 : integration_region[1]]

	return scipy.integrate.trapezoid(t_integration, x=p_integration)


# def filterQC(t,s,p, t_qc,s_qc,p_qc, acceptable):
# 	# given <t>emperature, <s>alinity and <p>ressure lists for a profile,
# 	# the corresponding <>_qc flags,
# 	# and an <acceptable> list of qc flags,
# 	# return t,s and p lists with levels dropped if t or p aren't acceptable qc,
# 	# if t and p are good but s isn't, mask s with NaN.

# 	data = list(zip(t,s,p,t_qc,s_qc,p_qc))
# 	goodTP = list(filter(lambda level: level[3] in acceptable and level[5] in acceptable, data))
# 	t_filter = [x[0] for x in goodTP]
# 	p_filter = [x[2] for x in goodTP]
# 	s_filter = [x[1] if x[4] in acceptable else numpy.NAN for x in goodTP]

# 	return t_filter, s_filter, p_filter

def filterQCandPressure(t,s,p, t_qc,s_qc,p_qc, acceptable, pressure):

	data = list(zip(t,s,p,t_qc,s_qc,p_qc))
	goodTPS = list(filter(lambda level: level[3] in acceptable and level[4] in acceptable and level[5] in acceptable and level[2]<pressure, data))
	t_filter = [x[0] for x in goodTPS]
	p_filter = [x[2] for x in goodTPS]
	s_filter = [x[1] for x in goodTPS]

	return t_filter, s_filter, p_filter	

#files = glob.glob("/scratch/alpine/wimi7695/wod/all/ocldb*")

# parse some command line arguments
files = glob.glob(sys.argv[1] + '/ocldb*')
#file = sys.argv[1]
y = int(sys.argv[2])
m = int(sys.argv[3])
p_arg = [float(n) for n in sys.argv[4].split(',')]
p_interp = False
p_range = False
if len(p_arg) == 1:
	# single level interpolation
	p_interp = p_arg[0]
else:
	# level integral
	p_range = p_arg
temp_type = sys.argv[5]

# build tables
t_table = []
s_table = []
for file in files:
	fid = open(file)
	filetype = file.split('.')[-1]
	p = wod.WodProfile(fid)
	while True:
		if y != p.year() or m != p.month():
			continue

		pindex = p.var_index(25)

		# extract and QC filter in situ measurements
		temp,psal,pres = filterQCandPressure(p.t(), p.s(), p.p(), p.t_level_qc(originator=False), p.s_level_qc(originator=False), p.var_level_qc(pindex), [0], 10000000)

		# make sure there's meaningful data in range:
		## single level interpolation: a level with both temp and salinity within <radius> of p_interp
		if p_interp:
			radius = 15
			p_min = max(0,p_interp-15)
			p_max = p_interp+15
			p_min_i = bisect.bisect_left(pres, p_min)
			p_max_i = bisect.bisect_right(pres, p_max)
			t_in_radius = temp[p_min_i:p_max_i]
			s_in_radius = psal[p_min_i:p_max_i]
			if not has_common_non_nan_value(t_in_radius, s_in_radius):
				continue
		## range integral: entire integral range is inside the pressure range found in the profile
		elif p_range:
			if p_range[0] < pres[0] or p_range[1] > pres[-1]:
				continue

		# narrow down levels considered to things near the region of interest
		near = 100 # dbar on either side of the level or integration region
		places = 5 # make sure we're keeping at least 5 levels above and below the ROI
		if p_interp:
			p_bracket = pad_bracket(pres, p_interp, p_interp, near, places)
		elif p_range:
			p_bracket = pad_bracket(pres, p_range[0], p_range[1], near, places)
		p_region = pres[p_bracket[0]:p_bracket[1]+1]
		t_region = temp[p_bracket[0]:p_bracket[1]+1]
		s_region = psal[p_bracket[0]:p_bracket[1]+1]

		# compute absolute salinity
		abs_sal = [gsw.conversions.SA_from_SP(s_region[i], p_region[i], p.longitude(), p.latitude()) for i in range(len(p_region))]

		# compute potential or conservative temperature; t_star will be whichever one we're interested in
		if temp_type == 'potential':
			t_potential = gsw.conversions.pt0_from_t(abs_sal, t_region, p_region)
			t_star = [t + 273.15 for t in t_potential]
		elif temp_type == 'conservative':
			t_conservative = gsw.conversions.CT_from_t(abs_sal, t_region, p_region)
			t_star = [t + 273.15 for t in t_conservative]

		# interpolate to specific level:
		if p_interp:
			if not numpy.isnan(t_star).all():
				try:
					t_interp = scipy.interpolate.pchip_interpolate(p_region, t_star, p_interp)
					t_table.append([
						mljul(p.year(),p.month(),p.day(),p.time()),
						remap_longitude(p.longitude()), 
						p.latitude(), 
						p.month(),
						[p_interp],
						[t_interp],
						p.year(),
						#filetype,
						0,
						0
					])	
				except:
					print(p.uid())
					print('pressure', p_region)
					print('temperature', t_region)
			if not numpy.isnan(abs_sal).all():
				try:
					s_interp = scipy.interpolate.pchip_interpolate(p_region, abs_sal, p_interp)
					s_table.append([
						mljul(p.year(),p.month(),p.day(),p.time()),
						remap_longitude(p.longitude()), 
						p.latitude(), 
						p.month(),
						[p_interp],
						[s_interp],
						p.year(),
						#filetype,
						0,
						0
					])
				except:
					print(p.uid())
					print('pressure', p_region)
					print('salinity', abs_sal)
		# integrate across ROI
		elif p_range:
			if not numpy.isnan(t_star).all():
				try:
					t_integrate = interpolate_and_integrate(p_region, t_star, p_range[0], p_range[1])
					t_table.append([
						mljul(p.year(),p.month(),p.day(),p.time()),
						remap_longitude(p.longitude()), 
						p.latitude(), 
						p.month(),
						p_range,
						[t_integrate],
						p.year(),
						#filetype,
						0,
						0
					])	
				except:
					print(p.uid())
					print('pressure', p_region)
					print('temperature', t_region)
			if not numpy.isnan(abs_sal).all():
				try:
					s_integrate = interpolate_and_integrate(p_region, abs_sal, p_range[0], p_range[1])
					s_table.append([
						mljul(p.year(),p.month(),p.day(),p.time()),
						remap_longitude(p.longitude()), 
						p.latitude(), 
						p.month(),
						p_range,
						[s_integrate],
						p.year(),
						#filetype,
						0,
						0
					])
				except:
					print(p.uid())
					print('pressure', p_region)
					print('salinity', abs_sal)

		if p.is_last_profile_in_file(fid):
			break
		else:
			p = wod.WodProfile(fid)

# choose names for whatever it was we just calculated
if p_interp and temp_type == 'potential':
	tname = 'potentialTemperature'
elif p_interp and temp_type == 'conservative':
	tname = 'conservativeTemperature'
elif p_range and temp_type == 'potential':
	tname = 'potentialTemperatureIntegral'
elif p_range and temp_type == 'conservative':
	tname = 'conservativeTemperatureIntegral'
if p_interp:
	sname = 'absoluteSalinity'
	pname = 'interpolatedPressure'
elif p_range:
	sname = 'absoluteSalinityIntegral'
	pname = 'pressureRange'

t_df = pandas.DataFrame(t_table, columns = [
		'profJulDayAggr',  
		'profLongAggr', 
		'profLatAggr', 
		'profMonthAggr',
		pname, 
		tname, 
		'profYearAggr', 
		#'WODtype', 
		'profCycleNumberAggr', 
		'profFloatIDAggr'
	]) 

print(t_df)

#scipy.io.savemat(f'/scratch/alpine/wimi7695/wod/interp/TS_WOD_PFL_CTD_MBR_{m}_{y}_{p_interp}_temp.mat', df.to_dict("list"))

s_df = pandas.DataFrame(s_table, columns = [
		'profJulDayAggr',  
		'profLongAggr', 
		'profLatAggr', 
		'profMonthAggr',
		pname, 
		sname, 
		'profYearAggr', 
		#'WODtype', 
		'profCycleNumberAggr', 
		'profFloatIDAggr'
	]) 

#scipy.io.savemat(f'/scratch/alpine/wimi7695/wod/interp/TS_WOD_PFL_CTD_MBR_{m}_{y}_{p_interp}_psal.mat', df.to_dict("list"))

