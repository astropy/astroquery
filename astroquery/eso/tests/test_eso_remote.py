# Licensed under a 3-clause BSD style license - see LICENSE.rst
import numpy as np
import tempfile
import shutil
from astropy.tests.helper import pytest, remote_data
from astropy.extern import six
from ...exceptions import LoginError

from ...eso import Eso

instrument_list = [u'fors1', u'fors2', u'sphere', u'vimos', u'omegacam',
                   u'hawki', u'isaac', u'naco', u'visir', u'vircam', u'apex',
                   u'giraffe', u'uves', u'xshooter', u'muse', u'crires',
                   u'kmos', u'sinfoni', u'amber', u'midi', u'pionier',
                   u'harps',]


@remote_data
class TestEso:
    @pytest.fixture()
    def temp_dir(self, request):
        my_temp_dir = tempfile.mkdtemp()

        def fin():
            shutil.rmtree(my_temp_dir)
        request.addfinalizer(fin)
        return my_temp_dir

    def test_SgrAstar(self, temp_dir):
        eso = Eso()
        eso.cache_location = temp_dir

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
        result_s = eso.query_surveys('VVV', coord1=266.41681662,
                                     coord2=-29.00782497,
                                     box='01 00 00',
                                     cache=False)

        assert 'midi' in instruments
        assert result_i is not None
        assert 'VVV' in surveys
        assert result_s is not None
        assert 'Object' in result_s.colnames
        assert 'b333' in result_s['Object']

    def test_multisurvey(self, temp_dir):

        eso = Eso()
        eso.cache_location = temp_dir
        eso.ROW_LIMIT = 200 #first b333 is at 157

        result_s = eso.query_surveys(['VVV','XSHOOTER'],
                                     coord1=266.41681662,
                                     coord2=-29.00782497,
                                     box='01 00 00',
                                     cache=False)

        assert result_s is not None
        assert 'Object' in result_s.colnames
        assert 'b333' in result_s['Object']
        assert 'Pistol-Star' in result_s['Object']

    def test_nologin(self):
        # WARNING: this test will fail if you haven't cleared your cache and
        # you have downloaded this file!
        eso = Eso()

        with pytest.raises(LoginError) as exc:
            eso.retrieve_data('AMBER.2006-03-14T07:40:19.830')

        assert (exc.value.args[0] ==
                ("If you do not pass a username to login(), you should "
                 "configure a default one!"))

    def test_empty_return(self):
        # test for empty return with an object from the North
        eso = Eso()
        surveys = eso.list_surveys(cache=False)
        assert len(surveys) > 0
        # result_s = eso.query_survey(surveys[0], target='M51')
        # Avoid SESAME
        result_s = eso.query_surveys(surveys[0], coord1=202.469575,
                                     coord2=47.195258, cache=False)

        assert result_s is None

    def test_SgrAstar_remotevslocal(self, temp_dir):
        eso = Eso()
        # Remote version
        instruments = eso.list_instruments(cache=False)
        # result1 = eso.query_instrument(instruments[0], target='Sgr A*')
        result1 = eso.query_instrument(instruments[0], coord1=266.41681662,
                                       coord2=-29.00782497, cache=False)

        # Local version
        eso.cache_location = temp_dir
        instruments = eso.list_instruments(cache=False)
        # result2 = eso.query_instrument(instruments[0], target='Sgr A*')
        result2 = eso.query_instrument(instruments[0], coord1=266.41681662,
                                       coord2=-29.00782497, cache=False)

        assert result1 == result2

    def test_list_instruments(self):
        # If this test fails, we may simply need to update it

        inst = set(Eso.list_instruments(cache=False))

        # we only care about the sets matching
        assert set(inst) == set(instrument_list)

    # REQUIRES LOGIN!
    # Can we get a special login specifically for astroquery testing?
    # def test_data_retrieval():
    #
    #    data_product_id = 'AMBER.2006-03-14T07:40:03.741'
    #    data_files = eso.retrieve_data([data_product_id])
    #    # How do we know if we're going to get .fits or .fits.Z?
    #    assert 'AMBER.2006-03-14T07:40:03.741.fits' in data_files[0]

    @pytest.mark.skipif('not Eso.USERNAME')
    def test_retrieve_data(self):
        eso = Eso()
        eso.login()
        result = eso.retrieve_data(["MIDI.2014-07-25T02:03:11.561"])
        assert len(result) > 0
        assert "MIDI.2014-07-25T02:03:11.561" in result[0]
        result = eso.retrieve_data("MIDI.2014-07-25T02:03:11.561")
        assert isinstance(result, six.string_types)

    @pytest.mark.skipif('not Eso.USERNAME')
    def test_retrieve_data_twice(self):
        eso = Eso()
        eso.login()
        result1 = eso.retrieve_data("MIDI.2014-07-25T02:03:11.561")
        result2 = eso.retrieve_data("AMBER.2006-03-14T07:40:19.830")

    @pytest.mark.parametrize('instrument', instrument_list)
    def test_help(self, instrument):
        eso = Eso()
        eso.query_instrument(instrument, help=True)

    def test_apex_retrieval(self):
        eso = Eso()

        tbl = eso.query_apex_quicklooks(prog_id='095.F-9802')
        tblb = eso.query_apex_quicklooks('095.F-9802')

        assert len(tbl) == 4
        assert set(tbl['Release Date']) == {'2015-07-17', '2015-07-18',
                                            '2015-09-15', '2015-09-18'}

        assert np.all(tbl == tblb)

    def test_each_instrument_SgrAstar(self, temp_dir):
        eso = Eso()
        eso.cache_location = temp_dir

        instruments = eso.list_instruments(cache=False)
        for instrument in instruments:
            result_i = eso.query_instrument(instrument, coord1=266.41681662,
                                            coord2=-29.00782497, cache=False)

    def test_each_survey_SgrAstar(self, temp_dir):
        eso = Eso()
        eso.cache_location = temp_dir

        surveys = eso.list_surveys(cache=False)
        for survey in surveys:
            result_s = eso.query_surveys(survey, coord1=266.41681662,
                                         coord2=-29.00782497,
                                         box='01 00 00',
                                         cache=False)
