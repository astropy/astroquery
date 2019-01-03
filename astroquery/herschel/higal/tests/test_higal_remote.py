# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest

from astropy import coordinates
from astropy import units as u
from astropy.io import fits
from astropy.table import Table

from ..core import HiGal


# Starting in 2025, anonymous POSTs to HiGALSearch.jsp are silently redirected
# (302) to the front page HiGAL.jsp instead of returning the cutout result page
# with the embedded `fitsHeaders = JSON.parse('...')` JSON. The catalog AJAX
# endpoint (MMCAjaxFunction) is unaffected. Cutout-flow tests are xfailed until
# SSDC restores the endpoint or we determine an alternative.
_CUTOUT_BROKEN = pytest.mark.xfail(
    reason=("SSDC cutout endpoint POST /HiGALSearch.jsp redirects to /HiGAL.jsp "
            "and no longer returns the result page"),
    strict=False,
)


@pytest.mark.remote_data
class TestHiGalRemote:

    def test_catalog_query(self):
        crd = coordinates.SkyCoord(281.85238759, -1.93488693, frame='fk5',
                                   unit=(u.deg, u.deg))

        catalog = HiGal.query_region(crd, radius=10*u.arcmin,
                                     catalog='blue',
                                     cache=False, catalog_query=True)

        assert isinstance(catalog, Table)
        assert 'DESIGNATION' in catalog.colnames
        assert 'HIGALPB030.6606-0.0878' in catalog['DESIGNATION']

    @_CUTOUT_BROKEN
    def test_basic_query(self):
        crd = coordinates.SkyCoord(281.85238759, -1.93488693, frame='fk5',
                                   unit=(u.deg, u.deg))

        base_response = HiGal.query_region_async(crd, radius=10*u.arcmin,
                                                 cache=False,
                                                 catalog_query=False)

        # this text is where the filename JSON data is hidden
        assert "fitsHeaders = JSON.parse('" in base_response.text

    @_CUTOUT_BROKEN
    def test_get_image_list(self):
        crd = coordinates.SkyCoord(49.5, -0.3, frame='galactic',
                                   unit=(u.deg, u.deg))
        urls = HiGal.get_image_list(crd, radius=3*u.arcmin)
        assert len(urls) == 5
        for url in urls:
            assert url.endswith('.fits')

    @_CUTOUT_BROKEN
    def test_get_images(self):
        crd = coordinates.SkyCoord(49.5, -0.3, frame='galactic',
                                   unit=(u.deg, u.deg))

        imlist = HiGal.get_images(crd, radius=3*u.arcmin)

        assert len(imlist) == 5

        for im in imlist:
            assert isinstance(im, fits.HDUList)
