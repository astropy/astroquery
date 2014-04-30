# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

from astropy.tests.helper import remote_data
from astropy.table import Table
import astropy.coordinates as coord
import astropy.units as u
import requests
import imp
imp.reload(requests)

from ... import ukidss


@remote_data
class TestUkidss:
    ukidss.core.Ukidss.TIMEOUT = 20

    def test_get_images_1(self):
        images = ukidss.core.Ukidss.get_images("m1")
        assert images is not None

    def test_get_images_2(self):
        images = ukidss.core.Ukidss.get_images(coord.Galactic
                                               (l=49.489, b=-0.27, unit=(u.deg, u.deg)),
                                               image_width=5 * u.arcmin)
        assert images is not None

    def test_get_images_async(self):
        images = ukidss.core.Ukidss.get_images_async("m1")
        assert images is not None

    def test_get_image_list(self):
        urls = ukidss.core.Ukidss.get_image_list(coord.ICRS
                                            (ra=83.633083, dec=22.0145, unit=(u.deg, u.deg)),
            frame_type='all', waveband='all')
        assert len(urls) > 0

    def test_query_region_async(self):
        response = ukidss.core.Ukidss.query_region_async(coord.Galactic
                                                   (l=10.625, b=-0.38, unit=(u.deg, u.deg)),
            radius=6 * u.arcsec)
        assert response is not None

    def test_query_region(self):
        table = ukidss.core.Ukidss.query_region(coord.Galactic
                                                (l=10.625, b=-0.38, unit=(u.deg, u.deg)),
                                                radius=6 * u.arcsec)
        assert isinstance(table, Table)
        assert len(table) > 0
