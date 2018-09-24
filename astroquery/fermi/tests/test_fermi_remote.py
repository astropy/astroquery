# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import astropy.coordinates as coord
from astropy.tests.helper import remote_data
from ... import fermi

FK5_COORDINATES = coord.SkyCoord(10.68471, 41.26875, unit=('deg', 'deg'))


@remote_data
def test_FermiLAT_query_async():
    result = fermi.core.FermiLAT.query_object_async(
        FK5_COORDINATES, energyrange_MeV='1000, 100000',
        obsdates='2013-01-01 00:00:00, 2013-01-02 00:00:00')
    assert 'https://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/QueryResults.cgi?' in result


@remote_data
def test_FermiLAT_query():
    # Make a query that results in small SC and PH file sizes
    result = fermi.core.FermiLAT.query_object(
        FK5_COORDINATES, energyrange_MeV='1000, 100000',
        obsdates='2013-01-01 00:00:00, 2013-01-02 00:00:00')
    # this test might be fragile?  I'm not sure how stable the file names are
    for rr in result:
        assert rr.startswith('https://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/')
        assert rr.endswith('_SC00.fits') or rr.endswith('_PH00.fits')
