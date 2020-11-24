# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import astropy.units as u
from astropy.coordinates import SkyCoord

from ... import first


@pytest.mark.remote_data
class TestFirst:

    def test_get_images_async(self):
        response = first.core.First.get_images_async(
            SkyCoord(162.530, 30.677, unit=(u.deg, u.deg), frame='icrs'),
            image_size='1 arcmin')
        assert response is not None

    def test_get_images(self):
        image = first.core.First.get_images(
            SkyCoord(162.530, 30.677, unit=(u.deg, u.deg), frame='icrs'),
            image_size='1 arcmin')
        assert image is not None
        assert image[0].data.shape == (33, 33)
