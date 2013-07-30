# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import ukidss
import astropy.coordinates as coord
import astropy.units as u

def test_regression_14():
    """
    Regression test for Issue 14:
    https://github.com/astropy/astroquery/issues/14
    """

    ukidss.core.Ukidss.get_images(coord.GalacticCoordinates(l=281.9027, b=-1.9425, unit=(u.deg, u.deg)), radius=1 * u.arcmin, waveband='all')

def test_ukidss_catalog():
    """
    Copy of doctests for catalog query
    """
    # not necessary to specify database, but done so that changes don't break tests
    ukidss.core.Ukidss.query_region(coord.GalacticCoordinates(l=10.625,b=-0.38,unit=(u.deg, u.deg)), radius=0.1*u.arcmin)

def test_ukidss_get_image_gal():

    # get UWISH2 data (as per http://astro.kent.ac.uk/uwish2/main.html)

    c = ukidss.core.Ukidss(username='U09B8',password='uwish2',community='nonSurvey', database='U09B8v20120403')
    c.get_images(coord.GalacticCoordinates(l=49.489, b=-0.27, unit=(u.deg, u.deg)), frame_type='leavstack', image_width=5*u.arcmin, waveband='H2')
