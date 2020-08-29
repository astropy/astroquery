# Licensed under a 3-clause BSD style license - see LICENSE.rst


import numpy.testing as npt
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

        # check table columns
        cols = (('target', None),
                ('epoch', u.d),
                ('RA', u.deg),
                ('DEC', u.deg),
                ('delta', u.au),
                ('V', u.mag),
                ('alpha', u.deg),
                ('elong', u.deg),
                ('RAcosD_rate', u.arcsec/u.minute),
                ('DEC_rate', u.arcsec/u.minute),
                ('delta_rate', u.km/u.s))

        for i in cols:
            assert i[0] in res.columns
            assert res[i[0]].unit == i[1]

        assert res['target'] == "Ceres"

        npt.assert_allclose(
            [2451544.5, 188.70280, 9.09829],
            list(res['epoch', 'RA', 'DEC'][0]),
            rtol=1e-5)
