# Python library
from unittest import TestCase
# External packages
from astropy import units as u
from astropy.coordinates import SkyCoord
# Local packages
import astroquery.noao
import astroquery.noao.tests.expected


class NoaoSia(TestCase):
    def setUp(self):
        self.arch = astroquery.noao.Noao

    def query_region_1(self):
        c = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')
        r = self.arch.query_region(c,radius='0.1')
        actual = r.pformat_all(max_lines=5)
        self.assertEqual(actual, expected.query_region_1)
        


if __name__ == '__main__':
    unittest.main()
