# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

# performs similar tests as test_module.py, but performs
# the actual HTTP request rather than monkeypatching them.
# should be disabled or enabled at will - use the
# remote_data decorator from astropy:

import pytest
from astropy.tests.helper import remote_data
from astropy.coordinates import SkyCoord
import astropy.units as u

from ... import hsc


@remote_data
class TestHsc:
    def test_query_region_async(self):
        hsc.core.Hsc.login()
        response = hsc.core.Hsc.query_region_async(
            SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'),
            radius=5 * u.arcsec)
        assert response.ok
        # assert response is not None

#    def test_query_region(self):
#        table = hsc.core.Ukidss.query_region(
#            SkyCoord(l=10.625, b=-0.38, unit=(u.deg, u.deg), frame='icrs'),
#            radius=6 * u.arcsec, programme_id='GPS')
#        assert isinstance(table, Table)
#        assert len(table) > 0
#
#    def test_get_images_1(self):
#        images = hsc.core.Ukidss.get_images("m1")
#        assert images is not None
#
#    def test_get_images_2(self):
#        images = hsc.core.Ukidss.get_images(
#            SkyCoord(l=49.489, b=-0.27, unit=(u.deg, u.deg), frame='galactic'),
#            image_width=5 * u.arcmin)
#        assert images is not None
#
#    def test_get_images_async(self):
#        images = ukidss.core.Ukidss.get_images_async("m1")
#        assert images is not None
#
#    def test_get_image_list(self):
#        urls = ukidss.core.Ukidss.get_image_list(
#            SkyCoord(ra=83.633083, dec=22.0145, unit=(u.deg, u.deg),
#                     frame='icrs'),
#            frame_type='all', waveband='all')
#        assert len(urls) > 0
#
