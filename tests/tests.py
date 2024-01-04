from helpers import helpers

def test_has_common_non_nan_value():

	x = [None, 2, None]
	y = [None, 3, None]
	z = [4, None, None]

	assert helpers.has_common_non_nan_value(x,y)
	assert not helpers.has_common_non_nan_value(x,z)

def test_find_bracket():

	x = [1.2, 3.3, 4.0, 5.1, 8.8, 10]

	assert helpers.find_bracket(x, 2, 6) == (0,4)