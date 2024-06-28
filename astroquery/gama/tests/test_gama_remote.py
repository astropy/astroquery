# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest
from astropy.table import Table
from ... import gama

SQL_QUERY = "SELECT * FROM SpecAll LIMIT 5"
GAMA_URL = "https://www.gama-survey.org/"


@pytest.mark.remote_data
def test_GAMA_query_sql_async():
    """Tests that a URL to the GAMA website is returned."""
    result = gama.core.GAMA.query_sql_async(SQL_QUERY)
    assert result.startswith(GAMA_URL)


@pytest.mark.remote_data
def test_GAMA_query_sql():
    """Tests that a valid HDUList object is returned."""
    result = gama.core.GAMA.query_sql(SQL_QUERY)
    assert isinstance(result, Table)
    assert len(result) > 0
