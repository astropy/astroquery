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
        assert b'2011.0.00217.S' in result_s['Project code']
        c = coordinates.SkyCoord(266.41681662*u.deg, -29.00782497*u.deg,
                                 frame='fk5')
        result_c = alma.query_region(c, 1*u.deg)
        assert b'2011.0.00217.S' in result_c['Project code']

    def test_stage_data(self, temp_dir):
        alma = Alma()
        alma.cache_location = temp_dir

        result_s = alma.query_object('Sgr A*')
        assert b'2011.0.00217.S' in result_s['Project code']
        uid = result_s['Asdm uid'][0]

        alma.stage_data([uid])

    def test_doc_example(self, temp_dir):
        alma = Alma()
        alma.cache_location = temp_dir
        alma2 = Alma()
        alma2.cache_location = temp_dir
        m83_data = alma.query_object('M83')
        assert m83_data.colnames == ['Project code', 'Source name', 'RA',
                                     'Dec', 'Band', 'Frequency resolution',
                                     'Integration', 'Release date',
                                     'Frequency support',
                                     'Velocity resolution', 'Pol products',
                                     'Observation date', 'PI name', 'PWV',
                                     'Member ous id', 'Asdm uid',
                                     'Project title', 'Project type',
                                     'Scan intent']
        galactic_center = coordinates.SkyCoord(0*u.deg, 0*u.deg,
                                               frame='galactic')
        gc_data = alma.query_region(galactic_center, 1*u.deg)

        uids = np.unique(m83_data['Asdm uid'])
        assert b'uid://A002/X3b3400/X90f' in uids
        X90f = (m83_data['Asdm uid'] == b'uid://A002/X3b3400/X90f')
        assert X90f.sum() == 45
        X31 = (m83_data['Member ous id'] == b'uid://A002/X3216af/X31')
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

        result = alma.query(payload={'start_date':'<11-11-2011'})
        assert len(result) == 621

    @pytest.mark.bigdata
    def test_cycle1(self, temp_dir):
        # About 500 MB
        alma = Alma()
        alma.cache_location = temp_dir

        target = 'NGC4945'
        project_code = '2012.1.00912.S'
        
        payload = {'project_code':project_code,
                   'source_name_alma':target,}
        result = alma.query(payload=payload)
        assert len(result) == 1

        # Need new Alma() instances each time
        uid_url_table_mous = alma().stage_data(result['Member ous id'])
        uid_url_table_asdm = alma().stage_data(result['Asdm uid'])
        # I believe the fixes as part of #495 have resulted in removal of a
        # redundancy in the table creation, so a 1-row table is OK here.
        # A 2-row table may not be OK any more, but that's what it used to
        # be...
        assert len(uid_url_table_asdm) == 1
        assert len(uid_url_table_mous) == 2

        small = uid_url_table_mous['size'] < 1

        urls_to_download = uid_url_table_mous[small]['URL']
        # THIS IS FAIL
        assert uid_url_table_mous['URL'][0].split("/")[-1] == uid_url_table_mous['uid'][0]
        data = alma.download_and_extract_files(urls_to_download)

        assert len(data) == 6

    def test_cycle0(self, temp_dir):
        # About 20 MB

        alma = Alma()
        alma.cache_location = temp_dir

        target = 'NGC4945'
        project_code = '2011.0.00121.S'
        
        payload = {'project_code':project_code,
                   'source_name_alma':target,}
        result = alma.query(payload=payload)
        assert len(result) == 1

        alma1 = alma()
        alma2 = alma()
        uid_url_table_mous = alma1.stage_data(result['Member ous id'])
        uid_url_table_asdm = alma2.stage_data(result['Asdm uid'])
        assert len(uid_url_table_asdm) == 1
        assert len(uid_url_table_mous) == 32

        assert uid_url_table_mous[0]['URL'].split("/")[-1] == '2011.0.00121.S_2012-08-16_001_of_002.tar'
        assert uid_url_table_mous[0]['uid'] == 'uid://A002/X327408/X246'

        small = uid_url_table_mous['size'] < 1

        urls_to_download = uid_url_table_mous[small]['URL']
        data = alma.download_and_extract_files(urls_to_download)

        # There are 10 small files, but only 8 unique
        assert len(data) == 8

    def test_help(self):
        
        help_list = Alma._get_help_page()
        assert help_list[0][0] == u'Position'
        assert help_list[1][0] == u'Energy'
        assert help_list[1][1][0] == (u'Frequency', 'frequency')
