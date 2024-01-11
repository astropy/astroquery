import pytest

from astropy.table import Table

from astroquery.ipac.irsa import sha
from astroquery.exceptions import NoResultsWarning

pytest.skip(allow_module_level=True,
            reason="Skip tests in this file until as the upstream API has changed and is scheduled to be removed."
            "https://github.com/astropy/astroquery/issues/2834")


@pytest.mark.remote_data
def test_query_no_results():
    # Test for issue #1836
    with pytest.warns(NoResultsWarning):
        result = sha.query(ra=219.57741, dec=64.171525, size=0.001)

    assert isinstance(result, Table)
    assert len(result) == 0
