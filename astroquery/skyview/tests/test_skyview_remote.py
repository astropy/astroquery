# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy.tests.helper import remote_data

from ...skyview import SkyView


@remote_data
def test_get_image_list():
    urls = SkyView().get_image_list(
        position='Eta Carinae', survey=['Fermi 5', 'HRI', 'DSS'])
    assert len(urls) == 3
    for url in urls:
        assert url.startswith('http://skyview.gsfc.nasa.gov/tempspace/fits/')
