# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest

import os

from ..core import HSAClass
from .test_hsa import TestHSA

class TestHSARemote(TestHSA):

    @pytest.mark.remote_data
    def test_download_data(self):
        obs_id = "1342195355"
        parameters = {'retrieval_type': "OBSERVATION",
                      'observation_id': obs_id,
                      'instrument_name': "PACS"}
        expected_res = obs_id + ".tar"
        hsa = HSAClass(self.get_dummy_tap_handler())
        res = hsa.download_data(**parameters)
        assert res == expected_res
        assert os.path.isfile(res)
        os.remove(res)

    @pytest.mark.remote_data
    def test_get_observation(self):
        obs_id = "1342195355"
        parameters = {'observation_id': obs_id,
                      'instrument_name': "PACS"}
        expected_res = obs_id + ".tar"
        hsa = HSAClass(self.get_dummy_tap_handler())
        res = hsa.get_observation(**parameters)
        assert res == expected_res
        assert os.path.isfile(res)
        os.remove(res)

    @pytest.mark.remote_data
    def test_get_postcard(self):
        obs_id = "1342195355"
        parameters = {'observation_id': obs_id,
                      'instrument_name': "PACS"}
        expected_res = obs_id + ".jpg"
        hsa = HSAClass(self.get_dummy_tap_handler())
        res = hsa.get_postcard(**parameters)
        assert res == expected_res
        assert os.path.isfile(res)
        os.remove(res)
