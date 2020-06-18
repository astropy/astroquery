# Licensed under a 3-clause BSD style license - see LICENSE.rst
import tempfile
import shutil
import numpy as np
import pytest

from astropy import coordinates
from astropy import units as u

from astroquery.utils.commons import ASTROPY_LT_4_1
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

        help_list = Alma._get_help_page()
        assert help_list[0][0] == u'Position'
        assert help_list[1][0] == u'Energy'
        assert help_list[1][1][0] == (u'Frequency', 'frequency')

    def test_SgrAstar(self, temp_dir):
        alma = Alma()
        alma.cache_location = temp_dir

        result_s = alma.query_object('Sgr A*')

        c = coordinates.SkyCoord(266.41681662 * u.deg, -29.00782497 * u.deg,
                                 frame='fk5')
        result_c = alma.query_region(c, 1 * u.deg)

        if ASTROPY_LT_4_1:
            # cycle 1 data are missing from the archive
            # assert b'2011.0.00887.S' in result_s['Project code']
            # "The Brick", g0.253, is in this one
            # assert b'2011.0.00217.S' in result_c['Project code']

            assert b'2013.1.00857.S' in result_s['Project code']
            assert b'2013.1.00857.S' in result_c['Project code']
            assert b'2012.1.00932.S' in result_c['Project code']
        else:
            assert '2013.1.00857.S' in result_s['Project code']
            assert '2013.1.00857.S' in result_c['Project code']
            assert '2012.1.00932.S' in result_c['Project code']

    @pytest.mark.skipif("SKIP_SLOW")
    def test_m83(self, temp_dir, recwarn):
        alma = Alma()
        alma.cache_location = temp_dir

        m83_data = alma.query_object('M83')
        uids = np.unique(m83_data['Member ous id'])
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

    def test_stage_data(self, temp_dir, recwarn):
        alma = Alma()
        alma.cache_location = temp_dir

        result_s = alma.query_object('Sgr A*')

        if ASTROPY_LT_4_1:
            assert b'2013.1.00857.S' in result_s['Project code']
            assert b'uid://A002/X40d164/X1b3' in result_s['Asdm uid']
            assert b'uid://A002/X391d0b/X23d' in result_s['Member ous id']
            match_val = b'uid://A002/X40d164/X1b3'
        else:
            assert '2013.1.00857.S' in result_s['Project code']
            assert 'uid://A002/X40d164/X1b3' in result_s['Asdm uid']
            assert 'uid://A002/X391d0b/X23d' in result_s['Member ous id']
            match_val = 'uid://A002/X40d164/X1b3'

        match = result_s['Asdm uid'] == match_val
        uid = result_s['Member ous id'][match]

        result = alma.stage_data(uid)

        assert ('uid___A002_X40d164_X1b3' in result['URL'][0])

    def test_stage_data_listall(self, temp_dir, recwarn):
        """
        test for expanded capability created in #1683
        """
        alma = Alma()
        alma.cache_location = temp_dir

        result_s = alma.query_object('Sgr A*')
        uid = 'uid://A001/X12a3/Xe9'
        assert uid in result_s['Member ous id']

        result1 = alma.stage_data(uid, expand_tarfiles=False)
        result2 = alma.stage_data(uid, expand_tarfiles=True)

        assert len(result2) > len(result1)

        assert 'PIPELINE_PRODUCT' in result2['type']
        assert 'PIPELINE_AUXILIARY_TARFILE' in result1['type']

    def test_stage_data_json(self, temp_dir, recwarn):
        """
        test for json returns
        """
        alma = Alma()
        alma.cache_location = temp_dir

        result_s = alma.query_object('Sgr A*')
        uid = 'uid://A001/X12a3/Xe9'
        assert uid in result_s['Member ous id']

        result1 = alma.stage_data(uid, return_json=False)
        result2 = alma.stage_data(uid, return_json=True)

        assert len(result1) > 0
        assert set(result2[0].keys()) == {'id', 'name', 'type', 'sizeInBytes',
                                          'permission', 'children',
                                          'allMousUids'}

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

        uids = np.unique(m83_data['Member ous id'])
        if ASTROPY_LT_4_1:
            assert b'uid://A001/X11f/X30' in uids
            X30 = (m83_data['Member ous id'] == b'uid://A001/X11f/X30')
            X31 = (m83_data['Member ous id'] == b'uid://A002/X3216af/X31')
        else:
            assert 'uid://A001/X11f/X30' in uids
            X30 = (m83_data['Member ous id'] == 'uid://A001/X11f/X30')
            X31 = (m83_data['Member ous id'] == 'uid://A002/X3216af/X31')

        assert X30.sum() == 1  # Apr 2, 2020
        assert X31.sum() == 2  # Jul 2, 2017: increased from 1

        mous1 = alma.stage_data('uid://A001/X11f/X30')
        totalsize_mous1 = mous1['size'].sum() * u.Unit(mous1['size'].unit)
        assert (totalsize_mous1.to(u.B) > 1.9*u.GB)

        mous = alma2.stage_data('uid://A002/X3216af/X31')
        totalsize_mous = mous['size'].sum() * u.Unit(mous['size'].unit)
        # More recent ALMA request responses do not include any information
        # about file size, so we have to allow for the possibility that all
        # file sizes are replaced with -1
        assert (totalsize_mous.to(u.GB).value > 52)

    def test_query(self, temp_dir):
        alma = Alma()
        alma.cache_location = temp_dir

        result = alma.query(payload={'start_date': '<11-11-2011'},
                            public=False, science=True)
        # Nov 16, 2016: 159
        # Apr 25, 2017: 150
        # Jul 2, 2017: 160
        # May 9, 2018: 162
        # March 18, 2019: 171 (seriously, how do they keep changing history?)
        assert len(result) == 171

        result = alma.query(payload={'member_ous_id': 'uid://A001/X11a2/X11'},
                            science=True)
        assert len(result) == 1

    def test_keywords(self, temp_dir):

        alma = Alma()
        alma.cache_location = temp_dir

        result = alma.query(payload={'spatial_resolution': '<0.1',
                                     'science_keyword':
                                     ['High-mass star formation',
                                      'Disks around high-mass stars']},
                            public=False, cache=False)

        assert len(result) >= 72
        assert 'Orion_Source_I' in result['Source name']


@pytest.mark.remote_data
def test_project_metadata():
    alma = Alma()
    metadata = alma.get_project_metadata('2013.1.00269.S')
    assert metadata == ['Sgr B2, a high-mass molecular cloud in our Galaxy\'s Central Molecular Zone, is the most extreme site of ongoing star formation in the Local Group in terms of its gas content, temperature, and velocity dispersion. If any cloud in our galaxy is analogous to the typical cloud at the universal peak of star formation at z~2, this is it. We propose a 6\'x6\' mosaic in the 3mm window targeting gas thermometer lines, specifically CH3CN and its isotopologues. We will measure the velocity dispersion and temperature of the molecular gas on all scales (0.02 - 12 pc, 0.5" - 5\') within the cloud, which will yield resolved measurements of the Mach number and the sonic scale of the gas. We will assess the relative importance of stellar feedback and turbulence on the star-forming gas, determining how extensive the feedback effects are within an ultradense environment. The observations will provide constraints on the inputs to star formation theories and will determine their applicability in extremely dense, turbulent, and hot regions. Sgr B2 will be used as a testing ground for star formation theories in an environment analogous to high-z starburst clouds in which they must be applied.']  # noqa


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

    alma.stage_data(['uid://A001/X13d5/X1d', 'uid://A002/X3216af/X31',
                     'uid://A001/X12a3/X240'])
