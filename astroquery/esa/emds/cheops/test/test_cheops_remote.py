# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
==========================================
CHEOPS Tests
==========================================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import pytest
import os
import tempfile
from pyvo import DALQueryError
from astroquery.esa.emds.cheops import CheopsClass


def create_temp_folder():
    return tempfile.TemporaryDirectory()


cheops = CheopsClass()


@pytest.mark.remote_data
class TestCheopsRemote:

    def test_get_tables(self):
        names = cheops.get_tables(only_names=True)

        assert isinstance(names, list)
        assert len(names) > 0
        assert all(isinstance(n, str) for n in names)
        assert cheops.conf.CHEOPS_DATA_PRODUCT_TABLE in [n.lower() for n in names]

    def test_get_table(self):
        observation_request_table = cheops.get_table("cheops.observation_request")

        assert observation_request_table is not None
        assert hasattr(observation_request_table, "columns")
        assert len(observation_request_table.columns) > 0

        # BaseParam objects expose the column name in `.name`
        colnames = {c.name for c in observation_request_table.columns}
        for expected in {"obs_cat", "ra", "dec", "target_name"}:
            assert expected in colnames

    def test_query_tap(self):
        # Query an existing table
        result = cheops.query_tap("SELECT TOP 10 obs_cat, ra, dec, target_name FROM cheops.observation_request")

        assert result is not None
        assert len(result) > 0
        assert {"obs_cat", "ra", "dec", "target_name"}.issubset(set(result.colnames))

        # Query a table that does not exist
        with pytest.raises(DALQueryError) as err:
            cheops.query_tap("SELECT TOP 10 * FROM schema.table")
        assert "Unknown table" in str(err.value) or "does not exist" in str(err.value)

        # Store the result in a file
        temp_folder = create_temp_folder()
        filename = os.path.join(temp_folder.name, "query_tap.votable")
        cheops.query_tap("SELECT obs_cat, ra, dec FROM cheops.observation_request", output_file=filename)
        assert os.path.exists(filename)

        temp_folder.cleanup()

    def test_get_observations_metadata(self):
        meta = cheops.get_observations(get_metadata=True)

        assert meta is not None
        assert len(meta) > 0

        expected_cols = {"Column", "Description", "Unit", "Data Type", "UCD", "UType"}
        assert expected_cols.issubset(set(meta.colnames))

        # Check that some columns appear in the metadata
        available = set(meta["Column"])
        assert {"ra", "dec"}.issubset(available)

    def test_get_observations_cone_coordinates(self):
        results = cheops.get_observations(
            coordinates="81.1238 17.4175",
            radius=0.1,
            columns=["obs_cat", "ra", "dec"],
            async_job=True,
        )

        assert results is not None
        assert {"obs_cat", "ra", "dec"}.issubset(set(results.colnames))

    def test_get_observations_cone_target_name(self):
        results = cheops.get_observations(
            target_name="V1589 Cyg",
            radius=0.1,
            columns=["obs_cat", "ra", "dec", "target_name"],
            output_format='votable'
        )

        assert results is not None
        assert {"obs_cat", "ra", "dec", "target_name"}.issubset(set(results.colnames))

    def test_get_observations_filters(self):
        # Run the filtered search
        filters = {"request_id": 3000240001}

        results = cheops.get_observations(
            **filters
        )

        assert results is not None
        assert {"obs_cat", "ra", "dec", "target_temp", "target_mag_gaia", "target_mag_cheops"}.issubset(
            set(results.colnames)
        )

        # If results exist, validate they match filters
        if len(results) > 0:
            assert set(results["request_id"]) == {3000240001}

    def test_get_observations_output_file(self):
        temp_folder = create_temp_folder()
        filename = os.path.join(temp_folder.name, "get_observations_cheops.votable")

        results = cheops.get_observations(
            coordinates="81.1238 17.4175",
            radius=0.01,
            columns=["obs_cat", "ra", "dec"],
            output_file=filename,
            output_format='votable'
        )

        assert os.path.exists(filename)
        assert results is not None
        assert {"obs_cat", "ra", "dec"}.issubset(set(results.colnames))

        temp_folder.cleanup()

    def test_get_program(self):
        programs_by_key = cheops.get_program(program_key="PR240015")
        programs_by_title = cheops.get_program(
            title="Hunting a second transit of the long-period Neptune exoplanet HIP41378 e in the gaps of TESS")
        programs_by_pi = cheops.get_program(pi_name="SALOME GROUFFAL")

        assert len(programs_by_key) > 0
        assert (programs_by_key['programme_key'] == programs_by_title['programme_key'])
        assert (programs_by_key['programme_key'] == programs_by_pi['programme_key'])

    def test_get_visit_from_observation(self):
        observation = cheops.get_observations(observation_request_oid=1)[0]
        visits = cheops.get_visit_from_observation(observation)

        assert len(visits) > 0
        assert visits[0]['observation_request_oid'] == 1
        assert visits[0]['visit_id'] is not None

    def test_get_products_from_coordinates(self):
        products = cheops.get_products_from_targets_or_coordinates(coordinates='116.3289575 28.0261988888889')

        assert len(products) > 0
        assert ('CH_PR300050_TG000101_TU2020-03-10T05-00-00_EXT_PRE_StarCatalogue-OBSID0001015985_V0300.fits'
                in products['filename'].value)

    def test_get_products_from_observation(self):
        products = cheops.get_products_from_observation(observation=1)

        assert len(products) > 0
        assert ('CH_PR300050_TG000101_TU2020-03-10T05-05-59_SCI_COR_Lightcurve-R40_V0300.fits'
                in products['filename'].value)

    def test_get_products_from_visit(self):
        products = cheops.get_products_from_visit(visit=300050000101)

        assert len(products) > 0
        assert ('CH_PR300050_TG000101_TU2020-03-10T05-00-00_EXT_PRE_StarCatalogue-OBSID0001015985_V0300.fits'
                in products['filename'].value)

        products = cheops.get_products_from_visit(visit=300050000101, level='L2')

        assert len(products) > 0
        assert ('CH_PR300050_TG000101_TU2020-03-10T05-05-59_SCI_COR_Lightcurve-DEFAULT_V0300.fits'
                in products['filename'].value)

    def test_get_products_from_program(self):
        products = cheops.get_products_from_program(program_key='PR300050')

        assert len(products) > 0
        assert ('CH_PR300050_TG000101_TU2020-03-10T05-05-59_SCI_COR_Lightcurve-R34_V0300.fits'
                in products['filename'].value)
