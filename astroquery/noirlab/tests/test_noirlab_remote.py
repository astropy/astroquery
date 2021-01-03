# Licensed under a 3-clause BSD style license - see LICENSE.rst
# Python library

# External packages
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.tests.helper import remote_data
# Local packages
from .. import Noirlab
from . import expected as expsia
# #!import pytest

# performs similar tests as test_module.py, but performs
# the actual HTTP request rather than monkeypatching them.
# should be disabled or enabled at will - use the
# remote_data decorator from astropy:


@remote_data
class TestNoirlabClass:

    def test_query_region_1(self):
        """Search FILES.
        Ensure query gets at least the set of files we expect.
        Its ok if more files have been added to the remote Archive."""

        c = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')
        r = Noirlab(which='file').query_region(c, radius='0.1')
        actual = set(list(r['md5sum']))
        expected = expsia.query_region_1
        assert expected.issubset(actual)

    def test_query_region_2(self):
        """Search HDUs.
        Ensure query gets at least the set of files we expect.
        Its ok if more files have been added to the remote Archive."""

        c = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')
        r = Noirlab(which='hdu').query_region(c, radius='0.07')
        actual = set(list(r['md5sum']))
        expected = expsia.query_region_2
        assert expected.issubset(actual)
