
import pytest
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.utils.exceptions import AstropyDeprecationWarning

from .. import Ogle


@pytest.mark.remote_data
def test_ogle_single():
    co = SkyCoord(0, 3, unit=(u.degree, u.degree), frame='galactic')
    response = Ogle.query_region(coord=co)
    assert len(response) == 1


@pytest.mark.remote_data
def test_ogle_list():
    co = SkyCoord(0, 3, unit=(u.degree, u.degree), frame='galactic')
    co_list = [co, co, co]
    response = Ogle.query_region(coord=co_list)
    assert len(response) == 3
    assert response['RA[hr]'][0] == response['RA[hr]'][1] == response['RA[hr]'][2]


@pytest.mark.remote_data
def test_ogle_list_values():
    co_list = [[0, 0, 0], [3, 3, 3]]
    with pytest.warns(AstropyDeprecationWarning):
        response = Ogle.query_region(coord=co_list)
    assert len(response) == 3
    assert response['RA[hr]'][0] == response['RA[hr]'][1] == response['RA[hr]'][2]
