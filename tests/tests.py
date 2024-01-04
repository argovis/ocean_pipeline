import numpy
from helpers import helpers

def test_has_common_non_nan_value():

	x = [None, 2, numpy.nan]
	y = [None, 3, numpy.nan]
	z = [4, None, None]

	assert helpers.has_common_non_nan_value(x,y), 'basic match'
	assert not helpers.has_common_non_nan_value(x,z), 'no match, including None vs nan'

def test_find_bracket():

	x = [1.2, 3.3, 4.0, 5.1, 8.8, 10]

	assert helpers.find_bracket(x, 2, 6) == (0,4), 'basic bracket'
	assert helpers.find_bracket(x, 1, 6) == (0,4), 'if ROI runs off low end of list, give list boundary'
	assert helpers.find_bracket(x, 2, 11) == (0,5), 'if ROI runs off high end of list, give list boundary'

def test_pad_bracket():

	x = [1.2, 3.3, 4.0, 5.1, 8.8, 10]

	assert helpers.pad_bracket(x, 3.5, 4.5, 1, 0) == (0,4), 'basic bracket'
	assert helpers.pad_bracket(x, 3.5, 4.5, 0.1, 0) == (1,3), 'basic bracket with small wing'
	assert helpers.pad_bracket(x, 3.5, 4.5, 0.1, 1) == (1,3), 'wing always includes one point, should be the same as above'
	assert helpers.pad_bracket(x, 3.5, 4.5, 0.1, 2) == (0,4), 'push wing out with extra points requested'
	assert helpers.pad_bracket(x, 3.5, 4.5, 0.1, 3) == (0,5), 'push wing out more, ok to get stuck at the list boundary'
	assert helpers.pad_bracket(x, 1, 11, 0, 0) == (0,5), 'an roi beyond the bounds of the list just returns the whole list'
	assert helpers.pad_bracket(x, 3.5, 4.5, 10, 0) == (0,5), 'a large wing just returns the whole list'
	assert helpers.pad_bracket(x, 3.5, 4.5, 0, 10) == (0,5), 'a large places requirement just returns the whole list'

def test_interpolate_and_integrate():

	x = [0,1,2,3,4,5,6,7,8,9]
	y = [10,10,10,2,2,2,2,10,10,10]

	assert numpy.isclose(helpers.interpolate_and_integrate(x, y, 3.5, 4.5), 2), 'basic integral on flat region'
	assert numpy.isclose(helpers.interpolate_and_integrate(x, y, 2, 3), 6), 'integral over slope'
	assert numpy.isclose(helpers.interpolate_and_integrate(x, y, 0, 10), 68), 'integral over whole range'