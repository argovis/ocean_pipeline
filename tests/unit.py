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

def test_has_common_non_nan_value():

	x = numpy.array([None, 2, numpy.nan])
	y = numpy.array([None, 3, numpy.nan])
	z = numpy.array([4, None, None])

	assert helpers.has_common_non_nan_value(x,y), 'basic match'
	assert not helpers.has_common_non_nan_value(x,z), 'no match, including None vs nan'

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

def test_interpolate_and_integrate():

	x = numpy.array([0,1,2,3,4,5,6,7,8,9])
	y = numpy.array([10,10,10,2,2,2,2,10,10,10])

	assert numpy.isclose(helpers.interpolate_and_integrate(x, y, 3.5, 4.5), 2), 'basic integral on flat region'
	assert numpy.isclose(helpers.interpolate_and_integrate(x, y, 2, 3), 6), 'integral over slope'
	assert numpy.isclose(helpers.interpolate_and_integrate(x, y, 0, 10), 68), 'integral over whole range'

def test_integrate_roi():
    x = numpy.array([0,2,4,6])
    y = numpy.array([1,2,3,4])

    assert numpy.isclose(helpers.integrate_roi(x, y, 0, 4), 8), 'basic integral'
    assert numpy.isclose(helpers.integrate_roi(x, y, 0, 6), 15), 'integral hitting high edge'
    with pytest.raises(Exception):
        helpers.integrate_roi(x, y, 1, 4), 'bounds must be in the list'

def test_sort_and_remove_neighbors():

	x = [
			[0,0,1234],
			[10,10,1234],
			[0,0,1234.01],
			[0,1,1234.01],
			[0,0,1234.02]
		]

	assert helpers.sort_and_remove_neighbors(x, 0, 1, 2) == [
			[0,0,1234],
			[0,1,1234.01],
			[10,10,1234]
		]

def test_mask_far_interps():

    insitu_pres = numpy.array([0.,1.,2.,3.,4.,5.,6.,7.,8.,9.,15.])
    interp_pres = numpy.array([4.5, 25, 25.1]) # note its not this function's job to disqualify levels outside of the range of measurements, only interpolated levels that don't have a close neighbor.
    interp_vals = numpy.array([0.,1.,2.])

    assert numpy.allclose(helpers.mask_far_interps(insitu_pres, interp_pres, interp_vals), [0,1,numpy.nan],equal_nan=True), 'basic mask'

def test_interpolate_to_levels():

    profile = {'juld': 100, 'latitude': 1, 'longitude': 2, 'pressure': [1,2,3,4,5], 'temperature': [10,20,30,40,50], 'salinity': [35,34,33,32,31], 'flag': 0}
    degen_profile = {'juld': 100, 'latitude': 1, 'longitude': 2, 'pressure': [1,1,3,4,5], 'temperature': [10,20,30,40,50], 'salinity': [35,34,33,32,31], 'flag': 0}
    df = pandas.DataFrame([profile, degen_profile])

    assert numpy.allclose(helpers.interpolate_to_levels(df.iloc[0], 'temperature', [1.5,2.5,3.5,4.5])[0], [15,25,35,45]), 'basic interp'
    assert numpy.allclose(helpers.interpolate_to_levels(df.iloc[0], 'temperature', [1.5,2.5,3.5,4.5])[1], 0), 'basic interp flagging'
    assert numpy.allclose(helpers.interpolate_to_levels(df.iloc[0], 'temperature', [2,4,6])[0], [20,40, numpy.nan], equal_nan=True), 'dont run off end of insitu data'
    assert numpy.allclose(helpers.interpolate_to_levels(df.iloc[0], 'temperature', [0.9999,2,4])[0], [numpy.nan,20,40], equal_nan=True), 'dont run off start of insitu data'
    assert numpy.allclose(helpers.interpolate_to_levels(df.iloc[1], 'temperature', [2,4,6])[0], [numpy.nan,40,numpy.nan], equal_nan=True), 'degenerate profile'
    assert numpy.allclose(helpers.interpolate_to_levels(df.iloc[1], 'temperature', [2,4,6])[1], 1), 'degenerate profile flagging'

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

def test_surrounding_gap():
    RG_levels = [2.5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 182.5, 200, 220, 240, 260, 280, 300, 320, 340, 360, 380, 400, 420, 440, 462.5, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150, 1200, 1250, 1300, 1350, 1412.5, 1500, 1600, 1700, 1800, 1900, 1975]

    assert helpers.surrounding_gap(RG_levels, 11) == 10, 'distance between nearest neighbors'
    assert helpers.surrounding_gap(RG_levels, 170) == 12.5, 'give the higher gap when right on a level'
    assert helpers.surrounding_gap(RG_levels, 1975) == 75, 'give the lower gap at the end of the list'
    assert helpers.surrounding_gap(RG_levels, 2000) == 75, 'give the last gap past the end of the list'
    assert helpers.surrounding_gap(RG_levels, 0) == 7.5, 'give the first gap before the start of the list'

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
    dt = datetime.datetime(1950, 1, 1, 0, 0)
    expected_datenum = 712224
    result = helpers.datetime_to_datenum(dt)
    assert abs(result-expected_datenum) < 0.00001, 'datetime to datenum conversion'

def test_pchip_search():
    # pchip_search(target, init_min, init_max, init_step, row, variable)

    profile = {'juld': 100, 'latitude': 1, 'longitude': 2, 'pressure': [1,2,3,4,5], 'temperature': [10,20,30,40,50], 'salinity': [35,34,33,32,31], 'flag': 0}
    df = pandas.DataFrame([profile])

    assert numpy.isclose(helpers.pchip_search(20.35, 1, 4, 1, df.iloc[0], 'temperature'), 2.035), 'pchip search basic'
    assert numpy.isclose(helpers.pchip_search(20.35, -10, 10, 1, df.iloc[0], 'temperature'), 2.035), 'cope with too-big range'
