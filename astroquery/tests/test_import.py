# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

from distutils.version import LooseVersion

# first test occurs with astropy import locally
def test_monkeypatch_warning(recwarn):
    import astropy
    if LooseVersion(astropy.version.version) < LooseVersion('0.3.dev4957'):
        warnstr = "WARNING: You are using an 'old' version of astropy prior to the change that made all units singular.  astropy is being monkeypatched such that degrees and degree are both allow and hours and hour are both allowed.  This is NOT normal astropy behavior. [astroquery]"
        w = recwarn.pop()
        assert str(w.message) == warnstr

# now import astropy globally
import astropy

def test_monkeypatch_units():
    x = astropy.coordinates.angles.Angle("5 deg")
    if LooseVersion(astropy.version.version) < LooseVersion('0.3.dev4957'):
        assert x.degree == x.degrees
        assert x.hour == x.hours
