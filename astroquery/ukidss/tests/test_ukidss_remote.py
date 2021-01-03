# Licensed under a 3-clause BSD style license - see LICENSE.rst


import pytest
import astropy.units as u
from astropy.table import Table
from astropy.coordinates import SkyCoord

from ... import ukidss


@pytest.mark.remote_data
class TestUkidss:
    ukidss.core.Ukidss.TIMEOUT = 20

    def test_get_images_1(self):
        images = ukidss.core.Ukidss.get_images("m1")
        assert images is not None

    def test_get_images_2(self):
        images = ukidss.core.Ukidss.get_images(
            SkyCoord(l=49.489, b=-0.27, unit=(u.deg, u.deg), frame='galactic'),
            image_width=5 * u.arcmin)
        assert images is not None

    def test_get_images_async(self):
        images = ukidss.core.Ukidss.get_images_async("m1")
        assert images is not None

    def test_get_image_list(self):
        urls = ukidss.core.Ukidss.get_image_list(
            SkyCoord(ra=83.633083, dec=22.0145, unit=(u.deg, u.deg),
                     frame='icrs'),
            frame_type='all', waveband='all')
        assert len(urls) > 0

    def test_query_region_async(self):
        response = ukidss.core.Ukidss.query_region_async(
            SkyCoord(l=10.625, b=-0.38, unit=(u.deg, u.deg), frame='galactic'),
            radius=6 * u.arcsec, programme_id='GPS')
        assert response is not None

    def test_query_region(self):
        table = ukidss.core.Ukidss.query_region(
            SkyCoord(l=10.625, b=-0.38, unit=(u.deg, u.deg), frame='galactic'),
            radius=6 * u.arcsec, programme_id='GPS')
        assert isinstance(table, Table)
        assert len(table) > 0

    def test_query_region_constraints(self):
        crd = SkyCoord(l=10.625, b=-0.38, unit=(u.deg, u.deg), frame='galactic')
        rad = 6 * u.arcsec
        constraints = '(priOrSec<=0 OR priOrSec=frameSetID)'
        table_noconstraint = ukidss.core.Ukidss.query_region(
            crd, radius=rad, programme_id='GPS')
        table_constraint = ukidss.core.Ukidss.query_region(
            crd, radius=rad, programme_id='GPS', constraints=constraints)

        assert isinstance(table_constraint, Table)
        assert len(table_noconstraint) >= len(table_constraint)
