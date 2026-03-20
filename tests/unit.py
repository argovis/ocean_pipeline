import numpy, pytest, pandas, datetime
from helpers import helpers

def test_filterQCandPressure():

    t = [15,16,17,18,19]
    s = [30,31,32,33,34]
    p = [100,101,102,103,104]
    t_qc = [0,0,1,0,0]
    s_qc = [0,0,0,1,0]
    p_qc = [1,0,0,0,0]

    temp,psal,pressure,temp_qc,psal_qc,pres_qc = helpers.filterQCandPressure(t,s,p,t_qc,s_qc,p_qc,[0],[0],[0], 1000)
    assert temp == [16,19], 'basic filter'
    assert psal == [31,34], 'basic filter'
    assert pressure == [101,104], 'basic filter'
    assert temp_qc == [0,0], 'basic filter'
    assert psal_qc == [0,0], 'basic filter'
    assert pres_qc == [0,0], 'basic filter'

    temp,psal,pressure,temp_qc,psal_qc,pres_qc = helpers.filterQCandPressure(t,s,p,t_qc,s_qc,p_qc,[0,1],[0,1],[0,1], 1000)
    assert temp == [15,16,17,18,19], 'multiple acceptable flags'
    assert psal == [30,31,32,33,34], 'multiple acceptable flags'
    assert pressure == [100,101,102,103,104], 'multiple acceptable flags'
    assert temp_qc == [0,0,1,0,0], 'multiple acceptable flags'
    assert psal_qc == [0,0,0,1,0], 'multiple acceptable flags'
    assert pres_qc == [1,0,0,0,0], 'multiple acceptable flags'

    temp,psal,pressure,temp_qc,psal_qc,pres_qc = helpers.filterQCandPressure(t,s,p,t_qc,s_qc,p_qc,[1],[1],[1], 1000)
    assert temp == [], 'no acceptable flags'
    assert psal == [], 'no acceptable flags'
    assert pressure == [], 'no acceptable flags'
    assert temp_qc == [], 'no acceptable flags'
    assert psal_qc == [], 'no acceptable flags'
    assert pres_qc == [], 'no acceptable flags'

    temp,psal,pressure,temp_qc,psal_qc,pres_qc = helpers.filterQCandPressure(t,s,p,t_qc,s_qc,p_qc,[0,1],[0,1],[0,1], 102)
    assert temp == [15,16], 'pressure limit'
    assert psal == [30,31], 'pressure limit'
    assert pressure == [100,101], 'pressure limit'
    assert temp_qc == [0,0], 'pressure limit'
    assert psal_qc == [0,0], 'pressure limit'
    assert pres_qc == [1,0], 'pressure limit'

    temp,psal,pressure,temp_qc,psal_qc,pres_qc = helpers.filterQCandPressure(t,s,p,t_qc,s_qc,p_qc,[0],[0],[0,1], 1000)
    assert temp == [16,18,19], 'pressure limit'
    assert psal == [31,33,34], 'pressure limit'
    assert pressure == [101,103,104], 'pressure limit'
    assert temp_qc == [0,0,0], 'pressure limit'
    assert psal_qc == [0,1,0], 'pressure limit'
    assert pres_qc == [0,0,0], 'pressure limit'


def test_mljul():
    assert numpy.allclose(helpers.mljul(2016, 8, 29, 10 + 5/60 + 24/60/60), 2457629.92041667), 'according to the matlab docs https://www.mathworks.com/help//releases/R2021a/matlab/ref/datetime.juliandate.html'
    assert numpy.allclose(helpers.mljul(2016, 8, 29, None), 2457629.5), 'deal with None for time'

def test_find_bracket():

	x = numpy.array([1.2, 3.3, 4.0, 5.1, 8.8, 10])

	assert helpers.find_bracket(x, 2, 6) == (0,4), 'basic bracket'
	assert helpers.find_bracket(x, 1, 6) == (0,4), 'if ROI runs off low end of list, give list boundary'
	assert helpers.find_bracket(x, 2, 11) == (0,5), 'if ROI runs off high end of list, give list boundary'

