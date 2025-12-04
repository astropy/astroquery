# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Performs similar tests as test_noirlab.py, but performs
the actual HTTPS request rather than monkeypatching it.
Enable with *e.g.*::

    tox -e py310-test-online -- -P noirlab
"""
import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord
from .. import NOIRLab, conf
from . import expected as exp


@pytest.mark.remote_data
@pytest.mark.parametrize('hdu', [(False,), (True,)])
def test_service_metadata(hdu):
    """Test compliance with 6.1 of SIA spec v1.0.
    """
    actual = NOIRLab().service_metadata(hdu=hdu)
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
    actual = NOIRLab().core_fields(hdu=hdu)
    if hdu:
        assert actual == exp.core_hdu_fields
    else:
        assert actual[:5] == exp.core_file_fields


@pytest.mark.remote_data
@pytest.mark.parametrize('hdu', [(False,), (True,)])
def test_aux_fields(hdu):
    """List the available AUX fields.
    """
    actual = NOIRLab().aux_fields('decam', 'instcal', hdu=hdu)
    if hdu:
        assert actual[:10] == exp.aux_hdu_fields
    else:
        assert actual[:10] == exp.aux_file_fields


@pytest.mark.remote_data
def test_categoricals():
    """List categories.
    """
    actual = NOIRLab().categoricals()
    assert actual == exp.categoricals


@pytest.mark.remote_data
def test_query_file_metadata():
    """Search FILE metadata.
    """
    conf.timeout = 300
    qspec = {"outfields": ["md5sum",
                           "archive_filename",
                           "original_filename",
                           "instrument",
                           "proc_type"],
             "search": [['original_filename', 'c4d_', 'contains']]}
    actual = NOIRLab().query_metadata(qspec, sort='md5sum', limit=3)
    assert actual.pformat(max_width=-1) == exp.query_file_metadata


@pytest.mark.remote_data
def test_query_file_metadata_minimal_input():
    """Search FILE metadata with minimum input parameters.
    """
    conf.timeout = 300
    actual = NOIRLab().query_metadata(qspec=None, sort='md5sum', limit=5)
    assert actual.pformat(max_width=-1) == exp.query_file_metadata_minimal


@pytest.mark.remote_data
def test_query_hdu_metadata():
    """Search HDU metadata.
    """
    conf.timeout = 300
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
    actual = NOIRLab().query_metadata(qspec, sort='md5sum', limit=3, hdu=True)
    assert actual.pformat(max_width=-1) == exp.query_hdu_metadata


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
