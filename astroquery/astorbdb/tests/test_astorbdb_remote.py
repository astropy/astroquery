# Licensed under a 3-clause BSD style license - see LICENSE.rst


# performs similar tests as test_module.py, but performs
# the actual HTTP request rather than monkeypatching them.
# should be disabled or enabled at will - use the
# remote_data decorator from astropy:

import pytest
import astropy.units as u

from .. import AstInfo

@pytest.mark.remote_data
class TestAstInfoClass:

    def test_albedos(self):
        astinfo = AstInfo.albedos('656')
        assert astinfo[0]['albedo'] == 0.065

    def test_colors(self):
        astinfo = AstInfo.colors('656')
        assert astinfo[0]['color'] == 0.431

    def test_designations(self):
        astinfo = AstInfo.designations('656')
        assert astinfo['name'] == 'Beagle'

    def test_dynamical_family(self):
        astinfo = AstInfo.dynamical_family('656')
        assert astinfo[0]['family'] == 'Themis'

    def test_elements(self):
        astinfo = AstInfo.elements('656')
        assert astinfo['a'] == 3.156090767861024 * u.au

    def test_escape_routes(self):
        astinfo = AstInfo.escape_routes('3200')
        assert astinfo[0]['p_nu6_complex'] == 0.64189

    def test_lightcurves(self):
        astinfo = AstInfo.lightcurves('656')
        assert astinfo[0]['period'] == 7.035 * u.h

    def test_orbit(self):
        astinfo = AstInfo.orbit('656')
        assert astinfo['arc'] == 117.17 * u.yr

    def test_taxonomies(self):
        astinfo = AstInfo.taxonomies('656')
        assert astinfo[0]['taxonomy'] == 'C'

    def test_all_astinfo(self):
        astinfo = AstInfo.all_astinfo('656')
        assert astinfo['designations']['name'] == 'Beagle'
