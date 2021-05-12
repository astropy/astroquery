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

    def test_observatories(self):
        # check values of IAU observatory codes

        obs = core.Miriade.get_observatory_codes()
        obs["sum"] = obs["sin"]**2 + obs["cos"]**2

        assert len(obs) == 2238
        assert obs["Code"][-1] == 'Z99'
        npt.assert_allclose(obs["sum"][obs["sum"] > 0], .995, rtol=1e-2)

    def test_observatories_restr(self):
        # check values of IAU observatory codes

        obs = core.Miriade.get_observatory_codes(restr='Greenwich')

        assert len(obs) == 1
        assert obs["Code"][0] == '000'
        assert obs["Name"][0] == 'Greenwich'
        npt.assert_allclose(obs["Long."], [0.])
