# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import ukidss


def test_regression_14():
    """
    Regression test for Issue 14:
    https://github.com/astropy/astroquery/issues/14
    """
    u = ukidss.UKIDSSQuery()
    u.get_images_radius(281.9027, -1.9425, 1.0, filter='all', directory='raw', save=True, n_concurrent=8)


def test_ukidss_catalog():
    """
    Copy of doctests for catalog query
    """
    # not necessary to specify database, but done so that changes don't break tests
    R = ukidss.UKIDSSQuery(programmeID='GPS', database='UKIDSSDR7PLUS')
    data = R.get_catalog_gal(10.625, -0.38, radius=0.1)
    bintable = data[0][1]
    assert bintable.size == 5130


def test_ukidss_get_image_gal():
    R = ukidss.UKIDSSQuery()
    fitsfile = R.get_image_gal(10.5, 0.0)

    # get UWISH2 data (as per http://astro.kent.ac.uk/uwish2/main.html)
    R.database = 'U09B8v20120403'
    R.login(username='U09B8', password='uwish2', community='nonSurvey')
    R.get_image_gal(49.489, -0.27, frametype='leavstack', size=5, filter='H2')
