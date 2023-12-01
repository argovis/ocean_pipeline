import numpy, pandas, glob, datetime, scipy.io, sys, bisect
from wodpy import wod
import scipy.interpolate

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
files = glob.glob(sys.argv[1] + '/ocldb*')
#file = sys.argv[1]
y = int(sys.argv[2])
m = int(sys.argv[3])
p_interp = float(sys.argv[4])
t_table = []
s_table = []
for file in files:
	fid = open(file)
	filetype = file.split('.')[-1]
	p = wod.WodProfile(fid)
	while True:
		pindex = p.var_index(25)

		temp,psal,pres = filterQCandPressure(p.t(), p.s(), p.p(), p.t_level_qc(originator=False), p.s_level_qc(originator=False), p.var_level_qc(pindex), [0], 10000000)
		if len(pres) > 0 and pres[0] <= p_interp and pres[-1] >= p_interp and y == p.year() and m == p.month():

			# make sure there's at least one value within <radius> of p_interp
			radius = 15
			p_min = max(0,p_interp-15)
			p_max = p_interp+15
			p_min_i = bisect.bisect_left(pres, p_min)
			p_max_i = bisect.bisect_right(pres,p_max)
			t_region = temp[p_min_i:p_max_i]
			s_region = psal[p_min_i:p_max_i]

			if not numpy.isnan(t_region).all():
				t_interp = scipy.interpolate.pchip_interpolate(pres, temp, p_interp)
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


			if not numpy.isnan(s_region).all():
				s_interp = scipy.interpolate.pchip_interpolate(pres, psal, p_interp)
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

		if p.is_last_profile_in_file(fid):
			break
		else:
			p = wod.WodProfile(fid)

t_df = pandas.DataFrame(table, columns = [
		'profJulDayAggr',  
		'profLongAggr', 
		'profLatAggr', 
		'profMonthAggr',
		'profPresAggr', 
		'profTempAggr', 
		'profYearAggr', 
		#'WODtype', 
		'profCycleNumberAggr', 
		'profFloatIDAggr'
	]) 

scipy.io.savemat(f'/scratch/alpine/wimi7695/wod/interp/TS_WOD_PFL_CTD_MBR_{m}_{y}_{p_interp}_temp.mat', df.to_dict("list"))

s_df = pandas.DataFrame(table, columns = [
		'profJulDayAggr',  
		'profLongAggr', 
		'profLatAggr', 
		'profMonthAggr',
		'profPresAggr', 
		'profPsalAggr', 
		'profYearAggr', 
		#'WODtype', 
		'profCycleNumberAggr', 
		'profFloatIDAggr'
	]) 

scipy.io.savemat(f'/scratch/alpine/wimi7695/wod/interp/TS_WOD_PFL_CTD_MBR_{m}_{y}_{p_interp}_psal.mat', df.to_dict("list"))





