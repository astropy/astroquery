# Licensed under a 3-clause BSD style license - see LICENSE.rst


import pytest
import astropy.units as u

from .. import core


@pytest.mark.remote_data
class TestMiriadeClass:

    def test_ephemerides(self):
        # check values of Ceres for a given epoch
        # orbital uncertainty of Ceres is basically zero
        res = core.Miriade.get_ephemerides('Ceres', location='500',
                                           epoch=2451544.5)

        assert u.allclose(res["epoch"].quantity, [2451544.5] * u.d)

        # the orbit solution change with time, but anything within 10" is enough
        # for this test
        assert u.allclose((res['RA'].quantity, res['DEC'].quantity),
                         ([188.7032992], [9.0980213]) * u.deg,
                         atol=10 * u.arcsec)
    
