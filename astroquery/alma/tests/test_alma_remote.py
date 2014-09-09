# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import tempfile
import shutil
from astropy.tests.helper import pytest, remote_data
from .. import Alma
from ...exceptions import LoginError


@remote_data
class TestAlma:
    @pytest.fixture()
    def temp_dir(self, request):
        my_temp_dir = tempfile.mkdtemp()
        def fin():
            shutil.rmtree(my_temp_dir)
        request.addfinalizer(fin)
        return my_temp_dir

    def test_SgrAstar(self, temp_dir):
        alma = Alma()
        alma.cache_location = temp_dir

        result_s = alma.query_object('Sgr A*')
        assert '2011.0.00217.S' in result_s['Project_code']
        c = coordinates.SkyCoord(266.41681662, -29.00782497, frame='fk5')
        result_c = alma.query_region(c, 1*u.deg)
        assert '2011.0.00217.S' in result_c['Project_code']

    def test_stage_data(self, temp_dir):
        alma = Alma()
        alma.cache_location = temp_dir

        result_s = alma.query_object('Sgr A*')
        assert '2011.0.00217.S' in result_s['Project_code']

        uid = result_s['Asdm_uid'][0]

        alma.stage_data([uid])