def test_pad_bracket():

	x = numpy.array([1.2, 3.3, 4.0, 5.1, 8.8, 10])

	assert helpers.pad_bracket(x, 3.5, 4.5, 1, 0) == (0,4), 'basic bracket'
	assert helpers.pad_bracket(x, 3.5, 4.5, 0.1, 0) == (1,3), 'basic bracket with small wing'
	assert helpers.pad_bracket(x, 3.5, 4.5, 0.1, 1) == (1,3), 'wing always includes one point, should be the same as above'
	assert helpers.pad_bracket(x, 3.5, 4.5, 0.1, 2) == (0,4), 'push wing out with extra points requested'
	assert helpers.pad_bracket(x, 3.5, 4.5, 0.1, 3) == (0,5), 'push wing out more, ok to get stuck at the list boundary'
	assert helpers.pad_bracket(x, 1, 11, 0, 0) == (0,5), 'an roi beyond the bounds of the list just returns the whole list'
	assert helpers.pad_bracket(x, 3.5, 4.5, 10, 0) == (0,5), 'a large wing just returns the whole list'
	assert helpers.pad_bracket(x, 3.5, 4.5, 0, 10) == (0,5), 'a large places requirement just returns the whole list'

def test_integrate_roi():
    x = numpy.array([0,2,4,6])
    y = numpy.array([1,2,3,4])

    assert numpy.isclose(helpers.integrate_roi(x, y, 0, 4), 8), 'basic integral'
    assert numpy.isclose(helpers.integrate_roi(x, y, 0, 6), 15), 'integral hitting high edge'
    with pytest.raises(Exception):
        helpers.integrate_roi(x, y, 1, 4), 'bounds must be in the list'

def test_mask_far_interps():

    insitu_pres = numpy.array([0.,1.,2.,3.,4.,5.,6.,7.,8.,9.,15.])
    interp_pres = numpy.array([4.5, 25.0, 1000.0]) # note its not this function's job to disqualify levels outside of the range of measurements, only interpolated levels that don't have a close neighbor.
    interp_vals = numpy.array([0.,1.,2.])

    assert numpy.allclose(helpers.mask_far_interps(insitu_pres, interp_pres, interp_vals)[0], [0,1,numpy.nan],equal_nan=True), 'basic mask'

def test_interpolate_to_levels():

    profile = {'juld': 100, 'latitude': 1, 'longitude': 2, 'pressure': [1,2,3,4,5], 'temperature': [10,20,30,40,50], 'salinity': [35,34,33,32,31], 'flag': 0}
    degen_profile = {'juld': 100, 'latitude': 1, 'longitude': 2, 'pressure': [1,1,3,4,5], 'temperature': [10,20,30,40,50], 'salinity': [35,34,33,32,31], 'flag': 0}
    df = pandas.DataFrame([profile, degen_profile])

    assert numpy.allclose(helpers.interpolate_to_levels(df.iloc[0], 'temperature', [1.5,2.5,3.5,4.5])[0], [15,25,35,45]), 'basic interp'
    assert numpy.allclose(helpers.interpolate_to_levels(df.iloc[0], 'temperature', [1.5,2.5,3.5,4.5])[1], 0), 'basic interp flagging'
    assert numpy.allclose(helpers.interpolate_to_levels(df.iloc[0], 'temperature', [2,4,6])[0], [20,40, numpy.nan], equal_nan=True), 'dont run off end of insitu data'
    assert numpy.allclose(helpers.interpolate_to_levels(df.iloc[0], 'temperature', [0.9999,2,4])[0], [numpy.nan,20,40], equal_nan=True), 'dont run off start of insitu data'
    assert numpy.allclose(helpers.interpolate_to_levels(df.iloc[1], 'temperature', [2,4,6])[0], [numpy.nan,40,numpy.nan], equal_nan=True), 'degenerate profile'
    assert numpy.allclose(helpers.interpolate_to_levels(df.iloc[1], 'temperature', [2,4,6])[1], 65), 'degenerate profile + cant extrapolate flagging'

def test_integration_regions():

    pressure = numpy.array([0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32])
    var = numpy.array([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,numpy.nan])

    assert numpy.allclose(helpers.integration_region([0,10], pressure, var), [25]), 'basic integration'

