# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Shared pytest fixtures for LAMOST tests.

This module provides common fixtures for mocking HTTP requests, config files,
and test data files used across all LAMOST test modules.
"""

import pytest
from pathlib import Path
from io import BytesIO

from astropy.io import fits
import numpy as np

from unittest.mock import Mock

from .. import conf
from ..core import Lamost, LamostClass
from .helpers import set_mock_home, LAMOST_TOKEN_ENV_VARS


@pytest.fixture(autouse=True)
def isolate_lamost_defaults(monkeypatch, tmp_path, request):
    if request.node.get_closest_marker('remote_data') is not None:
        yield
        return
    if "mock_home_dir" not in request.fixturenames and "temp_config_file" not in request.fixturenames:
        set_mock_home(monkeypatch, tmp_path)
    for env_name in LAMOST_TOKEN_ENV_VARS:
        monkeypatch.delenv(env_name, raising=False)
    # The module-level instance was configured at import time, possibly from
    # a developer's astroquery.cfg; conf.set_temp below does not update it.
    monkeypatch.setattr(Lamost, 'token', None)
    monkeypatch.setattr(Lamost, 'URL', 'https://www.lamost.org/openapi')
    monkeypatch.setattr(Lamost, 'TIMEOUT', 60)
    monkeypatch.setattr(Lamost, 'data_release', 'dr10')
    monkeypatch.setattr(Lamost, 'sub_version', 'v2.0')
    monkeypatch.setattr(
        LamostClass, '_request',
        Mock(side_effect=AssertionError('Unexpected HTTP request in an offline test.')),
    )

    with (
        conf.set_temp('token', ''),
        conf.set_temp('server', 'https://www.lamost.org/openapi'),
        conf.set_temp('timeout', 60),
        conf.set_temp('data_release', 'dr10'),
        conf.set_temp('sub_version', 'v2.0'),
    ):
        yield


@pytest.fixture
def mock_home_dir(tmp_path, monkeypatch):
    """
    Mock home directory for config file testing.

    Creates a temporary directory and sets it as the home directory in the
    environment variables used by POSIX and Windows.
    This allows testing of config file loading without affecting the user's actual home.

    Returns
    -------
    Path
        Path to the temporary home directory.
    """
    set_mock_home(monkeypatch, tmp_path)
    return tmp_path


@pytest.fixture
def temp_config_file(mock_home_dir):
    """
    Provide a temporary config file path for testing.

    The file doesn't exist by default - tests should create it as needed.

    Returns
    -------
    Path
        Path to pylamost.ini in the mocked home directory.
    """
    return mock_home_dir / 'pylamost.ini'


@pytest.fixture
def sample_lrs_fits():
    """
    Return path to a real low-resolution spectrum FITS file for testing.

    Returns
    -------
    str
        Absolute path to the LRS FITS file.
    """
    test_dir = Path(__file__).parent
    fits_file = test_dir / 'data' / 'spec-57278-EG224429N215706B01_sp01-001.fits.gz'

    if not fits_file.exists():
        pytest.fail(f"Required test FITS file is missing: {fits_file}")

    return str(fits_file)


@pytest.fixture
def sample_mrs_fits(tmp_path):
    """
    Create a synthetic medium-resolution spectrum FITS file for testing.

    Exercise lowercase column names and simple B/R extension names independently
    of the historical and modern archive excerpts.

    Returns
    -------
    str
        Path to the created MRS FITS file.
    """
    # Create primary HDU
    primary = fits.PrimaryHDU()

    # Create multiple extensions for different bands
    bands = ['B', 'R']
    hdu_list = [primary]

    for band in bands:
        # Create synthetic spectrum data
        n_pixels = 32
        wavelength = np.linspace(5000, 6000, n_pixels) if band == 'B' else np.linspace(6000, 7000, n_pixels)
        flux = np.arange(n_pixels, dtype=np.float32) + (1 if band == 'B' else 2)
        ivar = np.ones(n_pixels, dtype=np.float32)

        # Create structured array matching LAMOST MRS format
        data = np.array(
            [(flux, ivar, wavelength)],
            dtype=[('flux', 'f4', n_pixels), ('ivar', 'f4', n_pixels), ('wavelength', 'f8', n_pixels)]
        )

        # Create binary table HDU
        hdu = fits.BinTableHDU(data=data, name=band)
        hdu_list.append(hdu)

    # Write to file
    fits_path = tmp_path / 'test_mrs_spectrum.fits'
    hdul = fits.HDUList(hdu_list)
    hdul.writeto(fits_path, overwrite=True)
    hdul.close()

    return str(fits_path)


@pytest.fixture
def mock_votable_response():
    """
    Return mock VOTable XML response data.

    Returns
    -------
    bytes
        VOTable XML content as bytes.
    """
    votable_xml = b"""<?xml version="1.0"?>
<VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
  <RESOURCE type="results">
    <TABLE>
      <FIELD name="obsid" datatype="char" arraysize="*"/>
      <FIELD name="ra" datatype="double" unit="deg"/>
      <FIELD name="dec" datatype="double" unit="deg"/>
      <FIELD name="teff" datatype="float"/>
      <DATA>
        <TABLEDATA>
          <TR><TD>101001</TD><TD>10.0</TD><TD>40.0</TD><TD>5500.0</TD></TR>
          <TR><TD>101002</TD><TD>10.1</TD><TD>40.1</TD><TD>5600.0</TD></TR>
          <TR><TD>101003</TD><TD>10.2</TD><TD>40.2</TD><TD>5700.0</TD></TR>
        </TABLEDATA>
      </DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>"""
    return votable_xml


@pytest.fixture
def mock_json_response():
    """
    Return mock JSON response data.

    Returns
    -------
    dict
        JSON response as Python dict.
    """
    return [
        {'obsid': '101001', 'ra': 10.0, 'dec': 40.0, 'teff': 5500.0},
        {'obsid': '101002', 'ra': 10.1, 'dec': 40.1, 'teff': 5600.0},
        {'obsid': '101003', 'ra': 10.2, 'dec': 40.2, 'teff': 5700.0}
    ]


@pytest.fixture
def mock_csv_response():
    """
    Return mock CSV response data.

    Returns
    -------
    str
        CSV content as string.
    """
    return """obsid,ra,dec,teff
101001,10.0,40.0,5500.0
101002,10.1,40.1,5600.0
101003,10.2,40.2,5700.0"""


@pytest.fixture
def mock_dr_versions_response():
    """
    Return mock data release versions response.

    Returns
    -------
    dict
        DR versions response structure.
    """
    return {
        'versions': [
            {
                'dr_version': 'dr10',
                'sub_version': 'v2.0',
                'public_status': 'public',
                'has_mrs': True,
                'base_url': 'https://www.lamost.org/openapi/dr10/v2.0'
            },
            {
                'dr_version': 'dr10',
                'sub_version': 'v1.0',
                'public_status': 'public',
                'has_mrs': False,
                'base_url': 'https://www.lamost.org/openapi/dr10/v1.0'
            },
            {
                'dr_version': 'dr11',
                'sub_version': 'v1.0',
                'public_status': 'internal',
                'has_mrs': True,
                'base_url': 'https://www.lamost.org/openapi/dr11/v1.0'
            }
        ]
    }


@pytest.fixture
def mock_fits_content():
    """
    Return mock FITS file binary content.

    Returns
    -------
    bytes
        Minimal FITS file binary data.
    """
    # Create minimal FITS file in memory
    hdu = fits.PrimaryHDU(data=np.array([[1, 2], [3, 4]]))
    bio = BytesIO()
    hdu.writeto(bio)
    bio.seek(0)
    return bio.read()


@pytest.fixture
def patch_request(monkeypatch):
    """Set a response and return a spy for checking the actual request."""
    def setup_mock(response):
        request = Mock(return_value=response)
        monkeypatch.setattr(LamostClass, '_request', request)
        return request
    return setup_mock


@pytest.fixture
def spectral_schema(monkeypatch):
    """Supply types for payload tests that now compile SQL from metadata."""
    schema = {name: {'datatype': 'double'} for name in
              ('ra', 'dec', 'snrg', 'snr', 'teff', 'logg', 'feh', 'teff_lasp', 'logg_lasp', 'feh_lasp')}
    schema['obsid'] = {'datatype': 'long'}
    monkeypatch.setattr(LamostClass, 'get_tables_metadata',
                        lambda self, **kwargs: {'tables': {
                            'combined': {'columns': schema}, 'med_combined': {'columns': schema}}})
    return schema
