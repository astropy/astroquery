# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Test astroquery.noirlab, but monkeypatch any HTTP requests.
"""
import json
import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord
from ...utils.mocks import MockResponse
from ...exceptions import RemoteServiceError
from .. import NOIRLab
from . import expected as exp


def mock_content(method, url, **kwargs):
    if 'FORMAT=METADATA' in url:
        content = json.dumps(exp.service_metadata)
    elif '/sia/voimg' in url:
        raw_json = [{'HEADER': {'md5sum': 'str'}}] + [{'md5sum': m} for m in exp.query_region_1]
        content = json.dumps(raw_json)
    elif '/sia/vohdu' in url:
        raw_json = [{'HEADER': {'md5sum': 'str'}}] + [{'md5sum': m} for m in exp.query_region_2]
        content = json.dumps(raw_json)
    elif '/core_file_fields' in url:
        content = json.dumps(exp.core_file_fields)
    elif '/aux_file_fields' in url:
        content = json.dumps(exp.aux_file_fields)
    elif '/find/?rectype=file&limit=3' in url:
        content = json.dumps(exp.query_file_meta_raw)
    elif '/find/?rectype=file&limit=5' in url:
        content = json.dumps(exp.query_file_meta_raw_minimal)
    elif '/find/?rectype=hdu&limit=3' in url:
        content = json.dumps(exp.query_hdu_metadata_raw)
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
    return monkeypatch


@pytest.mark.parametrize('hdu', [(False,), (True,)])
def test_service_metadata(patch_request, hdu):
    """Test compliance with 6.1 of SIA spec v1.0.
    """
    actual = NOIRLab.service_metadata(hdu=hdu)
    assert actual[0] == exp.service_metadata[0]


@pytest.mark.parametrize('hdu,radius', [(False, '0.1'), (True, '0.07')])
def test_query_region(patch_request, hdu, radius):
    """Search a region.

    Ensure query gets at least the set of files we expect.
    It is OK if more files have been added to the remote Archive.
    """
    c = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')
    r = NOIRLab.query_region(c, radius=radius, hdu=hdu)
    actual = set(r['md5sum'].tolist())
    if hdu:
        expected = exp.query_region_2
    else:
        expected = exp.query_region_1
    assert expected.issubset(actual)


@pytest.mark.parametrize('hdu', [(False,), (True,)])
def test_core_fields(patch_request, hdu):
    """List the available CORE fields.
    """
    actual = NOIRLab.core_fields(hdu=hdu)
    if hdu:
        assert actual == exp.core_hdu_fields
    else:
        assert actual == exp.core_file_fields


@pytest.mark.parametrize('hdu', [(False,), (True,)])
def test_aux_fields(patch_request, hdu):
    """List the available AUX fields.
    """
    actual = NOIRLab.aux_fields('decam', 'instcal', hdu=hdu)
    if hdu:
        assert actual == exp.aux_hdu_fields
    else:
        assert actual == exp.aux_file_fields


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
    assert actual.pformat(max_width=-1) == exp.query_file_metadata


def test_query_file_metadata_minimal_input(patch_request):
    """Search FILE metadata with minimum input parameters.
    """
    actual = NOIRLab.query_metadata(qspec=None, limit=5)
    assert actual.pformat(max_width=-1) == exp.query_file_metadata_minimal


def test_query_hdu_metadata(patch_request):
    """Search HDU metadata.
    """
    qspec = {"outfields": ["md5sum",
                           "archive_filename",
                           "caldat",
                           "instrument",
                           "proc_type",
                           "EXPTIME",
                           "AIRMASS",
                           "hdu:EQUINOX"],
             "search": [["caldat", "2017-08-14", "2017-08-16"],
                        ["instrument", "decam"],
                        ["proc_type", "raw"]]}
    actual = NOIRLab.query_metadata(qspec, sort='md5sum', limit=3, hdu=True)
    assert actual.pformat(max_width=-1) == exp.query_hdu_metadata


def test_categoricals(patch_request):
    """List categories.
    """
    actual = NOIRLab.categoricals()
    assert actual == exp.categoricals


def test_version(patch_request):
    """Test the API version.
    """
    actual = NOIRLab._version()
    assert actual >= float(exp.version)


def test_api_version(patch_request):
    """Test the API version as a property.
    """
    actual = NOIRLab.api_version
    assert actual >= float(exp.version)


def test__validate_version(patch_request):
    """Check exception raised by outdated API version.
    """
    actual_api = NOIRLab.api_version
    NOIRLab._api_version = 9.8
    with pytest.raises(RemoteServiceError) as e:
        NOIRLab._validate_version()
    assert e.value.args[0] == ('The astroquery.noirlab module is expecting an older '
                               'version of the https://astroarchive.noirlab.edu API services. '
                               'Please upgrade to latest astroquery.  '
                               'Expected version 7.0 but got 9.8 from the API.')
    NOIRLab._api_version = actual_api


def test_get_token(patch_request):
    """Test token retrieval.
    """
    actual = NOIRLab.get_token('nobody@university.edu', '123456')
    assert actual == exp.get_token
