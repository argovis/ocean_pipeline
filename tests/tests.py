import numpy, pytest, pandas
from helpers import helpers

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

    insitu_pres = numpy.array([0.,1.,2.,3.,4.,5.,6.,7.,8.,9.])
    interp_pres = numpy.array([4.5, 20, 50]) # note its not this function's job to disqualify levels outside of the range of measurements, only interpolated levels that don't have a close neighbor.
    interp_vals = numpy.array([0.,1.,2.])

    assert numpy.allclose(helpers.mask_far_interps(insitu_pres, interp_pres, interp_vals), [0,1,numpy.nan],equal_nan=True), 'basic mask'

def test_interpolate_to_levels():

    profile = {'juld': 100, 'latitude': 1, 'longitude': 2, 'pressure': [1,2,3,4,5], 'temperature': [10,20,30,40,50], 'salinity': [35,34,33,32,31]}
    degen_profile = {'juld': 100, 'latitude': 1, 'longitude': 2, 'pressure': [1,1,3,4,5], 'temperature': [10,20,30,40,50], 'salinity': [35,34,33,32,31]}
    df = pandas.DataFrame([profile, degen_profile])

    assert numpy.allclose(helpers.interpolate_to_levels(df.iloc[0], 'temperature', [1.5,2.5,3.5,4.5]), [15,25,35,45]), 'basic interp'
    assert numpy.allclose(helpers.interpolate_to_levels(df.iloc[0], 'temperature', [2,4,6]), [20,40, numpy.nan], equal_nan=True), 'dont run off end of insitu data'
    assert numpy.allclose(helpers.interpolate_to_levels(df.iloc[1], 'temperature', [2,4,6]), 0xDEADBEEF), 'degenerate profile'

def test_integration_regions():

    regions = [(0,10), (20,30)]
    pressure = numpy.array([0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30])
    var = numpy.array([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])

    assert numpy.allclose(helpers.integration_regions(regions, pressure, var), [25, 125]), 'basic integration'

def test_integration_comb():

    regions = [(0,10), (20,30)]

    assert numpy.allclose(helpers.integration_comb(regions, 0.5), [0,0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10, 20,20.5,21,21.5,22,22.5,23,23.5,24,24.5,25,25.5,26,26.5,27,27.5,28,28.5,29,29.5,30]), 'basic comb'