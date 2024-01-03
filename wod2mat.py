# usage: python <WOD ascii file directory> <year> <month> <pressure level of interest OR pressure range shallow,deep for integral> <'conservative' or 'potential' temperature switch>

import numpy, pandas, glob, datetime, scipy.io, sys, bisect, gsw
from wodpy import wod
import scipy.interpolate
import scipy.integrate
import helpers

pandas.set_option('display.max_colwidth', None)
pandas.set_option('display.max_rows', None)

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
		temp,psal,pres = helpers.filterQCandPressure(p.t(), p.s(), p.p(), p.t_level_qc(originator=False), p.s_level_qc(originator=False), p.var_level_qc(pindex), [0], 10000000)

		# make sure there's meaningful data in range:
		## single level interpolation: a level with both temp and salinity within <radius> of p_interp
		if p_interp:
			p_min_i, p_max_i = helpers.pad_bracket(pres, p_interp, p_interp, 15, 0)
			t_in_radius = temp[p_min_i+1:p_max_i]
			s_in_radius = psal[p_min_i+1:p_max_i]
			if not helpers.has_common_non_nan_value(t_in_radius, s_in_radius):
				continue
		## range integral: entire integral range is inside the pressure range found in the profile
		elif p_range:
			if p_range[0] < pres[0] or p_range[1] > pres[-1]:
				continue

		# narrow down levels considered to things near the region of interest
		near = 100 # dbar on either side of the level or integration region
		places = 5 # make sure we're keeping at least 5 levels above and below the ROI
		if p_interp:
			p_bracket = helpers.pad_bracket(pres, p_interp, p_interp, near, places)
		elif p_range:
			p_bracket = helpers.pad_bracket(pres, p_range[0], p_range[1], near, places)
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
						helpers.mljul(p.year(),p.month(),p.day(),p.time()),
						helpers.remap_longitude(p.longitude()), 
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
						helpers.mljul(p.year(),p.month(),p.day(),p.time()),
						helpers.remap_longitude(p.longitude()), 
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
					t_integrate = helpers.interpolate_and_integrate(p_region, t_star, p_range[0], p_range[1])
					t_table.append([
						helpers.mljul(p.year(),p.month(),p.day(),p.time()),
						helpers.remap_longitude(p.longitude()), 
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
					s_integrate = helpers.interpolate_and_integrate(p_region, abs_sal, p_range[0], p_range[1])
					s_table.append([
						helpers.mljul(p.year(),p.month(),p.day(),p.time()),
						helpers.remap_longitude(p.longitude()), 
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

