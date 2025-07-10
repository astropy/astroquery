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
from .. import NOIRLab, NOIRLabClass
from . import expected as exp


@pytest.mark.remote_data
def test_service_metadata():
    """Test compliance with 6.1 of SIA spec v1.0.
    """
    actual = NOIRLab().service_metadata()
    assert actual == exp.service_metadata[0]


@pytest.mark.skip(reason='old API')
@pytest.mark.remote_data
def test_query_region_0():
    """Search FILES.
    """
    c = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')
    r = NOIRLab().query_region(c, radius='0.1')
    actual = set(list(r['md5sum']))
    expected = exp.query_region_1
    assert expected.issubset(actual)


@pytest.mark.skip(reason='old API')
@pytest.mark.remote_data
def test_query_region_1():
    """Search FILES.

    Ensure query gets at least the set of files we expect.
    It is OK if more files have been added to the remote Archive.
    """
    c = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')
    r = NOIRLabClass().query_region(c, radius='0.1')
    actual = set(list(r['md5sum']))
    expected = exp.query_region_1
    assert expected.issubset(actual)


@pytest.mark.skip(reason='old API')
@pytest.mark.remote_data
def test_query_region_2():
    """Search HDUs.

    Ensure query gets at least the set of files we expect.
    Its ok if more files have been added to the remote Archive.
    """
    c = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')
    r = NOIRLabClass(hdu=True).query_region(c, radius='0.07')
    actual = set(list(r['md5sum']))
    expected = exp.query_region_2
    assert expected.issubset(actual)


@pytest.mark.remote_data
def test_core_file_fields():
    """List the available CORE FILE fields.
    """
    actual = NOIRLab().core_fields()
    assert actual[:5] == exp.core_file_fields


@pytest.mark.remote_data
def test_aux_file_fields():
    """List the available AUX FILE fields.
    """
    actual = NOIRLab().aux_fields('decam', 'instcal')
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
    qspec = {"outfields": ["md5sum",
                           "archive_filename",
                           "original_filename",
                           "instrument",
                           "proc_type"],
             "search": [['original_filename', 'c4d_', 'contains']]}
    actual = NOIRLab().query_metadata(qspec, limit=3)
    assert actual.pformat(max_width=-1) == exp.query_file_metadata


@pytest.mark.remote_data
def test_query_file_metadata_minimal_input():
    """Search FILE metadata with minimum input parameters.
    """
    actual = NOIRLab().query_metadata(qspec=None, limit=5)
    assert actual.pformat(max_width=-1) == exp.query_file_metadata_minimal


@pytest.mark.remote_data
def test_core_hdu_fields():
    """List the available CORE HDU fields.
    """
    actual = NOIRLabClass(hdu=True).core_fields()
    assert actual == exp.core_hdu_fields


@pytest.mark.remote_data
def test_aux_hdu_fields():
    """List the available AUX HDU fields.
    """
    actual = NOIRLabClass(hdu=True).aux_fields('decam', 'instcal')
    assert actual[:10] == exp.aux_hdu_fields


@pytest.mark.skip(reason='old API')
@pytest.mark.remote_data
def test_query_hdu_metadata_minimal_input():
    """Search HDU metadata with minimum input parameters.
    """
    actual = NOIRLabClass(hdu=True).query_metadata(qspec=None, limit=5)
    assert actual.pformat(max_width=-1) == exp.query_hdu_metadata_minimal


@pytest.mark.skip(reason='old API')
@pytest.mark.remote_data
def test_query_hdu_metadata():
    """Search HDU metadata.
    """
    qspec = {"outfields": ["fitsfile__archive_filename",
                           "fitsfile__caldat",
                           "fitsfile__instrument",
                           "fitsfile__proc_type",
                           "AIRMASS"],  # AUX field. Slows search
             "search": [["fitsfile__caldat", "2017-08-14", "2017-08-16"],
                        ["fitsfile__instrument", "decam"],
                        ["fitsfile__proc_type", "raw"]]}
    actual = NOIRLabClass(hdu=True).query_metadata(qspec, limit=3)
    assert actual.pformat(max_width=-1) == exp.query_hdu_metadata


@pytest.mark.remote_data
def test_retrieve():
    hdulist = NOIRLab().retrieve('f92541fdc566dfebac9e7d75e12b5601')
    for key in exp.retrieve:
        assert key in hdulist[0].header
        assert hdulist[0].header[key] == exp.retrieve[key]
    hdulist.close()


@pytest.mark.remote_data
def test_version():
    """Test the API version.
    """
    actual = NOIRLab().version()
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
