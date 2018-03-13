# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

# performs similar tests as test_module.py, but performs
# the actual HTTP request rather than monkeypatching them.
# should be disabled or enabled at will - use the
# remote_data decorator from astropy:

from astropy import coordinates as coord
from astropy.table import Table
import astropy.units as u
from astropy.tests.helper import remote_data

from .. import OAC


@remote_data
class TestOACClass:
    """Test methods to verify the functionality of methods in the
    OAC API astroquery module.
    """

    # A simple test object. The kilonova associated with GW170817.
    ra = 197.45037
    dec = -23.38148
    test_coords = coord.SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg))

    test_radius = 10*u.arcsecond
    test_width = 10*u.arcsecond
    test_height = 10*u.arcsecond

    def test_query_object_csv(self):
        phot = OAC.query_object(event='GW170817')
        assert isinstance(phot, Table)

    def test_query_object_json(self):
        phot = OAC.query_object(event='GW170817', data_format='json')
        assert isinstance(phot, dict)

    def test_query_region_cone_csv(self):
        phot = OAC.query_region(coordinates=self.test_coords,
                                radius=self.test_radius)
        assert isinstance(phot, Table)

    def test_query_region_cone_json(self):
        phot = OAC.query_region(coordinates=self.test_coords,
                                radius=self.test_radius,
                                data_format='json')
        assert isinstance(phot, dict)

    def test_query_region_box_csv(self):
        phot = OAC.query_region(coordinates=self.test_coords,
                                width=self.test_width,
                                height=self.test_height)
        assert isinstance(phot, Table)

    def test_query_region_box_json(self):
        phot = OAC.query_region(coordinates=self.test_coords,
                                width=self.test_width,
                                height=self.test_height,
                                data_format='json')
        assert isinstance(phot, dict)

    def test_get_photometry(self):
        phot = OAC.get_photometry(event="GW170817")
        assert isinstance(phot, Table)

    def test_get_single_spectrum(self):
        test_time = 54773
        spec = OAC.get_single_spectrum(event="GW170817", time=test_time)
        assert isinstance(spec, Table)

    def test_get_spectra(self):
        spec = OAC.get_spectra(event="GW170817")
        assert isinstance(spec, dict)
