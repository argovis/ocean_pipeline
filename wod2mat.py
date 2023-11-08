import numpy, pandas, glob, datetime, scipy.io
from wodpy import wod

def mljul(year, month, day, time):
	# compute something appropriate to interpret as matlab's julian day

	# matlab epoch begins noon, Nov 24, 4714 BCE; offest to midnight Jan 1 1900
	julday = 2415020.5

	delta = datetime.date(year,month,day) - datetime.date(1900,1,1)

	return julday + delta.days + time/24.0

def filterQC(t,s,p, t_qc,s_qc,p_qc, acceptable):
	# given <t>emperature, <s>alinity and <p>ressure lists for a profile,
	# the corresponding <>_qc flags,
	# and an <acceptable> list of qc flags,
	# return t,s and p lists with levels dropped if t or p aren't acceptable qc,
	# if t and p are good but s isn't, mask s with NaN.

	data = list(zip(t,s,p,t_qc,s_qc,p_qc))
	goodTP = list(filter(lambda level: level[3] in acceptable and level[5] in acceptable, data))
	t_filter = [x[0] for x in goodTP]
	p_filter = [x[2] for x in goodTP]
	s_filter = [x[1] if x[4] in acceptable else numpy.NAN for x in goodTP]

	return t_filter, s_filter, p_filter

files = glob.glob("./ocldb*")
table = []
for file in files[0:1]:
	fid = open(file)
	filetype = file.split('.')[-1]
	while True:
		p = wod.WodProfile(fid)

		temp,psal,pres = filterQC(p.t(), p.s(), p.p(), p.t_level_qc(originator=False), p.s_level_qc(originator=False), p.z_level_qc(originator=False), [0])

		table.append([
			mljul(p.year(),p.month(),p.day(),p.time()),
			'-'.join([str(p.year()),str(p.month()),str(p.day()),str(p.time())]),
			p.longitude(), 
			p.latitude(), 
			p.month(),
			pres,
			psal,
			temp,
			p.year(),
			filetype
		])
		if p.is_last_profile_in_file(fid):
			break

df = pandas.DataFrame(table, columns = ['profJulDayAggr', 'datestring', 'profMonthAggr', 'profLongAggr', 'profLatAggr', 'profPresAggr', 'profPsalAggr', 'profTempAggr', 'profYearAggr', 'WODtype']) 

scipy.io.savemat('wod.mat', {'struct1':df.to_dict("list")})