# Licensed under a 3-clause BSD style license - see LICENSE.rst


import pytest
import astropy.units as u
from astropy.coordinates import SkyCoord

from ...import nvas


@pytest.mark.remote_data
class TestNvas:

    def test_get_images_async(self):
        image_list = nvas.core.Nvas.get_images_async(
            SkyCoord(l=49.489, b=-0.37, unit=(u.deg, u.deg), frame='galactic'),
            band="K")

        assert len(image_list) > 0

    @pytest.mark.filterwarnings("ignore:Invalid 'BLANK' keyword in header")
    def test_get_images(self):

        images = nvas.core.Nvas.get_images("3c 273", radius=0.5*u.arcsec, band="L", max_rms=200)
        assert images is not None

    def test_get_image_list(self):
        image_urls = nvas.core.Nvas.get_image_list(
            "05h34m31.94s 22d00m52.2s", radius='0d0m0.6s', max_rms=500)

        assert len(image_urls) > 0
