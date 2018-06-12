# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import pytest

from astropy.tests.helper import remote_data
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u
import requests
import imp

from ... import vsa

imp.reload(requests)


vista = vsa.core.VsaClass()


@remote_data
class TestVista:

    @pytest.mark.dependency(name='vsa_up')
    def test_is_vsa_up(self):
        try:
            vista._request("GET", "http://horus.roe.ac.uk:8080/vdfs/VgetImage_form.jsp")
        except Exception as ex:
            pytest.xfail("VISTA appears to be down.  Exception was: {0}".format(ex))

    @pytest.mark.dependency(depends=["vsa_up"])
    def test_get_images(self):

        crd = SkyCoord(l=336.489, b=-1.48, unit=(u.deg, u.deg),
                       frame='galactic')
        images = vista.get_images(crd, frame_type='tilestack', image_width=5 *
                                  u.arcmin, waveband='H')
        assert images is not None

    @pytest.mark.dependency(depends=["vsa_up"])
    def test_get_images_async(self):
        crd = SkyCoord(l=336.489, b=-1.48, unit=(u.deg, u.deg), frame='galactic')
        images = vista.get_images_async(crd, frame_type='tilestack',
                                        image_width=5 * u.arcmin, waveband='H')
        assert images is not None

    @pytest.mark.dependency(depends=["vsa_up"])
    def test_get_image_list(self):
        crd = SkyCoord(l=350.488, b=0.949, unit=(u.deg, u.deg), frame='galactic')
        urls = vista.get_image_list(crd, frame_type='all', waveband='all')
        assert len(urls) > 0

    @pytest.mark.dependency(depends=["vsa_up"])
    def test_query_region_async(self):
        crd = SkyCoord(l=350.488, b=0.949, unit=(u.deg, u.deg), frame='galactic')
        response = vista.query_region_async(crd, radius=6 * u.arcsec, programme_id='VVV')
        assert response is not None

    @pytest.mark.dependency(depends=["vsa_up"])
    def test_query_region(self):
        crd = SkyCoord(l=350.488, b=0.949, unit=(u.deg, u.deg), frame='galactic')
        table = vista.query_region(crd, radius=6 * u.arcsec, programme_id='VVV')
        assert isinstance(table, Table)
        assert len(table) > 0
