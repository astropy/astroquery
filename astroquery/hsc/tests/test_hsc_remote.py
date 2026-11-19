# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import pytest
from astropy.tests.helper import remote_data
from astropy.table import Table
from astropy.io import fits
import astropy.coordinates as coord
import astropy.units as u

from ... import hsc


@remote_data
@pytest.mark.skip(reason='Local testing. Works only with an HSC archive account.')
class TestHsc:
    def test_query_region_async(self):
        hsc.core.Hsc.login()
        response = hsc.core.Hsc.query_region_async(
            coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'))

        assert response.ok

    def test_query_region(self):
        hsc.core.Hsc.login()
        table = hsc.core.Hsc.query_region(
            coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'),
            radius=6 * u.arcsec)

        assert isinstance(table, Table)
        assert len(table) > 0

    def test_get_images_cutout(self):
        hsc.core.Hsc.login()
        image = hsc.core.Hsc.get_images(
            coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'),
            image_width=10 * u.arcsec)

        assert len(image) == 1
        assert isinstance(image[0], fits.HDUList)

    def test_get_images_async_cutout(self):
        hsc.core.Hsc.login()
        url_list = hsc.core.Hsc.get_images_async(
            coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'))

        assert len(url_list) == 1

    def test_get_image_list_cutout(self):
        hsc.core.Hsc.login()
        url_list = hsc.core.Hsc.get_image_list(
            coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'))

        assert len(url_list) == 1

# This test is not included because coadd images are very large (>100Mb)
#    def test_get_images_coadd(patch_request, patch_get_fits):
#        image = hsc.core.Hsc.get_images(
#            coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'),
#            radius=6 * u.arcsec)
#
#        assert len(image) >= 1
#        assert isinstance(image[0], fits.HDUList)

    def test_get_images_async_coadd(self):
        hsc.core.Hsc.login()
        url_list = hsc.core.Hsc.get_images_async(
            coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'),
            radius=6 * u.arcsec)

        assert len(url_list) >= 1

    def test_get_image_list_coadd(self):
        hsc.core.Hsc.login()
        url_list = hsc.core.Hsc.get_image_list(
            coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'),
            radius=6 * u.arcsec)

        assert len(url_list) >= 1

    def test_get_image_list_coadd_filters(self):
        hsc.core.Hsc.login()
        filters = ['g', 'r']
        url_list = hsc.core.Hsc.get_image_list(
            coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'),
            radius=6 * u.arcsec, filters=filters)

        assert len(url_list) >= 1
        assert len(url_list) <= len(filters)
