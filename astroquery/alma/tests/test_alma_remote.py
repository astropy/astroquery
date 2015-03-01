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
        alma2 = Alma()
        alma2.cache_location = temp_dir
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
        X90f = (m83_data['Asdm_uid'] == b'uid://A002/X3b3400/X90f')
        assert X90f.sum() == 45
        X31 = (m83_data['Member_ous_id'] == b'uid://A002/X3216af/X31')
        assert X31.sum() == 225

        link_list_asdm = alma.stage_data('uid://A002/X3b3400/X90f')
        totalsize_asdm = link_list_asdm['size'].sum() * u.Unit(link_list_asdm['size'].unit)
        assert (totalsize_asdm.to(u.B).value == -1.0)

        link_list_mous = alma2.stage_data('uid://A002/X3216af/X31')
        totalsize_mous = link_list_mous['size'].sum() * u.Unit(link_list_mous['size'].unit)
        # More recent ALMA request responses do not include any information
        # about file size, so we have to allow for the possibility that all
        # file sizes are replaced with -1
        assert (totalsize_mous.to(u.GB).value > 159)

    def test_query(self, temp_dir):
        alma = Alma()
        alma.cache_location = temp_dir

        result = alma.query(payload={'start_date-asu':'<11-11-2011'})
        assert len(result) == 621

    @pytest.mark.bigdata
    def test_cycle1(self, temp_dir):
        # About 500 MB
        alma = Alma()
        alma.cache_location = temp_dir

        target = 'NGC4945'
        project_code = '2012.1.00912.S'
        
        payload = {'project_code-asu':project_code,
                   'source_name-asu':target,}
        result = alma.query(payload=payload)
        assert len(result) == 1

        # Need new Alma() instances each time
        uid_url_table_mous = alma().stage_data(result['Member_ous_id'])
        uid_url_table_asdm = alma().stage_data(result['Asdm_uid'])
        # I believe the fixes as part of #495 have resulted in removal of a
        # redundancy in the table creation, so a 1-row table is OK here.
        # A 2-row table may not be OK any more, but that's what it used to
        # be...
        assert len(uid_url_table_asdm) == 1
        assert len(uid_url_table_mous) == 2

        urls_to_download = uid_url_table_mous['URL'][uid_url_table_mous['size'] < 1]
        data = alma.download_and_extract_files(urls_to_download)

        assert len(data) == 6

    def test_cycle0(self, temp_dir):
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

    def test_help(self):
        
        help_list = Alma._get_help_page()
        assert help_list[0][0] == u'Position'
        assert help_list[1][0] == u'Energy'
        assert help_list[1][1][0] == (u'Frequency', 'energy.frequency-asu')
