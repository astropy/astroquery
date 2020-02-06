# Licensed under a 3-clause BSD style license - see LICENSE.rst
# Python library
from __future__ import print_function
# External packages
import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.tests.helper import remote_data
# Local packages
import astroquery.noao
from astroquery.noao.tests import expected

# performs similar tests as test_module.py, but performs
# the actual HTTP request rather than monkeypatching them.
# should be disabled or enabled at will - use the
# remote_data decorator from astropy:


#@remote_data
class TestNoaoClass(object):
    @classmethod
    def setup_class(cls):
        cls.arch = astroquery.noao.Noao


    def test_query_region_1(self):
        c = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')
        r = self.arch.query_region(c,radius='0.1')
        actual = r.pformat_all(max_lines=3)
        print(f'DBG: query_region_1; actual={actual}')
        assert actual == expected.query_region_1

