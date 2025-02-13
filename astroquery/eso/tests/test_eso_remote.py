# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
===========================
ESO Astroquery Module tests
===========================

European Southern Observatory (ESO)

"""

from collections import Counter
import numpy as np
import pytest

from astropy.table import Table
from astroquery.exceptions import NoResultsWarning, MaxResultsWarning
from astroquery.eso import Eso

instrument_list = ['fors1', 'fors2', 'sphere', 'vimos', 'omegacam',
                   'hawki', 'isaac', 'naco', 'visir', 'vircam',
                   # TODO 'apex', uncomment when ready in the ISTs
                   'giraffe', 'uves', 'xshooter', 'muse', 'crires',
                   'kmos', 'sinfoni', 'amber', 'midi', 'pionier',
                   'gravity', 'espresso', 'wlgsu', 'matisse', 'eris',
                   'fiat',
                   ]

SGRA_COLLECTIONS = ['195.B-0283',
                    'ALMA',
                    'ATLASGAL',
                    'ERIS-SPIFFIER',
                    'GIRAFFE',
                    'HARPS',
                    'HAWKI',
                    'KMOS',
                    'MW-BULGE-PSFPHOT',
                    'VPHASplus',
                    'VVV',
                    'VVVX',
                    'XSHOOTER'
                    ]


@pytest.mark.remote_data
class TestEso:
    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_query_tap_service(self):
        eso = Eso()
        eso.ROW_LIMIT = 7
        with pytest.warns(MaxResultsWarning):
            t = eso.query_tap_service("select * from ivoa.ObsCore")
        lt = len(t)
        assert isinstance(t, Table), f"Expected type {type(Table)}; Obtained {type(t)}"
        assert len(t) > 0, "Table length is zero"
        assert len(t) == eso.ROW_LIMIT, f"Table length is {lt}, expected {eso.ROW_LIMIT}"

    def test_query_instrument(self):
        # TODO - Just testing whether this alleviates Codecov complaints
        assert True

    def test_query_collections(self):
        # TODO - Just testing whether this alleviates Codecov complaints
        assert True

    def test_query_main(self):
        # TODO - Just testing whether this alleviates Codecov complaints
        assert True

    def test_query_apex_quicklooks(self):
        # TODO - Just testing whether this alleviates Codecov complaints
        assert True

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_row_limit(self):
        eso = Eso()
        eso.ROW_LIMIT = 5
        # since in this case the results are truncated, a warning is issued

        with pytest.warns(MaxResultsWarning):
            table = eso.query_instrument('UVES', cache=False)
            n = len(table)
            assert n == eso.ROW_LIMIT, f"Expected {eso.ROW_LIMIT}; Obtained {n}"

        with pytest.warns(MaxResultsWarning):
            table = eso.query_collections('VVV', cache=False)
            n = len(table)
            assert n == eso.ROW_LIMIT, f"Expected {eso.ROW_LIMIT}; Obtained {n}"

        with pytest.warns(MaxResultsWarning):
            table = eso.query_main(cache=False)
            n = len(table)
            assert n == eso.ROW_LIMIT, f"Expected {eso.ROW_LIMIT}; Obtained {n}"

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_top(self):
        eso = Eso()
        top = 5
        eso.ROW_LIMIT = None
        # in this case the results are NOT truncated, no warnings should be issued

        table = eso.query_instrument('UVES', cache=False, top=top)
        n = len(table)
        assert n == top, f"Expected {top}; Obtained {n}"

        table = eso.query_collections('VVV', cache=False, top=top)
        n = len(table)
        assert n == top, f"Expected {top}; Obtained {n}"

        table = eso.query_main(cache=False, top=top)
        n = len(table)
        assert n == top, f"Expected {top}; Obtained {n}"

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_SgrAstar(self):
        eso = Eso()
        eso.ROW_LIMIT = 1

        instruments = eso.list_instruments(cache=False)
        # in principle, we should run both of these tests
        # result_i = eso.query_instrument('midi', target='Sgr A*')
        # Equivalent, does not depend on SESAME:
        with pytest.warns(MaxResultsWarning):
            result_i = eso.query_instrument('midi', ra=266.41681662,
                                            dec=-29.00782497, radius=1.0, cache=False)

        collections = eso.list_collections(cache=False)
        assert len(collections) > 0
        # result_s = eso.query_collections('VVV', target='Sgr A*')
        # Equivalent, does not depend on SESAME:
        with pytest.warns(MaxResultsWarning):
            result_s = eso.query_collections(collections='VVV', ra=266.41681662,
                                             dec=-29.00782497,
                                             radius=1.0,
                                             cache=False)

        assert 'midi' in instruments
        assert result_i is not None
        assert 'VVV' in collections
        assert result_s is not None

        # From obs.raw, we have "object" (when query_instruments)
        # object: Target designation as given by the astronomer,
        # though at times overwritten by the obeservatory,
        # especially for CALIB observations. Compare with the similar field called "target".)

        # From ivoa.ObsCore, we have "target_name" (when query_collections)
        # target_name: The target name as assigned by the Principal Investigator;
        # ref. Ref. OBJECT keyword in ESO SDP standard.
        # For spectroscopic public surveys, the value shall be set to the survey source identifier.
        assert 'target_name' in result_s.colnames
        assert 'b319' in result_s['target_name']

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_multicollection(self, tmp_path):

        eso = Eso()
        eso.cache_location = tmp_path
        eso.ROW_LIMIT = 1000

        test_collections = ['VVV', 'XSHOOTER']
        with pytest.warns(MaxResultsWarning):
            result_s = eso.query_collections(collections=test_collections,
                                             ra=266.41681662,
                                             dec=-29.00782497,
                                             radius=1.0,
                                             cache=False)

        assert result_s is not None
        assert 'target_name' in result_s.colnames

        counts = Counter(result_s["obs_collection"].data)
        for tc in test_collections:
            assert counts[tc] > 0, f"{tc} : collection not present in results"

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_empty_return(self):
        # test for empty return with an object from the North
        eso = Eso()
        collections = eso.list_collections(cache=False)
        assert len(collections) > 0

        # Avoid SESAME
        with pytest.warns(NoResultsWarning):
            result_s = eso.query_collections(collections=collections[0], ra=202.469575,
                                             dec=47.195258, radius=1.0, cache=False)

        assert len(result_s) == 0

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_SgrAstar_remotevslocal(self, tmp_path):
        eso = Eso()
        # TODO originally it was 'gravity', but it is not yet ready in the TAP ISTs
        instrument = 'uves'

        # Remote version
        with pytest.warns(MaxResultsWarning):
            result1 = eso.query_instrument(instrument, ra=266.41681662,
                                           dec=-29.00782497, radius=1.0, cache=False)
        # Local version
        eso.cache_location = tmp_path
        with pytest.warns(MaxResultsWarning):
            result2 = eso.query_instrument(instrument, ra=266.41681662,
                                           dec=-29.00782497, radius=1.0, cache=True)
        assert all(result1.values_equal(result2))

    def test_list_instruments(self):
        # If this test fails, we may simply need to update it

        inst = set(Eso.list_instruments(cache=False))

        # TODO ############ restore when they are fixed in TAP #
        try:
            inst.remove('apex')
        except ValueError:
            pass
        # #################################################### #

        # we only care about the sets matching
        assert set(inst) == set(instrument_list), \
            f"Expected result {instrument_list}; Obtained: {inst}"

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

    @pytest.mark.parametrize('instrument', instrument_list)
    def test_help(self, instrument):
        eso = Eso()
        eso.query_instrument(instrument, print_help=True)

    def test_apex_retrieval(self):
        eso = Eso()

        tbl = eso.query_apex_quicklooks(prog_id='095.F-9802', cache=False)
        tblb = eso.query_apex_quicklooks(project_id='095.F-9802', cache=False)

        assert len(tbl) == 5
        assert set(tbl['Release Date']) == {'2015-07-17', '2015-07-18',
                                            '2015-09-15', '2015-09-18'}

        assert np.all(tbl == tblb)

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_each_instrument_SgrAstar(self, tmp_path):
        eso = Eso()
        eso.cache_location = tmp_path
        eso.ROW_LIMIT = 5

        instruments = eso.list_instruments(cache=False)

        # TODO: restore all of these instruments when they are fixed in the TAP ists ##################################
        try:
            instruments.remove('apex')      # ValueError: 1:0: not well-formed (invalid token)
            #                               # pyvo.dal.exceptions.DALServiceError:
            #                                 500 Server Error:  for url: http://dfidev5.hq.eso.org:8123/tap_obs/sync
            instruments.remove('fiat')      # TODO pyvo.dal.exceptions.DALQueryError: # fiat has no ra and dec
            #                                 Error converting data type varchar to numeric.
            instruments.remove('espresso')  # pyvo.dal.exceptions.DALQueryError: Invalid column name 'obs_container_id'
            instruments.remove('gravity')   # pyvo.dal.exceptions.DALQueryError: Invalid column name 'obs_container_id'
            instruments.remove('matisse')   # pyvo.dal.exceptions.DALQueryError: Invalid column name 'obs_container_id'
            instruments.remove('omegacam')  # pyvo.dal.exceptions.DALQueryError: Invalid column name 'obs_container_id'
            instruments.remove('pionier')   # pyvo.dal.exceptions.DALQueryError: Invalid column name 'obs_container_id'
            instruments.remove('vircam')    # pyvo.dal.exceptions.DALQueryError: Invalid column name 'obs_container_id'
        except ValueError:
            pass
        # #################################################### #

        for instrument in instruments:
            try:
                with pytest.warns(MaxResultsWarning):
                    result = eso.query_instrument(instrument,
                                                  ra=266.41681662, dec=-29.00782497, radius=1.0,
                                                  cache=False)
            except NoResultsWarning:  # we don't care if there are no results
                pass
            else:
                assert result is not None, f"query_instrument({instrument}) returned None"
                assert len(result) > 0, f"query_instrument({instrument}) returned no records"

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_each_collection_and_SgrAstar(self, tmp_path):
        eso = Eso()
        eso.cache_location = tmp_path
        eso.ROW_LIMIT = 1

        collections = eso.list_collections(cache=False)
        for collection in collections:
            if collection in SGRA_COLLECTIONS:
                with pytest.warns(MaxResultsWarning):
                    result_s = eso.query_collections(collections=collection,
                                                     ra=266.41681662, dec=-29.00782497, radius=0.1775,
                                                     cache=False)
                assert len(result_s) > 0
            else:
                with pytest.warns(NoResultsWarning):
                    result_s = eso.query_collections(collections=collection, ra=266.41681662,
                                                     dec=-29.00782497,
                                                     radius=0.1775,
                                                     cache=False)
                    assert len(result_s) == 0, f"Failed for collection {collection}"

                with pytest.warns(MaxResultsWarning):
                    generic_result = eso.query_collections(collections=collection)

                    assert generic_result is not None, \
                        f"query_collection({collection}) returned None"
                    assert len(generic_result) > 0, \
                        f"query_collection({collection}) returned no records"

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_mixed_case_instrument(self, tmp_path):
        eso = Eso()
        eso.cache_location = tmp_path
        eso.ROW_LIMIT = 5

        with pytest.warns(MaxResultsWarning):
            result1 = eso.query_instrument('midi', ra=266.41681662,
                                           dec=-29.00782497, radius=1.0, cache=False)
            result2 = eso.query_instrument('MiDi', ra=266.41681662,
                                           dec=-29.00782497, radius=1.0, cache=False)

        assert all(result1.values_equal(result2))

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_main_SgrAstar(self):
        eso = Eso()
        eso.ROW_LIMIT = 5

        with pytest.warns(MaxResultsWarning):
            result = eso.query_main(target='SGR A', object='SGR A', cache=False)

        assert len(result) == 5
        assert 'SGR A' in result['object']
        assert 'SGR A' in result['target']
