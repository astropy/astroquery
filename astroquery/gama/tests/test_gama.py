# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy.utils.data import get_pkg_data_filename
from astropy.table import Table
from ... import gama

import os.path

DATA_FILES = {"fits_data": "GAMA_HzVs28.fits",
              "html_page": "query_result.html",
              }


def data_path(filename):
    return get_pkg_data_filename(os.path.join('data', filename))


def test_GAMA_find_result():
    """Tests that the URL of the data is correctly found."""
    with open(data_path(DATA_FILES["html_page"])) as f_html:
        result_page = f_html.read()
    url = gama.core.find_data_url(result_page)
    expected_url = os.path.join("..", "tmp", DATA_FILES["fits_data"])
    assert os.path.abspath(url) == os.path.abspath(expected_url)


def test_GAMA_read_data():
    """Tests that the data fits file is successfully turned into a Table."""
    result = gama.core.get_gama_datafile(data_path(DATA_FILES["fits_data"]))
    assert isinstance(result, Table)
    assert len(result) > 0
