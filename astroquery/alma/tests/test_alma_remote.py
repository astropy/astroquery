# Licensed under a 3-clause BSD style license - see LICENSE.rst
import tempfile
import shutil
import numpy as np
import os
import pytest

from astropy import coordinates
from astropy import units as u
from six.moves.urllib_parse import urlparse

from .. import Alma
from .. import _url_list, _test_url_list

# ALMA tests involving staging take too long, leading to travis timeouts
# TODO: make this a configuration item
SKIP_SLOW = True

all_colnames = {'Project code', 'Source name', 'RA', 'Dec', 'Band',
                'Frequency resolution', 'Integration', 'Release date',
                'Frequency support', 'Velocity resolution', 'Pol products',
                'Observation date', 'PI name', 'PWV', 'Member ous id',
                'Asdm uid', 'Project title', 'Project type', 'Scan intent',
                'Spatial resolution', 'Largest angular scale',
                'QA2 Status', 'Group ous id', 'Pub'}


@pytest.mark.remote_data
class TestAlma:

    def setup_class(cls):
        pass
        # new test server
        # this server seems not to serve a help page?
        # Alma.archive_url = "https://2016-03.asa-test.alma.cl/aq/"
        # starting somewhere between Nov 2015 and Jan 2016, the beta server
        # stopped serving the actual data, making all staging attempts break
        # Alma.archive_url = 'http://beta.cadc-ccda.hia-iha.nrc-cnrc.gc.ca'

    @pytest.fixture()
    def temp_dir(self, request):
        my_temp_dir = tempfile.mkdtemp()

        def fin():
            shutil.rmtree(my_temp_dir)
        request.addfinalizer(fin)
        return my_temp_dir

    def test_help(self):
        Alma().help()

    def test_SgrAstar(self, temp_dir):
        alma = Alma()
        alma.cache_location = temp_dir

        result_s = alma.query_object('Sgr A*')
        # cycle 1 data are missing from the archive assert b'2011.0.00887.S' in result_s['Project code']
        assert b'2013.1.00857.S' in result_s['proposal_id']
        c = coordinates.SkyCoord(266.41681662 * u.deg, -29.00782497 * u.deg,
                                 frame='fk5')
        result_c = alma.query_region(c, 1 * u.deg)
        assert b'2013.1.00857.S' in result_c['proposal_id']
        # "The Brick", g0.253, is in this one
        # assert b'2011.0.00217.S' in result_c['Project code'] # missing cycle 1 data
        assert b'2012.1.00635.S' in result_c['proposal_id']

    @pytest.mark.skipif("SKIP_SLOW")
    def test_m83(self, temp_dir, recwarn):
        alma = Alma()
        alma.cache_location = temp_dir

        m83_data = alma.query_object('M83')
        uids = np.unique(m83_data['obs_id'])
        link_list = alma.stage_data(uids)

        # On Feb 8, 2016 there were 83 hits.  This number should never go down.
        # Except it has.  On May 18, 2016, there were 47.
        assert len(link_list) >= 47

        # test re-staging
        # (has been replaced with warning)
        # with pytest.raises(requests.HTTPError) as ex:
        #    link_list = alma.stage_data(uids)
        # assert ex.value.args[0] == ('Received an error 405: this may indicate you have '
        #                            'already staged the data.  Try downloading the '
        #                            'file URLs directly with download_files.')

        # log.warning doesn't actually make a warning
        # link_list = alma.stage_data(uids)
        # w = recwarn.pop()
        # assert (str(w.message) == ('Error 405 received.  If you have previously staged the '
        #                           'same UIDs, the result returned is probably correct,'
        #                           ' otherwise you may need to create a fresh astroquery.Alma instance.'))

    @pytest.mark.skipif("SKIP_SLOW")
    def test_stage_data(self, temp_dir, recwarn):
        alma = Alma()
        alma.cache_location = temp_dir

        result_s = alma.query_object('Sgr A*')
        # assert b'2011.0.00887.S' in result_s['Project code']
        assert b'2013.1.00857.S' in result_s['proposal_id']
        # assert b'uid://A002/X40d164/X1b3' in result_s['Asdm uid']
        assert b'uid://A002/X651f57/Xade' in result_s['asdm_uid']
        # match = result_s['Asdm uid'] == b'uid://A002/X40d164/X1b3'
        match = result_s['asdm_uid'] == b'uid://A002/X651f57/Xade'
        uid = result_s['obs_id'][match]

        result = alma.stage_data(uid)

        assert ('2012.1.00080.S_uid___A002_X6444ba_X10_001_of_001.tar' in
                os.path.split(result['URL'][0])[1])

        # test re-staging
        # with pytest.raises(requests.HTTPError) as ex:
        #    result = alma.stage_data([uid])
        # assert ex.value.args[0] == ('Received an error 405: this may indicate you have '
        #                            'already staged the data.  Try downloading the '
        #                            'file URLs directly with download_files.')

        # log.warning doesn't actually make a warning
        # result = alma.stage_data([uid])
        # w = recwarn.pop()
        # assert (str(w.message) == ('Error 405 received.  If you have previously staged the '
        #                           'same UIDs, the result returned is probably correct,'
        #                           ' otherwise you may need to create a fresh astroquery.Alma instance.'))

    @pytest.mark.skipif("SKIP_SLOW")
    def test_doc_example(self, temp_dir):
        alma = Alma()
        alma.cache_location = temp_dir
        alma2 = Alma()
        alma2.cache_location = temp_dir
        m83_data = alma.query_object('M83')
        # the order can apparently sometimes change
        # These column names change too often to keep testing.
        # assert set(m83_data.colnames) == set(all_colnames)
        galactic_center = coordinates.SkyCoord(0 * u.deg, 0 * u.deg,
                                               frame='galactic')
        gc_data = alma.query_region(galactic_center, 1 * u.deg)
        # assert len(gc_data) >= 425 # Feb 8, 2016
        assert len(gc_data) >= 50  # Nov 16, 2016

        uids = np.unique(m83_data['asdm_uid'])
        assert b'uid://A002/X3b3400/X90f' in uids
        X90f = (m83_data['asdm_uid'] == b'uid://A002/X3b3400/X90f')
        assert X90f.sum() == 4  # Jul 2, 2017: increased from 1
        X31 = (m83_data['member_ous_uid'] == b'uid://A002/X3216af/X31')
        assert X31.sum() == 4  # Jul 2, 2017: increased from 1

        asdm = alma.stage_data('uid://A002/X3b3400/X90f')
        totalsize_asdm = asdm['size'].sum() * u.Unit(asdm['size'].unit)
        assert (totalsize_asdm.to(u.B).value == 0.0)

        mous = alma2.stage_data('uid://A002/X3216af/X31')
        totalsize_mous = mous['size'].sum() * u.Unit(mous['size'].unit)
        # More recent ALMA request responses do not include any information
        # about file size, so we have to allow for the possibility that all
        # file sizes are replaced with -1
        assert (totalsize_mous.to(u.GB).value > 159)

    def test_query(self, temp_dir):
        alma = Alma()
        alma.cache_location = temp_dir
        #  TODO start date?
        result = alma.query(payload={'start_date': '<11-11-2011'},
                            public=False, science=True)
        # Nov 16, 2016: 159
        # Apr 25, 2017: 150
        # Jul 2, 2017: 160
        # May 9, 2018: 162
        # March 18, 2019: 171 (seriously, how do they keep changing history?)
        assert len(result) == 171

        result = alma.query(payload={'member_ous_uid': 'uid://A001/X11a2/X11'},
                            science=True)
        assert len(result) == 1

    # As of April 2017, these data are *MISSING FROM THE ARCHIVE*.
    # This has been reported, as it is definitely a bug.
    @pytest.mark.xfail
    @pytest.mark.bigdata
    @pytest.mark.skipif("SKIP_SLOW")
    def test_cycle1(self, temp_dir):
        # About 500 MB
        alma = Alma()
        alma.cache_location = temp_dir

        target = 'NGC4945'
        project_code = '2012.1.00912.S'

        payload = {'project_code': project_code,
                   'source_name_alma': target, }
        result = alma.query(payload=payload)
        assert len(result) == 1

        # Need new Alma() instances each time
        a1 = alma()
        uid_url_table_mous = a1.stage_data(result['member_ous_uid'])
        a2 = alma()
        uid_url_table_asdm = a2.stage_data(result['asdm_uid'])
        # I believe the fixes as part of #495 have resulted in removal of a
        # redundancy in the table creation, so a 1-row table is OK here.
        # A 2-row table may not be OK any more, but that's what it used to
        # be...
        assert len(uid_url_table_asdm) == 1
        assert len(uid_url_table_mous) >= 2  # now is len=3 (Nov 17, 2016)

        # URL should look like:
        # https://almascience.eso.org/dataPortal/requests/anonymous/944120962/ALMA/2012.1.00912.S_uid___A002_X5a9a13_X528_001_of_001.tar/2012.1.00912.S_uid___A002_X5a9a13_X528_001_of_001.tar
        # https://almascience.eso.org/rh/requests/anonymous/944222597/2012.1.00912.S_uid___A002_X5a9a13_X528_001_of_001.tar/2012.1.00912.S_uid___A002_X5a9a13_X528_001_of_001.tar

        small = uid_url_table_mous['size'] < 1

        urls_to_download = uid_url_table_mous[small]['URL']

        uri = urlparse(urls_to_download[0])
        assert uri.path == ('/dataPortal/requests/anonymous/{0}/ALMA/2012.1.00912.S_uid___A002_X5a9a13_X528_001_of_001.tar/2012.1.00912.S_uid___A002_X5a9a13_X528_001_of_001.tar'  # noqa
                            .format(a1._staging_log['staging_page_id']))

        # THIS IS FAIL
        # '2012.1.00912.S_uid___A002_X5a9a13_X528_001_of_001.tar'
        left = uid_url_table_mous['URL'][0].split("/")[-1]
        assert left == '2012.1.00912.S_uid___A002_X5a9a13_X528_001_of_001.tar'
        right = uid_url_table_mous['uid'][0]
        assert right == 'uid://A002/X5a9a13/X528'
        assert left[15:-15] == right.replace(":", "_").replace("/", "_")
        data = alma.download_and_extract_files(urls_to_download)

        assert len(data) == 6

    @pytest.mark.skipif("SKIP_SLOW")
    def test_cycle0(self, temp_dir):
        # About 20 MB

        alma = Alma()
        alma.cache_location = temp_dir

        target = 'NGC4945'
        project_code = '2011.0.00121.S'

        payload = {'project_id': project_code,
                   'target_name': target}
        result = alma.query(payload=payload)
        assert len(result) == 80

        alma1 = alma()
        alma2 = alma()
        uid_url_table_mous = alma1.stage_data(result['member_ous_uid'])
        uid_url_table_asdm = alma2.stage_data(result['asdm_uid'])
        assert len(uid_url_table_asdm) == 1
        assert len(uid_url_table_mous) == 32

        assert uid_url_table_mous[0]['URL'].split("/")[-1] == '2011.0.00121.S_2012-08-16_001_of_002.tar'
        assert uid_url_table_mous[0]['uid'] == 'uid://A002/X327408/X246'

        small = uid_url_table_mous['size'] < 1

        urls_to_download = uid_url_table_mous[small]['URL']
        # Check that all URLs show up in the Cycle 0 table
        for url in urls_to_download:
            tarfile_name = os.path.split(url)[-1]
            assert tarfile_name in alma._cycle0_tarfile_content['ID']

        data = alma.download_and_extract_files(urls_to_download)

        # There are 10 small files, but only 8 unique
        assert len(data) == 8

    def test_keywords(self, temp_dir):

        alma = Alma()
        alma.cache_location = temp_dir

        result = alma.query(payload={'spatres': ('-Inf', 0.1)},
                            public=False, cache=False)

        assert len(result) >= 72
        assert b'Ganymede' in result['target_name']


