# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import astropy.coordinates as coord
import astropy.units as u
from astropy.tests.helper import remote_data
import requests
import imp
imp.reload(requests)

from ... import magpis


@remote_data
class TestMagpis:

    def test_get_images_async(self):
        response = magpis.core.Magpis.get_images_async(
                        coord.Galactic(10.5, 0.0, unit=(u.deg, u.deg)),
                        image_size='1 arcmin')
        assert response is not None

    def test_get_images(self):
        image = magpis.core.Magpis.get_images(
                coord.Galactic(10.5, 0.0, unit=(u.deg, u.deg)),
                image_size='1 arcmin')
        assert image is not None
        assert image[0].data.shape == (8, 8)
