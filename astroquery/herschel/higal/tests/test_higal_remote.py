# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

from astropy.tests.helper import remote_data

from astropy import coordinates
from astropy import units as u
from astropy.io import fits

from ..core import HiGal


@remote_data
class TestTemplateClass:
    def test_basic_query(self):
        crd = coordinates.SkyCoord(*(281.85238759, -1.93488693), frame='fk5',
                                   unit=(u.deg, u.deg))

        # check cutout response
        base_response = HiGal.query_region_async(crd, radius=10*u.arcmin,
                                                 cache=False,
                                                 catalog_query=False)

        # this text is where the filename JSON data is hidden
        assert 'fitsHeaders = JSON.parse(\'' in base_response.text

    def test_catalog_query(self):
        crd = coordinates.SkyCoord(*(281.85238759, -1.93488693), frame='fk5',
                                   unit=(u.deg, u.deg))

        # check catalog response
        catalog = HiGal.query_region_async(crd, radius=10*u.arcmin,
                                           catalog='blue',
                                           cache=False, catalog_query=True)

        assert 'HIGALPB030.6606-0.0878' in catalog['DESIGNATION']

    def test_get_images(self):
        crd = coordinates.SkyCoord(49.5, -0.3, frame='galactic',
                                   unit=(u.deg, u.deg))

        imlist = HiGal.get_images(crd, radius=3*u.arcmin)

        assert len(imlist) == 5

        for im in imlist:
            assert isinstance(im, fits.HDUList)