def test_integration_comb():

    regions = [0,10]

    assert numpy.allclose(helpers.integration_comb(regions, 0.5), [0,0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10]), 'basic comb'

def test_remap_longitude():
    assert helpers.remap_longitude(0) == 360, 'basic remap'
    assert helpers.remap_longitude(180) == 180, 'basic remap'
    assert helpers.remap_longitude(10) == 370, 'basic remap'
    assert helpers.remap_longitude(379) == 379, 'basic remap'
    assert helpers.remap_longitude(-180) == 180, 'basic remap'
    assert helpers.remap_longitude(-360) == 360, 'basic remap'

def test_choose_profile():

    assert helpers.choose_profile(pandas.DataFrame([['a', [2,4,6,8,10]], ['b', [1,2,3,4,5,6,7,8,9,10]] ], columns=['dummy_label', 'pressure']) )['dummy_label'] == 'b', 'choose higher resolution when all else equal'
    assert helpers.choose_profile(pandas.DataFrame([['a', [1,2,3,4,6,7,8,9,10,11]], ['b', [1,2,3,4,5,6,7,8,9,10]] ], columns=['dummy_label', 'pressure']) )['dummy_label'] == 'a', 'choose slightly lower resolution if it goes deeper'
    assert helpers.choose_profile(pandas.DataFrame([['a', [1,2,3,4,6]], ['b', [2,4,6,7.1,7.2,7.3,7.4,7.5,7.6,7.7,7.8,7.9,8]] ], columns=['dummy_label', 'pressure']) )['dummy_label'] == 'a', 'levels below the shallowest bottom dont count'
    assert helpers.choose_profile(pandas.DataFrame([['a', [2,4,6,8,10,100]], ['b', [1,2,3,4,5,6,7,8,9,10]] ], columns=['dummy_label', 'pressure']) )['dummy_label'] == 'b', 'choose higher resolution even when another profile goes deeper'

def test_merge_qc():
    assert helpers.merge_qc([[0,0,0], [0,0,2], [0,0,1]]) == [0,0,2], 'basic merge'

def test_tidy_profile():
    assert helpers.tidy_profile([1,2,3,3,4], [6,7,8,9,10], 0) == ([1,2,4], [6,7,10], 1), 'mask degen neighbors'
    assert helpers.tidy_profile([6,5,4,3],[2,5,3,4], 0) == ([3,4,5,6], [4,3,5,2], 2), 'levels in reverse order'
    assert helpers.tidy_profile([1,2,4,3,5], [6,1,4,2,9], 0) == ([1,2,3,4,5], [6,1,2,4,9], 8), 'levels out of order'

def test_datenum_to_datetime():
    datenum = 736333.6493055555 # 2016-01-04T15:35:00.000Z
    expected_datetime = datetime.datetime(2016, 1, 4, 15, 35)
    result = helpers.datenum_to_datetime(datenum)
    delta = abs(result - expected_datetime)
    assert delta < datetime.timedelta(seconds=1)

    datenum = 712224 # see https://www.mathworks.com/help/exlink/convert-dates-between-microsoft-excel-and-matlab.html
    expected_datetime = datetime.datetime(1950, 1, 1, 0, 0)
    result = helpers.datenum_to_datetime(datenum)
    delta = abs(result - expected_datetime)
    assert delta < datetime.timedelta(seconds=1)

def test_datetime_to_datenum():
    # examples from https://www.mathworks.com/help/matlab/ref/datetime.datenum.html
    dt = datetime.datetime(2007, 9, 16, 0, 0)
    expected_datenum = 733301
    result = helpers.datetime_to_datenum(dt)
    assert abs(result-expected_datenum) < 0.00001, 'datetime to datenum conversion'

    dt = datetime.datetime(1996, 5, 14, 0, 0)
    expected_datenum = 729159
    result = helpers.datetime_to_datenum(dt)
    assert abs(result-expected_datenum) < 0.00001, 'datetime to datenum conversion'

    dt = datetime.datetime(2010, 11, 29, 0, 0)
    expected_datenum = 734471
    result = helpers.datetime_to_datenum(dt)
    assert abs(result-expected_datenum) < 0.00001, 'datetime to datenum conversion'

    dt = datetime.datetime(2025, 2, 1, 8, 46, 48)
    expected_datenum = 739649.3658360614
    result = helpers.datetime_to_datenum(dt)
    assert abs(result-expected_datenum) < 0.00001, 'datetime to datenum conversion'

