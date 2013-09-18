from astropy.io import fits
from ... import gama

SQL_QUERY = "SELECT * FROM SpecAll LIMIT 5"
GAMA_URL = "http://www.gama-survey.org/"

def test_GAMA_query_sql_async():
    """Tests that a URL to the GAMA website is returned."""
    result = gama.core.GAMA.query_sql_async(SQL_QUERY)
    assert result.startswith(GAMA_URL)

def test_GAMA_query_sql():
    """Tests that a valid HDUList object is returned."""
    result = gama.core.GAMA.query_sql(SQL_QUERY)
    assert isinstance(result, fits.HDUList)

