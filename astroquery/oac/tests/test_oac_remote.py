# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import pytest

from astropy import coordinates as coord
from astropy.table import Table
import astropy.units as u

from .. import OAC


@pytest.mark.remote_data
class TestOACClass:
    """Test methods to verify the functionality of methods in the
    OAC API astroquery module.
    """

    # A simple test object. The famous supernova SN2014J
    ra = '09:55:42.12'
    dec = '+69:40:25.9'
    test_coords = coord.SkyCoord(ra=ra, dec=dec, unit=(u.hourangle, u.deg))

    test_radius = 60*u.arcsecond
    test_width = 60*u.arcsecond
    test_height = 60*u.arcsecond

    test_time = 56680

    def test_query_object_csv(self):
        phot = OAC.query_object(event='SN2014J')
        assert isinstance(phot, Table)

    def test_query_object_json(self):
        phot = OAC.query_object(event='SN2014J', data_format='json')
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

    @pytest.mark.xfail(reason="Upstream API issue.  See #1130")
    def test_get_photometry(self):
        phot = OAC.get_photometry(event="SN2014J")
        assert isinstance(phot, Table)

    def test_get_photometry_b(self):
        phot = OAC.get_photometry(event="SN2014J")
        assert isinstance(phot, Table)

    @pytest.mark.xfail(reason="Upstream API issue.  See #1130")
    def test_get_single_spectrum(self):
        spec = OAC.get_single_spectrum(event="SN2014J",
                                       time=self.test_time)
        assert isinstance(spec, Table)

    def test_get_single_spectrum_b(self):
        test_time = 56680
        spec = OAC.get_single_spectrum(event="SN2014J", time=test_time)
        assert isinstance(spec, Table)

    def test_get_spectra(self):
        spec = OAC.get_spectra(event="SN2014J")
        assert isinstance(spec, dict)