def test_pchip_search():
    # pchip_search(target, init_min, init_max, init_step, row, variable)

    profile = {'juld': 100, 'latitude': 1, 'longitude': 2, 'pressure': [1,2,3,4,5], 'temperature': [10,20,30,40,50], 'salinity': [35,34,33,32,31], 'flag': 0}
    df = pandas.DataFrame([profile])

    assert numpy.isclose(helpers.pchip_search(20.35, 1, 4, 1, df.iloc[0], 'temperature'), 2.035), 'pchip search basic'
    assert numpy.isclose(helpers.pchip_search(20.35, -10, 10, 1, df.iloc[0], 'temperature'), 2.035), 'cope with too-big range'
    assert helpers.pchip_search(500, -10, 10, 1, df.iloc[0], 'temperature') is None, 'cope with dependent value out of range'
    assert helpers.pchip_search(20.35, 3, 5, 1, df.iloc[0], 'temperature') is None, 'cope with ill-considered search region'

def steric_dummy_profile():
    # a single profile pulled from ECCO's examples so we cn check for consistency

    p_pa = [50693.86,   151104.2 ,   251518.81,   351937.66,   452364.56,   552823.3, 653345.1 ,   753988.06,   854841.  ,   956241.1 ,  1059132.  ,  1165520.4, 1279179. ,   1406052.6,   1554507.9,   1735234.2,   1960389.8,   2242443.2, 2592969. ,   3021236.2,   3533252.2,   4131203.5,   4813050. ,   5572917.5, 6401650. ,   7287760. ,   8218831. ,   9182732. ,  10168828. ,  11168938., 12178466.,   13199039.,   14243196.,   15338622.,   16527386.,   17857848., 19372716.,   21100988.,   23057768.,   25249012.,   27676804.,   30342108., 33245700.,   36388416.,   39771152.,   43394844.]
    profile = {
        'pressure': [p/10000. for p in p_pa],
        'absolute_salinity': [35.740704, 35.74047 , 35.740253, 35.74011 , 35.791935, 35.993553, 36.154236, 36.155464, 36.039345, 35.878483, 35.719044, 35.57875 , 35.457626, 35.348583, 35.246   , 35.151165, 35.068886, 35.001835, 34.95113 , 34.91935 , 34.90545 , 34.896297, 34.872807, 34.82736 , 34.771805, 34.729393, 34.717014, 34.73745 , 34.78228 , 34.83682 , 34.88698 , 34.9255  , 34.951996, 34.96873 , 34.97748 , 34.979218, 34.975174, 34.967308, 34.957714, 34.948082, 34.93924 , 34.931137, 34.92283 , 34.913082, 34.902054, 34.89157],
        'conservative_temperature': [26.25490762, 26.2526441 , 26.24980898, 26.24537066, 26.12370909, 25.03197028, 23.04100463, 20.76708524, 18.63356992, 16.84369306, 15.4457291 , 14.38836105, 13.57298315, 12.89599416, 12.28058422, 11.69996678, 11.15768665, 10.65201655, 10.1746791 ,  9.73397494, 9.33730091,  8.93909306,  8.45316596,  7.83153825,  7.11627806, 6.4218868 ,  5.85085284,  5.44162926,  5.17416019,  4.9920434 , 4.83407749,  4.66293618,  4.46776533,  4.25059203,  4.01683401, 3.77341731,  3.52860259,  3.29117292,  3.06666884,  2.85931313, 2.67026141,  2.49932292,  2.33837903,  2.17755657,  2.01927576, 1.88600045],
        'flag': 0
    }

    return profile

