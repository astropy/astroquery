# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import astropy.coordinates as coord
import astropy.units as u
from astropy.tests.helper import remote_data
import requests
reload(requests)

from ... import magpis


@remote_data
class TestMagpis:

    def test_get_images_async(self):
        response = magpis.core.Magpis.get_images_async(coord.GalacticCoordinates(10.5, 0.0, unit=(u.deg, u.deg)))
        assert response is not None

    def test_get_images(self):
        image = magpis.core.Magpis.get_images(coord.GalacticCoordinates(10.5, 0.0, unit=(u.deg, u.deg)))
        assert image is not None