@pytest.mark.remote_data
def test_project_metadata():
    alma = Alma()
    metadata = alma.get_project_metadata('2013.1.00269.S')
    assert metadata == ['Sgr B2, a high-mass molecular cloud in our Galaxy\'s Central Molecular Zone, is the most extreme site of ongoing star formation in the Local Group in terms of its gas content, temperature, and velocity dispersion. If any cloud in our galaxy is analogous to the typical cloud at the universal peak of star formation at z~2, this is it. We propose a 6\'x6\' mosaic in the 3mm window targeting gas thermometer lines, specifically CH3CN and its isotopologues. We will measure the velocity dispersion and temperature of the molecular gas on all scales (0.02 - 12 pc, 0.5" - 5\') within the cloud, which will yield resolved measurements of the Mach number and the sonic scale of the gas. We will assess the relative importance of stellar feedback and turbulence on the star-forming gas, determining how extensive the feedback effects are within an ultradense environment. The observations will provide constraints on the inputs to star formation theories and will determine their applicability in extremely dense, turbulent, and hot regions. Sgr B2 will be used as a testing ground for star formation theories in an environment analogous to high-z starburst clouds in which they must be applied.']


@pytest.mark.remote_data
@pytest.mark.parametrize('dataarchive_url', _test_url_list)
def test_staging_postfeb2020(dataarchive_url):

    alma = Alma()
    alma.archive_url = dataarchive_url
    tbl = alma.stage_data('uid://A001/X121/X4ba')

    assert 'mous_uid' in tbl.colnames

    assert '2013.1.00269.S_uid___A002_X9de499_X3d6c.asdm.sdm.tar' in tbl['name']


@pytest.mark.remote_data
@pytest.mark.parametrize('dataarchive_url', _url_list)
def test_staging_uptofeb2020(dataarchive_url):

    alma = Alma()
    alma.archive_url = dataarchive_url
    tbl = alma.stage_data('uid://A001/X121/X4ba')

    assert 'mous_uid' in tbl.colnames

    names = [x.split("/")[-1] for x in tbl[tbl['mous_uid'] == 'uid://A001/X147/X92']['URL']]

    assert '2013.1.00269.S_uid___A002_X9de499_X3d6c.asdm.sdm.tar' in names


@pytest.mark.remote_data
@pytest.mark.parametrize('dataarchive_url', _test_url_list)
def test_staging_stacking(dataarchive_url):
    alma = Alma()
    alma.archive_url = dataarchive_url

    tbl = alma.stage_data(['uid://A001/X13d5/X1d', 'uid://A002/X3216af/X31',
                           'uid://A001/X12a3/X240'])
