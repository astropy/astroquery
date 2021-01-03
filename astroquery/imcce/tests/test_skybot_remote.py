# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest

import astropy.units as u

from .. import Skybot


@pytest.mark.remote_data
class TestSBDBClass:

    def general_query(self):
        a = Skybot.cone_search((0, 0), 0.5, 2451200)
        assert(len(a) >= 141)

    def failed_query(self):
        with pytest.raises(RuntimeError):
            Skybot.cone_search((0, 90), 0.00000001, 2451200)

    def planet_moons(self):
        a = Skybot.cone_search((221.48552, -14.82952), 0.1,
                               2458291.893831018, location='688')
        assert('Jupiter' in a['Name'])
        assert('Ganymed' in a['Name'])
        assert(len(a) > 4)

        b = Skybot.cone_search((221.48552, -14.82952), 0.1,
                               2458291.893831018, location='688',
                               find_asteroids=False)
        assert(len(b) == 4)

    def test_uncertainty_filter(self):
        a = Skybot.cone_search((0, 0), 0.3,
                               2458291.893831018, location='G37',
                               position_error=0.1)
        assert(max(a['posunc'] < 0.1*u.arcsec))
