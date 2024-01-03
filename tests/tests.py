from helpers import helpers

def test_has_common_non_nan_value():

	x = [None, 2, None]
	y = [None, 3, None]
	z = [4, None, None]

    assert helpers.test_has_common_non_nan_value(x,y)
    assert not helpers.test_has_common_non_nan_value(x,z)
