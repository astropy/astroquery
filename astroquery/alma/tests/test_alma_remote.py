# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import tempfile
import shutil
import numpy as np
from astropy.tests.helper import pytest, remote_data
from astropy import coordinates
from astropy import units as u
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
        assert b'2011.0.00217.S' in result_s['Project_code']
        c = coordinates.SkyCoord(266.41681662*u.deg, -29.00782497*u.deg,
                                 frame='fk5')
        result_c = alma.query_region(c, 1*u.deg)
        assert b'2011.0.00217.S' in result_c['Project_code']

    def test_stage_data(self, temp_dir):
        alma = Alma()
        alma.cache_location = temp_dir

        result_s = alma.query_object('Sgr A*')
        assert b'2011.0.00217.S' in result_s['Project_code']

        uid = result_s['Asdm_uid'][0]

        alma.stage_data([uid])

    def test_doc_example(self, temp_dir):
        alma = Alma()
        alma.cache_location = temp_dir

        m83_data = alma.query_object('M83')
        assert m83_data.colnames == ['Project_code', 'Source_name', 'RA',
                                     'Dec', 'Band', 'Frequency_resolution',
                                     'Integration', 'Release_date',
                                     'Frequency_support',
                                     'Velocity_resolution', 'Pol_products',
                                     'Observation_date', 'PI_name', 'PWV',
                                     'Member_ous_id', 'Asdm_uid',
                                     'Project_title', 'Project_type',
                                     'Scan_intent']
        galactic_center = coordinates.SkyCoord(0*u.deg, 0*u.deg,
                                               frame='galactic')
        gc_data = alma.query_region(galactic_center, 1*u.deg)

        uids = np.unique(m83_data['Asdm_uid'])
        assert b'uid://A002/X3b3400/X90f' in uids

        link_list = alma.stage_data(uids[0:2])
        totalsize = alma.data_size(link_list)
        assert totalsize.to(u.GB).value > 1

    def test_query(self, temp_dir):
        alma = Alma()
        alma.cache_location = temp_dir

        result = alma.query(payload={'start_date-asu':'<11-11,2011'})
        assert len(result) == 621

    @pytest.mark.bigdata
    def test_cycle1(self):
        # About 500 MB
        alma = Alma()
        alma.cache_location = temp_dir

        target = 'NGC4945'
        project_code = '2012.1.00912.S'
        
        payload = {'project_code-asu':project_code,
                   'source_name-asu':target,}
        result = alma.query(payload=payload)
        assert len(result) == 1

        uid_url_table = alma.stage_data(result['Asdm_uid'], cache=False)
        assert len(uid_url_table) == 2

        data = alma.download_and_extract_files(uid_url_table['URL'])

        assert len(data) == 6

    def test_cycle0(self):
        # About 20 MB

        alma = Alma()
        alma.cache_location = temp_dir

        target = 'NGC4945'
        project_code = '2011.0.00121.S'
        
        payload = {'project_code-asu':project_code,
                   'source_name-asu':target,}
        result = alma.query(payload=payload)
        assert len(result) == 1

        uid_url_table = alma.stage_data(result['Asdm_uid'], cache=False)
        assert len(uid_url_table) == 2

        # The sizes are 4.9 and 0.016 GB respectively
        data = alma.download_and_extract_files(uid_url_table['URL'][1:])

        assert len(data) == 2
