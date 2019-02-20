import pytest
import unittest
from astropy.tests.helper import remote_data
from astroquery.dace import Dace


@remote_data
class TestDaceClass(unittest.TestCase):

    def test_should_get_radial_velocities(self):
        radial_velocities = Dace.query_radial_velocities('HD40307')
        assert radial_velocities is not None
        assert 'rv' in radial_velocities.colnames


if __name__ == "__main__":
    unittest.main()
