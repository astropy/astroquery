# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
===========================
ESO Astroquery Module tests
===========================

European Southern Observatory (ESO)

"""

from collections import Counter
import pytest

from astropy.table import Table
from astroquery.exceptions import NoResultsWarning, MaxResultsWarning
from astroquery.eso import Eso

instrument_list = ['alpaca', 'fors1', 'fors2', 'sphere', 'vimos', 'omegacam',
                   'hawki', 'isaac', 'naco', 'visir', 'vircam',
                   'apex',
                   'giraffe', 'uves', 'xshooter', 'muse', 'crires',
                   'kmos', 'sinfoni', 'amber', 'midi', 'pionier',
                   'gravity', 'espresso', 'wlgsu', 'matisse', 'eris',
                   'fiat',
                   'efosc', 'harps', 'nirps', 'sofi'
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
        eso.maxrec = 7
        with pytest.warns(MaxResultsWarning):
            t = eso.query_tap_service("select * from ivoa.ObsCore")
        lt = len(t)
        assert isinstance(t, Table), f"Expected type {type(Table)}; Obtained {type(t)}"
        assert len(t) > 0, "Table length is zero"
        assert len(t) == eso.maxrec, f"Table length is {lt}, expected {eso.maxrec}"

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_row_limit(self):
        eso = Eso()
        eso.maxrec = 5
        # since in this case the results are truncated, a warning is issued

        with pytest.warns(MaxResultsWarning):
            table = eso.query_instrument('UVES')
            n = len(table)
            assert n == eso.maxrec, f"Expected {eso.maxrec}; Obtained {n}"

        with pytest.warns(MaxResultsWarning):
            table = eso.query_surveys('VVV')
            n = len(table)
            assert n == eso.maxrec, f"Expected {eso.maxrec}; Obtained {n}"

        with pytest.warns(MaxResultsWarning):
            table = eso.query_main()
            n = len(table)
            assert n == eso.maxrec, f"Expected {eso.maxrec}; Obtained {n}"

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_top(self):
        eso = Eso()
        top = 5
        eso.maxrec = None
        # in this case the results are NOT truncated, no warnings should be issued

        table = eso.query_instrument('UVES', top=top)
        n = len(table)
        assert n == top, f"Expected {top}; Obtained {n}"

        table = eso.query_surveys('VVV', top=top)
        n = len(table)
        assert n == top, f"Expected {top}; Obtained {n}"

        table = eso.query_main(top=top)
        n = len(table)
        assert n == top, f"Expected {top}; Obtained {n}"

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_sgrastar(self):
        eso = Eso()
        eso.maxrec = 1

        instruments = eso.list_instruments()
        # in principle, we should run both of these tests
        # result_i = eso.query_instrument('midi', target='Sgr A*')
        # Equivalent, does not depend on SESAME:
        with pytest.warns(MaxResultsWarning):
            result_i = eso.query_instrument('midi', ra=266.41681662,
                                            dec=-29.00782497, radius=1.0)

        collections = eso.list_surveys()
        assert len(collections) > 0
        # result_s = eso.query_collections('VVV', target='Sgr A*')
        # Equivalent, does not depend on SESAME:
        with pytest.warns(MaxResultsWarning):
            result_s = eso.query_surveys(surveys='VVV', ra=266.41681662,
                                         dec=-29.00782497,
                                         radius=1.0)

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
        eso.maxrec = 1000

        test_collections = ['VVV', 'XSHOOTER']
        with pytest.warns(MaxResultsWarning):
            result_s = eso.query_surveys(surveys=test_collections,
                                         ra=266.41681662,
                                         dec=-29.00782497,
                                         radius=1.0)

        assert result_s is not None
        assert 'target_name' in result_s.colnames

        counts = Counter(result_s["obs_collection"].data)
        for tc in test_collections:
            assert counts[tc] > 0, f"{tc} : collection not present in results"

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_empty_return(self):
        # test for empty return with an object from the North
        eso = Eso()
        collections = eso.list_surveys()
        assert len(collections) > 0

        # Avoid SESAME
        with pytest.warns(NoResultsWarning):
            result_s = eso.query_surveys(surveys=collections[0], ra=202.469575,
                                         dec=47.195258, radius=1.0)

        assert len(result_s) == 0

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_sgrastar_column_filters(self):
        eso = Eso()

        result1 = eso.query_surveys(["sphere", "vegas"],
                                    columns=("obs_collection, calib_level, "
                                    "multi_ob, filter, s_pixel_scale, instrument_name"),
                                    calib_level=3,
                                    multi_ob='M'
                                    )

        result2 = eso.query_surveys("sphere, vegas",
                                    columns=("obs_collection, calib_level, "
                                             "multi_ob, filter, s_pixel_scale, instrument_name"),
                                    column_filters={
                                        'calib_level': 3,
                                        'multi_ob': 'M'
                                    }
                                    )

        assert all(result1.values_equal(result2))

    def test_list_instruments(self):
        # If this test fails, we may simply need to update it
        inst = set(Eso.list_instruments())
        assert set(inst) == set(instrument_list), f"Expected result {instrument_list}; Obtained: {inst}"

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
        eso.query_instrument(instrument, help=True)

    def test_apex_retrieval(self):
        eso = Eso()

        tblb = eso.query_apex_quicklooks(project_id='E-095.F-9802A-2015')
        tbla = eso.query_apex_quicklooks(prog_id='095.F-9802(A)')

        assert len(tbla) == 5
        assert set(tbla['release_date']) == {
            '2015-07-17T03:06:23.280Z',
            '2015-07-18T12:07:32.713Z',
            '2015-09-18T11:31:15.867Z',
            '2015-09-15T11:06:55.663Z',
            '2015-09-18T11:46:19.970Z'
        }

        assert all(tbla.values_equal(tblb))

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    @pytest.mark.parametrize('instrument', instrument_list)
    def test_each_instrument_sgrastar(self, instrument):
        eso = Eso()
        eso.maxrec = 1  # Either we have maxrec results or none at all
        try:
            with pytest.warns(MaxResultsWarning):
                result = eso.query_instrument(instrument,
                                              ra=266.41681662, dec=-29.00782497, radius=1.0)
        except NoResultsWarning:  # we don't care if there are no results
            pass
        else:
            assert result is not None, f"query_instrument({instrument}) returned None"
            assert len(result) > 0, f"query_instrument({instrument}) returned no records"

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_each_collection_sgrastar(self, tmp_path):
        eso = Eso()
        eso.cache_location = tmp_path
        eso.maxrec = 1

        collections = eso.list_surveys()
        for collection in collections:
            if collection in SGRA_COLLECTIONS:
                with pytest.warns(MaxResultsWarning):
                    result_s = eso.query_surveys(
                        surveys=collection,
                        ra=266.41681662, dec=-29.00782497, radius=0.1775)
                assert len(result_s) > 0
            else:
                with pytest.warns(NoResultsWarning):
                    result_s = eso.query_surveys(surveys=collection, ra=266.41681662,
                                                 dec=-29.00782497,
                                                 radius=0.1775)
                    assert len(result_s) == 0, f"Failed for collection {collection}"

                with pytest.warns(MaxResultsWarning):
                    generic_result = eso.query_surveys(surveys=collection)

                    assert generic_result is not None, f"query_collection({collection}) returned None"
                    assert len(generic_result) > 0, f"query_collection({collection}) returned no records"

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_mixed_case_instrument(self, tmp_path):
        eso = Eso()
        eso.cache_location = tmp_path
        eso.maxrec = 5

        with pytest.warns(MaxResultsWarning):
            result1 = eso.query_instrument('midi', ra=266.41681662,
                                           dec=-29.00782497, radius=1.0)
            result2 = eso.query_instrument('MiDi', ra=266.41681662,
                                           dec=-29.00782497, radius=1.0)

        assert all(result1.values_equal(result2))

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_main_sgrastar(self):
        eso = Eso()
        eso.maxrec = 5

        with pytest.warns(MaxResultsWarning):
            result = eso.query_main(target='SGR A', object='SGR A')

        assert len(result) == 5
        assert 'SGR A' in result['object']
        assert 'SGR A' in result['target']
