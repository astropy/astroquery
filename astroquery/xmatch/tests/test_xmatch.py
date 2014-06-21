import pytest
from astropy.units import arcsec

from ...xmatch import XMatch


def test_xmatch_query_invalid_max_distance():
    with pytest.raises(ValueError) as ex:
        XMatch().query('', '', 181 * arcsec)
        assert str(ex.value) == (
            'max_distance argument must not be greater than 180')
