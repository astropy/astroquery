# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.tests.helper import remote_data
import requests
import imp

from ... import magpis

imp.reload(requests)


@remote_data
class TestMagpis:

    def test_get_images_async(self):
        response = magpis.core.Magpis.get_images_async(
            SkyCoord(10.5, 0.0, unit=(u.deg, u.deg), frame='galactic'),
            image_size='1 arcmin')
        assert response is not None

    def test_get_images(self):
        image = magpis.core.Magpis.get_images(
            SkyCoord(10.5, 0.0, unit=(u.deg, u.deg), frame='galactic'),
            image_size='1 arcmin')
        assert image is not None
        assert image[0].data.shape == (8, 8)
