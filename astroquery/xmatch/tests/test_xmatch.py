import pytest
from astropy.units import arcsec

from ...xmatch import XMatch


def test_xmatch_query_invalid_max_distance():
    with pytest.raises(ValueError):
        XMatch().query('', '', 181 * arcsec)
