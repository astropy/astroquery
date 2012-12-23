from astroquery import ukidss

def test_regression_14():
    """
    Regression test for Issue 14:
    https://github.com/astropy/astroquery/issues/14
    """
    u = ukidss.UKIDSSQuery()
    u.get_images_radius(281.9027, -1.9425, 1.0, filter='all', directory='raw', save=True, n_concurrent=8)

