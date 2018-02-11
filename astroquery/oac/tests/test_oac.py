# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import pytest

import os
import requests

from numpy import testing as npt
from astropy.table import Table
import astropy.coordinates as coord
import astropy.units as u

from ...utils.testing_tools import MockResponse

from .. import OAC
from ...oac import conf

DATA_FILES = {'phot_csv': 'photometry_csv.txt',
              'phot_json': 'photometry_json.txt',
              'single_spec': 'single_spectrum_csv.txt',
              'multi_spec': 'spectra_json.txt'}

OAC_CLASS = OAC.core.OACClass()


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_get(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(OAC, '_request', get_mockreturn)
    return mp


def get_mockreturn(method, url, data, timeout, file=None, **kwargs):
    content = open(data_path(DATA_FILES[file]), 'r').read()
    response = MockResponse(content, **kwargs)
    return response


ra = 197.45037
dec = -23.38148
test_coords = coord.SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg))

test_radius = 10*u.arcsecond
test_width = 10*u.arcsecond
test_height = 10*u.arcsecond


def test_query_object_csv(patch_get):
    result = OAC_CLASS.query_object('GW170817')
    assert isinstance(result, Table)


def test_query_object_json(patch_get):
    result = OAC_CLASS.query_object('GW170817', data_format='json')
    assert isinstance(result, dict)


def test_query_rgion_cone_csv(patch_get):
    result = OAC_CLASS.query_region(coordinates=test_coords,
                                    radius=test_radius)
    assert isinstance(result, Table)


def test_query_rgion_cone_json(patch_get):
    result = OAC_CLASS.query_region(coordinates=test_coords,
                                    radius=test_radius,
                                    data_format='json')
    assert isinstance(result, dict)


def test_query_rgion_box_csv(patch_get):
    result = OAC_CLASS.query_region(coordinates=test_coords,
                                    width=test_width,
                                    height=test_height)
    assert isinstance(result, Table)


def test_query_rgion_box_json(patch_get):
    result = OAC_CLASS.query_region(coordinates=test_coords,
                                    width=test_width,
                                    height=test_height,
                                    data_format='json')
    assert isinstance(result, dict)


def test_get_photometry(patch_get):
    result = OAC_CLASS.get_photometry("GW170817")
    assert isinstance(result, Table)


def test_get_single_spectrum(patch_get):
    test_time = 56704
    result = OAC_CLASS.get_single_spectrum("SN2014J", time=test_time)
    assert isinstance(result, Table)


def test_get_spectra(patch_get):
    result = OAC_CLASS.get_spectra("SN1998bw")
    assert isinstance(result, dict)
