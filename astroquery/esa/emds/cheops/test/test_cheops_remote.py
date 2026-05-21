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


@pytest.mark.remote_data
class TestCheopsRemote:

    def test_get_tables(self):
        cheops = CheopsClass()
        names = cheops.get_tables(only_names=True)

        assert isinstance(names, list)
        assert len(names) > 0
        assert all(isinstance(n, str) for n in names)
        assert cheops.conf.CHEOPS_DATA_PRODUCT_TABLE in [n.lower() for n in names]

    def test_get_table(self):
        cheops = CheopsClass()

        observation_request_table = cheops.get_table("cheops.observation_request")

        assert observation_request_table is not None
        assert hasattr(observation_request_table, "columns")
        assert len(observation_request_table.columns) > 0

        # BaseParam objects expose the column name in `.name`
        colnames = {c.name for c in observation_request_table.columns}
        for expected in {"obs_cat", "ra", "dec", "target_name"}:
            assert expected in colnames

    def test_query_tap(self):
        cheops = CheopsClass()

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
        cheops = CheopsClass()
        meta = cheops.get_observations(get_metadata=True)

        assert meta is not None
        assert len(meta) > 0

        expected_cols = {"Column", "Description", "Unit", "Data Type", "UCD", "UType"}
        assert expected_cols.issubset(set(meta.colnames))

        # Check that some columns appear in the metadata
        available = set(meta["Column"])
        assert {"ra", "dec"}.issubset(available)

    def test_get_observations_cone_coordinates(self):
        cheops = CheopsClass()
        results = cheops.get_observations(
            coordinates="81.1238 17.4175",
            radius=0.1,
            columns=["obs_cat", "ra", "dec"],
            async_job=True,
        )

        assert results is not None
        assert {"obs_cat", "ra", "dec"}.issubset(set(results.colnames))

    def test_get_observations_cone_target_name(self):
        cheops = CheopsClass()

        results = cheops.get_observations(
            target_name="V1589 Cyg",
            radius=0.1,
            columns=["obs_cat", "ra", "dec", "target_name"],
            output_format='votable'
        )

        assert results is not None
        assert {"obs_cat", "ra", "dec", "target_name"}.issubset(set(results.colnames))

    def test_get_observations_filters(self):
        cheops = CheopsClass()

        # Run the filtered search
        filters = { "request_id": 3000240001 }

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
        cheops = CheopsClass()

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

    def test_get_products_by_observation_id(self):
        cheops = CheopsClass()

        with pytest.raises(TypeError) as err:
           cheops.get_products()

        assert "Please use either observation_id or visit_id" in str(err.value)

        table = cheops.get_products(observation_id=2652014)

        assert table is not None
        assert len(table) > 0

        # Mandatory columns for download
        assert "filename" in table.colnames
        assert "filepath" in table.colnames

    def test_get_products_by_visit_id(self):
        cheops = CheopsClass()

        table = cheops.get_products(visit_id=250033000701)

        assert table is not None
        assert len(table) > 0

        table2 = cheops.get_products(observation_id=2652014, visit_id=250033000701)

        assert table2 is not None
        assert len(table2) > 0

        with pytest.raises(ValueError) as err:
            cheops.get_products(observation_id=2652065, visit_id=250033000701)

        assert "No data products can be found for CHEOPS" in str(err.value)

    def test_download_product(self, tmp_path):
        cheops = CheopsClass()

        filename = "CH_PR140061_TG000702_TU2023-08-26T00-32-10_SCI_COR_SubArray_V0300.fits"

        local_path = cheops.download_product(
            filename=filename,
            path=str(tmp_path),
            verbose=True
        )

        assert os.path.exists(local_path)
        assert os.path.getsize(local_path) > 0