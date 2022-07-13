# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import shutil
import tempfile

from astroquery.mpc import MPC


@pytest.mark.remote_data
class TestRandomThings:

    @pytest.fixture()
    def temp_dir(self, request):
        my_temp_dir = tempfile.mkdtemp()

        def fin():
            shutil.rmtree(my_temp_dir)
        request.addfinalizer(fin)
        return my_temp_dir

    def test_quantity_hooks_cache(self, temp_dir):
        # Regression test for #2294
        mpc = MPC()
        mpc.cache_location = temp_dir
        mpc.get_observations(12893, cache=True)
        mpc.get_observations(12894, cache=True)
