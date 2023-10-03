# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest

from astropy.io.fits import HDUList

from ...skyview import SkyView


@pytest.mark.remote_data
def test_get_image_list():
    """ Test Retrieving the URL list for a Skyview Query """
    ETA_CARINAE_MULTI_CASE_ARGS = {'position': 'Eta Carinae',
                                   'survey': ['FERMI', 'HRI', 'DSS']}
    urls = SkyView().get_image_list(**ETA_CARINAE_MULTI_CASE_ARGS)
    assert len(urls) == 7
    for url in urls:
        assert url.startswith('https://skyview.gsfc.nasa.gov/cgi-bin/images')


@pytest.mark.remote_data
def test_get_images():
    """ For a smaller query, test actually opening the FITS response """
    ETA_CARINAE_SINGLE_CASE_ARGS = {'position': 'Eta Carinae',
                                    'survey': ['DSS']}
    images = SkyView().get_images(**ETA_CARINAE_SINGLE_CASE_ARGS)
    assert len(images) == 1
    assert isinstance(images[0], HDUList)