def test_steric_hgt_anom():
    # check that steric_hgt_anom is consistent with the ECCO implementation up to integration

    profile = steric_dummy_profile()

    specvol_anom = helpers.steric_hgt_anom(profile, testbit=True)
    specvol_anom_ecco = [4.49457432e-06, 4.49876016e-06, 4.50275999e-06, 4.50622333e-06, 4.43787138e-06, 3.97711569e-06, 3.30090064e-06, 2.69346269e-06,2.24451338e-06, 1.94305432e-06, 1.75192026e-06, 1.63397612e-06,1.56021411e-06, 1.51063018e-06, 1.47257482e-06, 1.43943048e-06,1.40797111e-06, 1.37553415e-06, 1.33949511e-06, 1.29897913e-06,1.25545929e-06, 1.21070486e-06, 1.16493037e-06, 1.11696317e-06,1.06569810e-06, 1.01119857e-06, 9.54287636e-07, 8.96373426e-07,8.39763212e-07, 7.87281032e-07, 7.40953792e-07, 7.01013448e-07,6.66308132e-07, 6.35648715e-07, 6.08755706e-07, 5.86103790e-07,5.68002219e-07, 5.54120807e-07, 5.43476002e-07, 5.35188442e-07,5.28623890e-07, 5.23652775e-07, 5.19582012e-07, 5.15514361e-07,5.11455215e-07, 5.09870761e-07]
    assert numpy.allclose(specvol_anom, specvol_anom_ecco), "specvol_anom should match ECCO"
    assert numpy.allclose(helpers.steric_hgt_anom(profile), [2.079517702385701]), "steric_hgt_anom stability check"

def test_thermosteric_hgt_anom_linear():
    # check that thermosteric_hgt_anom_linear is consistent with the ECCO implementation up to integration

    profile = steric_dummy_profile()

    specvol_thermo_anom_linear = helpers.thermosteric_hgt_anom_linear(profile, testbit=True)
    specvol_thermo_anom_linear_ecco = [1.35718400e-06, 1.36449070e-06, 1.37176350e-06, 1.37894772e-06,1.37993486e-06, 1.32933609e-06, 1.23011407e-06, 1.11458548e-06,1.00535515e-06, 9.13578233e-07, 8.42213540e-07, 7.88851129e-07,7.48471982e-07, 7.15724132e-07, 6.86674131e-07, 6.60125566e-07,6.36553363e-07, 6.16095656e-07, 5.98434786e-07, 5.84122472e-07,5.73604585e-07, 5.63960894e-07, 5.49239363e-07, 5.25250590e-07,4.93476188e-07, 4.60893025e-07, 4.34754253e-07, 4.18577474e-07,4.11784691e-07, 4.10714099e-07, 4.10776664e-07, 4.08907135e-07,4.04153923e-07, 3.96782929e-07, 3.87479457e-07, 3.77076566e-07,3.66437132e-07, 3.56369744e-07, 3.47304164e-07, 3.39562077e-07,3.33194855e-07, 3.28159455e-07, 3.23373691e-07, 3.17319784e-07,3.10096330e-07, 3.05139265e-07]
    assert numpy.allclose(specvol_thermo_anom_linear, specvol_thermo_anom_linear_ecco), "specvol_thermo_anom_linear should match ECCO"
    assert numpy.allclose(helpers.thermosteric_hgt_anom_linear(profile), [1.0078781446471092]), "thermosteric_hgt_anom_linear stability check"

def test_thalosteric_hgt_anom_linear():
    # check that halosteric_hgt_anom_linear is consistent with the ECCO implementation up to integration

    profile = steric_dummy_profile()

    specvol_halo_anom_linear = helpers.halosteric_hgt_anom_linear(profile, testbit=True)
    specvol_halo_anom_linear_ecco = [-4.37110406e-07, -4.36843472e-07, -4.36589548e-07, -4.36391881e-07,-4.75622156e-07, -6.28460392e-07, -7.50191630e-07, -7.50969345e-07,-6.62788618e-07, -5.40731817e-07, -4.19802300e-07, -3.13425364e-07,-2.21611088e-07, -1.38983734e-07, -6.12866496e-08,  1.04995149e-08,7.27286342e-08,  1.23373940e-07,  1.61589430e-07,  1.85435649e-07,1.95724199e-07,  2.02381038e-07,  2.19768463e-07,  2.53558251e-07,2.94782728e-07,  3.25996963e-07,  3.34636706e-07,  3.18759222e-07,2.84779896e-07,  2.43716689e-07,  2.06058301e-07,  1.77155075e-07,1.57235553e-07,  1.44573345e-07,  1.37807680e-07,  1.36175952e-07,1.38729354e-07,  1.43992907e-07,  1.50409623e-07,  1.56735651e-07,1.62367977e-07,  1.67345267e-07,  1.72342028e-07,  1.78226733e-07,1.84863498e-07,  1.90956750e-07]
    assert numpy.allclose(specvol_halo_anom_linear, specvol_halo_anom_linear_ecco), "specvol_halo_anom_linear should match ECCO"
    assert numpy.allclose(helpers.halosteric_hgt_anom_linear(profile), [0.3189293498222558]), "halosteric_hgt_anom_linear stability check"

