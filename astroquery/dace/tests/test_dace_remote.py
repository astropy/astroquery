import unittest
from astropy.tests.helper import remote_data
from astroquery.dace import Dace


@remote_data
class TestDaceClass(unittest.TestCase):

    def test_should_get_radial_velocities(self):
        radial_velocities_table = Dace.query_radial_velocities('HD40307')
        assert radial_velocities_table is not None and 'rv' in radial_velocities_table.colnames

if __name__ == "__main__":
    unittest.main()
