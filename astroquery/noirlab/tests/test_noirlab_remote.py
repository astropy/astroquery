# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Performs similar tests as test_noirlab.py, but performs
the actual HTTPS request rather than monkeypatching it.
Enable with *e.g.*::

    tox -e py310-test-online -- -P noirlab
"""
import re
import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord
from .. import NOIRLab, conf
from . import expected as exp


md5sum_string = re.compile(r'[0-9a-f]+')


@pytest.mark.remote_data
@pytest.mark.parametrize('hdu', [(False,), (True,)])
def test_service_metadata(hdu):
    """Test compliance with 6.1 of SIA spec v1.0.
    """
    actual = NOIRLab()._service_metadata(hdu=hdu)
    assert actual[0] == exp.service_metadata[0]


@pytest.mark.remote_data
@pytest.mark.parametrize('hdu,radius', [(False, '0.1'), (True, '0.07')])
def test_query_region(hdu, radius):
    """Search a region.

    Ensure query gets at least the set of files we expect.
    It is OK if more files have been added to the remote Archive.
    """
    conf.timeout = 300
    c = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')
    r = NOIRLab().query_region(c, radius=radius, hdu=hdu)
    actual = set(r['md5sum'].tolist())
    if hdu:
        expected = exp.query_region_2
    else:
        expected = exp.query_region_1
    assert expected.issubset(actual)


@pytest.mark.remote_data
@pytest.mark.parametrize('hdu', [(False,), (True,)])
def test_core_fields(hdu):
    """List the available CORE fields.
    """
    actual = NOIRLab().list_fields(hdu=hdu)
    if hdu:
        assert actual == exp.core_hdu_fields
    else:
        assert actual[:5] == exp.core_file_fields


@pytest.mark.remote_data
@pytest.mark.parametrize('hdu', [(False,), (True,)])
def test_aux_fields(hdu):
    """List the available AUX fields.
    """
    actual = NOIRLab().list_fields(aux=True, instrument='decam',
                                   proctype='instcal', hdu=hdu)
    if hdu:
        assert actual[:10] == exp.aux_hdu_fields
    else:
        assert actual[:10] == exp.aux_file_fields


@pytest.mark.remote_data
def test_categoricals():
    """List categories.
    """
    actual = NOIRLab().list_fields(categorical=True)
    assert actual == exp.categoricals


@pytest.mark.remote_data
def test_query_file_metadata():
    """Search FILE metadata.

    Both the column ordering and the actual returned results may vary,
    so just check that the response "looks like" the expected data.
    """
    conf.timeout = 300
    qspec = {"outfields": ["md5sum",
                           "archive_filename",
                           "original_filename",
                           "instrument",
                           "proc_type"],
             "search": [['original_filename', 'c4d_', 'contains']]}
    actual = NOIRLab().query_metadata(qspec, sort='md5sum', limit=3)
    actual_formatted = actual.pformat(max_width=-1)
    for f in qspec['outfields']:
        assert f in actual_formatted[0]
    assert md5sum_string.match(actual['md5sum'][2]) is not None
    assert actual['instrument'][0] == 'decam'


@pytest.mark.remote_data
def test_query_file_metadata_minimal_input():
    """Search FILE metadata with minimum input parameters.

    Actual returned results may vary, so just check that the response
    "looks like" the expected data.
    """
    conf.timeout = 300
    actual = NOIRLab().query_metadata(qspec=None, sort='md5sum', limit=5)
    actual_formatted = actual.pformat(max_width=-1)
    assert actual_formatted[0] == exp.query_file_metadata_minimal[0]
    assert md5sum_string.match(actual_formatted[6]) is not None


@pytest.mark.remote_data
def test_query_hdu_metadata():
    """Search HDU metadata.

    Both the column ordering and the actual returned results may vary,
    so just check that the response "looks like" the expected data.
    """
    conf.timeout = 300
    qspec = {"outfields": ["md5sum",
                           "archive_filename",
                           "caldat",
                           "instrument",
                           "proc_type",
                           "EXPTIME",
                           "AIRMASS",
                           "hdu:CD1_1",
                           "hdu:CD1_2"],
             "search": [["caldat", "2017-08-14", "2017-08-16"],
                        ["instrument", "decam"],
                        ["proc_type", "raw"]]}
    actual = NOIRLab().query_metadata(qspec, sort='md5sum', limit=3, hdu=True)
    actual_formatted = actual.pformat(max_width=-1)
    for f in qspec['outfields']:
        if 'hdu:' in f:
            assert f.split(':')[1] in actual_formatted[0]
        else:
            assert f in actual_formatted[0]
    assert md5sum_string.match(actual['md5sum'][2]) is not None
    assert actual['caldat'][0] == '2017-08-15'


@pytest.mark.remote_data
def test_get_file():
    hdulist = NOIRLab().get_file('f92541fdc566dfebac9e7d75e12b5601')
    for key in exp.get_file:
        assert key in hdulist[0].header
        assert hdulist[0].header[key] == exp.get_file[key]
    hdulist.close()


@pytest.mark.remote_data
def test_version():
    """Test the API version.
    """
    actual = NOIRLab()._version()
    assert actual >= float(exp.version)


@pytest.mark.remote_data
def test_api_version():
    """Test the API version as a property.
    """
    actual = NOIRLab().api_version
    assert actual >= float(exp.version)


@pytest.mark.remote_data
def test_get_token():
    """Test token retrieval.
    """
    actual = NOIRLab().get_token('nobody@university.edu', '123456')
    assert actual.split('.')[0] == exp.get_token