def test_thermosteric_hgt_anom():
    # check that thermosteric_hgt_anom is consistent with the ECCO implementation up to integration

    profile = steric_dummy_profile()

    specvol_thermo_anom = helpers.thermosteric_hgt_anom(profile, testbit=True)
    specvol_thermo_anom_ecco = [4.90042461e-06, 4.90437870e-06, 4.90815929e-06, 4.91145686e-06,4.87964092e-06, 4.56205475e-06, 4.00194794e-06, 3.39871568e-06,2.87007126e-06, 2.45569624e-06, 2.15137849e-06, 1.93307560e-06,1.77218278e-06, 1.64382727e-06, 1.53141667e-06, 1.42933218e-06,1.33790547e-06, 1.25649074e-06, 1.18334303e-06, 1.11953110e-06,1.06581171e-06, 1.01435129e-06, 9.51365697e-07, 8.70055240e-07,7.77961695e-07, 6.92249446e-07, 6.26249552e-07, 5.83461042e-07,5.59947803e-07, 5.47659675e-07, 5.38244120e-07, 5.26630871e-07,5.11425720e-07, 4.93128884e-07, 4.72792049e-07, 4.51632502e-07,4.30887865e-07, 4.11680287e-07, 3.94564098e-07, 3.79892798e-07,3.67632195e-07, 3.57616887e-07, 3.48482021e-07, 3.38462830e-07,3.27699967e-07, 3.19960234e-07]
    assert numpy.allclose(specvol_thermo_anom, specvol_thermo_anom_ecco), "specvol_thermo_anom should match ECCO"
    assert numpy.allclose(helpers.thermosteric_hgt_anom(profile), [1.7641229540705763]), "thermosteric_hgt_anom stability check"

def test_thalosteric_hgt_anom():
    # check that halosteric_hgt_anom_linear is consistent with the ECCO implementation up to integration

    profile = steric_dummy_profile()

    specvol_halo_anom = helpers.halosteric_hgt_anom(profile, testbit=True)
    specvol_halo_anom_ecco = [-4.36924437e-07, -4.36657737e-07, -4.36404036e-07, -4.36206545e-07,-4.75402010e-07, -6.28076054e-07, -7.49644010e-07, -7.50420613e-07,-6.62361201e-07, -5.40447336e-07, -4.19630837e-07, -3.13329791e-07,-2.21563308e-07, -1.38964942e-07, -6.12829957e-08,  1.04996222e-08,7.27337789e-08,  1.23388743e-07,  1.61614819e-07,  1.85469076e-07,1.95761426e-07,  2.02420824e-07,  2.19815357e-07,  2.53620636e-07,2.94866989e-07,  3.26099929e-07,  3.34745101e-07,  3.18857471e-07,2.84858223e-07,  2.43773983e-07,  2.06099201e-07,  1.77185261e-07,1.57259294e-07,  1.44593380e-07,  1.37825846e-07,  1.36193647e-07,1.38747663e-07,  1.44012557e-07,  1.50430965e-07,  1.56758695e-07,1.62392536e-07,  1.67371138e-07,  1.72369191e-07,  1.78255432e-07,1.84893928e-07,  1.90988658e-07]
    assert numpy.allclose(specvol_halo_anom, specvol_halo_anom_ecco), "specvol_halo_anom should match ECCO"
    assert numpy.allclose(helpers.halosteric_hgt_anom(profile), [0.3190518312082038]), "halosteric_hgt_anom stability check"