# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Test astroquery.noirlab, but monkeypatch any HTTP requests.
"""
import json
import pytest
# from astropy import units as u
# from astropy.coordinates import SkyCoord
from ...utils.mocks import MockResponse
from .. import NOIRLab, NOIRLabClass
from . import expected as exp


NOIRLabHDU = NOIRLabClass(hdu=True)


def mock_content(method, url, **kwargs):
    if 'FORMAT=METADATA' in url:
        content = json.dumps(exp.service_metadata)
    elif '/core_file_fields' in url:
        content = json.dumps(exp.core_file_fields)
    elif '/aux_file_fields' in url:
        content = json.dumps(exp.aux_file_fields)
    elif '/find?rectype=file' in url:
        content = json.dumps(exp.query_file_metadata)
    elif '/core_hdu_fields' in url:
        content = json.dumps(exp.core_hdu_fields)
    elif '/aux_hdu_fields' in url:
        content = json.dumps(exp.aux_hdu_fields)
    elif '/find?rectype=hdu' in url:
        content = json.dumps(exp.query_hdu_metadata)
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
    monkeypatch.setattr(NOIRLabHDU, '_request', mock_content)
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


@pytest.mark.skip(reason='WIP')
def test_query_file_metadata(patch_request):
    """Search FILE metadata.
    """
    qspec = {"outfields": ["md5sum",
                           "archive_filename",
                           "original_filename",
                           "instrument",
                           "proc_type"],
             "search": [['original_filename', 'c4d_', 'contains']]}
    actual = NOIRLab.query_metadata(qspec, limit=3)
    assert actual.pformat_all() == exp.query_file_metadata


def test_core_hdu_fields(patch_request):
    """List the available CORE HDU fields.
    """
    actual = NOIRLabHDU.core_fields()
    assert actual == exp.core_hdu_fields


def test_aux_hdu_fields(patch_request):
    """List the available AUX HDU fields.
    """
    actual = NOIRLabHDU.aux_fields('decam', 'instcal')
    assert actual == exp.aux_hdu_fields


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
