# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Test astroquery.noirlab, but monkeypatch any HTTP requests.
"""
import json
import pytest
# from astropy import units as u
# from astropy.coordinates import SkyCoord
from ...utils.mocks import MockResponse
from .. import NOIRLab  # , NOIRLabClass
from . import expected as exp


def mock_content(method, url, **kwargs):
    if 'FORMAT=METADATA' in url:
        content = json.dumps(exp.service_metadata)
    elif '/core_file_fields' in url:
        content = json.dumps(exp.core_file_fields)
    elif '/aux_file_fields' in url:
        content = json.dumps(exp.aux_file_fields)
    elif '/cat_lists/' in url:
        content = json.dumps(exp.categoricals)
    elif '/version/' in url:
        content = exp.version
    elif '/get_token/' in url:
        content = f'"{exp.get_token}"'
    return MockResponse(content=content.encode('utf-8'), url=url)


@pytest.fixture
def patch_request(monkeypatch):
    monkeypatch.setattr(NOIRLab, '_request', mock_content)
    return monkeypatch


def test_service_metadata(patch_request):
    """Test compliance with 6.1 of SIA spec v1.0.
    """
    actual = NOIRLab.service_metadata()
    assert actual == exp.service_metadata[0]


def test_core_file_fields(patch_request):
    """List the available CORE FILE fields.
    """
    actual = NOIRLab.core_fields()
    assert actual == exp.core_file_fields


def test_aux_file_fields(patch_request):
    """List the available AUX FILE fields.
    """
    actual = NOIRLab.aux_fields('decam', 'instcal')
    assert actual == exp.aux_file_fields


def test_categoricals(patch_request):
    """List categories.
    """
    actual = NOIRLab.categoricals()
    assert actual == exp.categoricals


def test_version(patch_request):
    """Test the API version.
    """
    actual = NOIRLab.version()
    assert actual >= float(exp.version)


def test_api_version(patch_request):
    """Test the API version as a property.
    """
    actual = NOIRLab.api_version
    assert actual >= float(exp.version)


def test_get_token(patch_request):
    """Test token retrieval.
    """
    actual = NOIRLab.get_token('nobody@university.edu', '123456')
    assert actual == exp.get_token
