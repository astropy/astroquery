# Licensed under a 3-clause BSD style license - see LICENSE.rst

import numpy as np
import pytest

from astroquery.eso import Eso
from astroquery.exceptions import NoResultsWarning

instrument_list = [u'fors1', u'fors2', u'sphere', u'vimos', u'omegacam',
                   u'hawki', u'isaac', u'naco', u'visir', u'vircam', u'apex',
                   u'giraffe', u'uves', u'xshooter', u'muse', u'crires',
                   u'kmos', u'sinfoni', u'amber', u'midi', u'pionier',
                   u'gravity', u'espresso', u'wlgsu', u'matisse', u'eris']

# Some tests take too long, leading to travis timeouts
# TODO: make this a configuration item
SKIP_SLOW = True

SGRA_SURVEYS = ['195.B-0283', 'GIRAFFE', 'HARPS', 'HAWKI', 'KMOS',
                'ERIS-SPIFFIER',
                'MW-BULGE-PSFPHOT', 'VPHASplus', 'VVV', 'VVVX', 'XSHOOTER']


@pytest.mark.remote_data
class TestEso:
    def test_SgrAstar(self, tmp_path):
        eso = Eso()
        eso.cache_location = tmp_path

        instruments = eso.list_instruments(cache=False)
        # in principle, we should run both of these tests
        # result_i = eso.query_instrument('midi', target='Sgr A*')
        # Equivalent, does not depend on SESAME:
        result_i = eso.query_instrument('midi', coord1=266.41681662,
                                        coord2=-29.00782497, cache=False)

        surveys = eso.list_surveys(cache=False)
        assert len(surveys) > 0
        # result_s = eso.query_surveys('VVV', target='Sgr A*')
        # Equivalent, does not depend on SESAME:
        result_s = eso.query_surveys(surveys='VVV', coord1=266.41681662,
                                     coord2=-29.00782497,
                                     box='01 00 00',
                                     cache=False)

        assert 'midi' in instruments
        assert result_i is not None
        assert 'VVV' in surveys
        assert result_s is not None
        assert 'Object' in result_s.colnames
        assert 'b333' in result_s['Object']

    def test_multisurvey(self, tmp_path):

        eso = Eso()
        eso.cache_location = tmp_path
        eso.ROW_LIMIT = 1000
        # first b333 was at 157
        # first pistol....?

        result_s = eso.query_surveys(surveys=['VVV', 'XSHOOTER'],
                                     coord1=266.41681662,
                                     coord2=-29.00782497,
                                     box='01 00 00',
                                     cache=False)

        assert result_s is not None
        assert 'Object' in result_s.colnames
        assert 'b333_414_58214' in result_s['Object']
        assert 'Pistol-Star' in result_s['Object']

    def test_empty_return(self):
        # test for empty return with an object from the North
        eso = Eso()
        surveys = eso.list_surveys(cache=False)
        assert len(surveys) > 0

        # Avoid SESAME
        with pytest.warns(NoResultsWarning):
            result_s = eso.query_surveys(surveys=surveys[0], coord1=202.469575,
                                         coord2=47.195258, cache=False)

        assert result_s is None

    def test_SgrAstar_remotevslocal(self, tmp_path):
        eso = Eso()
        # Remote version
        result1 = eso.query_instrument('gravity', coord1=266.41681662,
                                       coord2=-29.00782497, cache=False)
        # Local version
        eso.cache_location = tmp_path
        result2 = eso.query_instrument('gravity', coord1=266.41681662,
                                       coord2=-29.00782497, cache=True)
        assert all(result1 == result2)

    def test_list_instruments(self):
        # If this test fails, we may simply need to update it

        inst = set(Eso.list_instruments(cache=False))

        # we only care about the sets matching
        assert set(inst) == set(instrument_list)

    def test_retrieve_data(self):
        eso = Eso()
        file_id = 'AMBER.2006-03-14T07:40:19.830'
        result = eso.retrieve_data(file_id)
        assert isinstance(result, str)
        assert file_id in result

    @pytest.mark.skipif('not Eso.USERNAME')
    def test_retrieve_data_authenticated(self):
        eso = Eso()
        eso.login()
        file_id = 'AMBER.2006-03-14T07:40:19.830'
        result = eso.retrieve_data(file_id)
        assert isinstance(result, str)
        assert file_id in result

    def test_retrieve_data_list(self):
        eso = Eso()
        datasets = ['MIDI.2014-07-25T02:03:11.561', 'AMBER.2006-03-14T07:40:19.830']
        result = eso.retrieve_data(datasets)
        assert isinstance(result, list)
        assert len(result) == 2

    # TODO: remove filter when https://github.com/astropy/astroquery/issues/2539 is fixed
    @pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
    @pytest.mark.parametrize('instrument', instrument_list)
    def test_help(self, instrument):
        eso = Eso()
        eso.query_instrument(instrument, help=True)

    def test_apex_retrieval(self):
        eso = Eso()

        tbl = eso.query_apex_quicklooks(prog_id='095.F-9802')
        tblb = eso.query_apex_quicklooks(project_id='095.F-9802')

        assert len(tbl) == 5
        assert set(tbl['Release Date']) == {'2015-07-17', '2015-07-18',
                                            '2015-09-15', '2015-09-18'}

        assert np.all(tbl == tblb)

    def test_each_instrument_SgrAstar(self, tmp_path):
        eso = Eso()
        eso.cache_location = tmp_path

        instruments = eso.list_instruments(cache=False)

        for instrument in instruments:
            try:
                result = eso.query_instrument(instrument, coord1=266.41681662, coord2=-29.00782497, cache=False)
            except NoResultsWarning:
                # Sometimes there are ResourceWarnings, we ignore those for this test
                pass
            else:
                assert len(result) > 0

    def test_each_survey_and_SgrAstar(self, tmp_path):
        eso = Eso()
        eso.cache_location = tmp_path
        eso.ROW_LIMIT = 5

        surveys = eso.list_surveys(cache=False)
        for survey in surveys:
            if survey in SGRA_SURVEYS:
                result_s = eso.query_surveys(surveys=survey, coord1=266.41681662,
                                             coord2=-29.00782497,
                                             box='01 00 00',
                                             cache=False)
                assert len(result_s) > 0
            else:
                with pytest.warns(NoResultsWarning):
                    result_s = eso.query_surveys(surveys=survey, coord1=266.41681662,
                                                 coord2=-29.00782497,
                                                 box='01 00 00',
                                                 cache=False)
                    assert result_s is None

                    generic_result = eso.query_surveys(surveys=survey)
                    assert len(generic_result) > 0

    def test_mixed_case_instrument(self, tmp_path):
        eso = Eso()
        eso.cache_location = tmp_path
        eso.ROW_LIMIT = 5

        result1 = eso.query_instrument('midi', coord1=266.41681662,
                                       coord2=-29.00782497, cache=False)
        result2 = eso.query_instrument('MiDi', coord1=266.41681662,
                                       coord2=-29.00782497, cache=False)

        assert np.all(result1 == result2)
