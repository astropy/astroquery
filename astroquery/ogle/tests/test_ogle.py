# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import ogle

import os
import pytest
from astropy.coordinates import SkyCoord
from astropy import units as u

from astroquery.utils.mocks import MockResponse


DATA_FILES = {'gal_0_3': 'gal_0_3.txt'}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_post(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(ogle.Ogle, '_request', post_mockreturn)
    return mp


def post_mockreturn(method, url, data, timeout, files=None, **kwargs):
    if files is not None:
        with open(data_path(DATA_FILES['gal_0_3']), 'rb') as infile:
            content = infile.read()
        response = MockResponse(content, **kwargs)
    else:
        raise ValueError("Unsupported post request.")
    return response


def test_ogle_single(patch_post):
    """
    Test a single pointing using an astropy coordinate instance
    """
    co = SkyCoord(0, 3, unit=(u.degree, u.degree), frame='galactic')
    ogle.core.Ogle.query_region(coord=co)


def test_ogle_list(patch_post):
    """
    Test multiple pointings using a list of astropy coordinate instances
    """
    co = SkyCoord(0, 3, unit=(u.degree, u.degree), frame='galactic')
    co_list = [co, co, co]
    ogle.core.Ogle.query_region(coord=co_list)


def test_ogle_single_payload():
    """
    Test single pointing payload
    """
    co = SkyCoord(0*u.deg, 3*u.deg, frame='galactic')
    payload = ogle.core.Ogle.query_region(coord=co, get_query_payload=True)
    fk5 = co.transform_to('fk5')
    ra = fk5.ra.hour
    dec = fk5.dec.degree
    assert len(payload) == 1
    expected_payload = f'# RD NG GOOD\n{ra} {dec}'
    assert payload['file1'] == expected_payload


def test_ogle_multipointing_payload():
    """
    Test payload of multiple pointings using a list of astropy coordinates
    """
    co1 = SkyCoord(0*u.deg, 3*u.deg, frame='galactic')
    co2 = SkyCoord(4*u.deg, 5*u.deg, frame='galactic')
    pointings = [co1, co2]
    payload = ogle.core.Ogle.query_region(
        coord=pointings,
        get_query_payload=True
    )
    conversions = []
    for co in pointings:
        fk5 = co.transform_to('fk5')
        ra_str = f"{fk5.ra.hour}"
        dec_str = f"{fk5.dec.degree}"
        conversions.append(f"{ra_str} {dec_str}")
    expected_payload = "# RD NG GOOD\n" + "\n".join(conversions)
    assert payload['file1'] == expected_payload
