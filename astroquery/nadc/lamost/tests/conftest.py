# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Shared pytest fixtures for LAMOST tests.

This module provides common fixtures for mocking HTTP requests, config files,
and test data files used across all LAMOST test modules.
"""

import pytest
import os
import tempfile
from pathlib import Path
from io import BytesIO

from astropy.io import fits
import numpy as np

from .helpers import LAMOST_TOKEN_ENV_VARS, _home_env_values, set_mock_home


_IMPORT_HOME = tempfile.TemporaryDirectory(prefix='astroquery-lamost-home-')
os.environ.update(_home_env_values(_IMPORT_HOME.name))
_IMPORT_TOKEN_ENV_VALUES = {
    _env_name: os.environ[_env_name]
    for _env_name in LAMOST_TOKEN_ENV_VARS
    if _env_name in os.environ
}
for _env_name in LAMOST_TOKEN_ENV_VARS:
    os.environ.pop(_env_name, None)
try:
    # Keep the LAMOST singleton isolated from user credentials at import time
    # without permanently mutating the pytest process environment.
    from .. import core as _lamost_core  # noqa: F401
finally:
    os.environ.update(_IMPORT_TOKEN_ENV_VALUES)


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
        pytest.skip(f"Test FITS file not found: {fits_file}")

    return str(fits_file)


@pytest.fixture
def sample_mrs_fits(tmp_path):
    """
    Create a synthetic medium-resolution spectrum FITS file for testing.

    Since we don't have a real MRS file, this creates a minimal valid MRS FITS
    structure with multiple extensions.

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
        n_pixels = 2048
        wavelength = np.linspace(5000, 6000, n_pixels) if band == 'B' else np.linspace(6000, 7000, n_pixels)
        flux = np.random.rand(n_pixels).astype(np.float32) * 100
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
def mock_pagination_count():
    """
    Return mock pagination count response.

    Returns
    -------
    int
        Total count of query results.
    """
    return 25000


@pytest.fixture
def mock_pagination_page():
    """
    Return mock pagination page response.

    Returns
    -------
    list
        List of result dictionaries for one page.
    """
    # Create a page with 100 results
    return [
        {'obsid': f'10{i:04d}', 'ra': 10.0 + i*0.01, 'dec': 40.0 + i*0.01}
        for i in range(100)
    ]


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
def mock_png_content():
    """
    Return mock PNG image binary content.

    Returns
    -------
    bytes
        Minimal PNG file binary data (1x1 pixel black PNG).
    """
    # Minimal 1x1 black PNG
    png_data = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
        b'\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4'
        b'\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return png_data


@pytest.fixture
def patch_request(monkeypatch):
    """
    Fixture to patch the _request method for testing without actual HTTP calls.

    This fixture returns a function that can be called to set up specific
    mock responses for tests.

    Returns
    -------
    callable
        Function to set up mock responses: patch_request(response)

    Examples
    --------
    def test_example(patch_request):
        # Set up mock response
        mock_resp = create_mock_response(json_data={'result': 'success'})
        patch_request(mock_resp)

        # Now any _request calls will return mock_resp
        lamost = LamostClass()
        result = lamost.some_method()
    """
    from ..core import LamostClass

    def setup_mock(response):
        """Set up the mock _request to return the given response."""
        def mock_request(self, method, url, **kwargs):
            return response
        monkeypatch.setattr(LamostClass, '_request', mock_request)

    return setup_mock
