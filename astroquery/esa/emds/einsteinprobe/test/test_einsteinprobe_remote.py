# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
==========================================
EinsteinProbe (EPSA) tests
==========================================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import pytest
import os
import tempfile
from pyvo import DALQueryError
from astroquery.esa.emds.einsteinprobe import EinsteinProbeClass


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def close_file(file):
    file.close()


def close_files(file_list):
    for file in file_list:
        close_file(file['fits'])


def create_temp_folder():
    return tempfile.TemporaryDirectory()


@pytest.mark.remote_data
class TestEmdsRemote:

    def test_get_tables(self):
        epsa = EinsteinProbeClass()
        names = epsa.get_tables(only_names=True)

        assert isinstance(names, list)
        assert len(names) > 0
        assert all(isinstance(n, str) for n in names)
        assert "einsteinprobe.obscore_extended" in [n.lower() for n in names]

    def test_get_table(self):
        epsa = EinsteinProbeClass()

        obscore = epsa.get_table('einsteinprobe.obscore_extended')
        assert obscore is not None
        assert hasattr(obscore, "columns")
        assert len(obscore.columns) > 0

        # BaseParam objects expose the column name in `.name`
        colnames = {c.name for c in obscore.columns}
        for expected in {"obs_id", "s_ra", "s_dec", "obs_collection"}:
            assert expected in colnames

    def test_query_tap(self):
        epsa = EinsteinProbeClass()

        # Query an existing table
        result = epsa.query_tap("SELECT TOP 10 obs_id, s_ra, s_dec FROM einsteinprobe.obscore_extended")
        assert result is not None
        assert len(result) > 0
        assert {"obs_id", "s_ra", "s_dec"}.issubset(set(result.colnames))

        # Query a table that does not exist
        with pytest.raises(DALQueryError) as err:
            epsa.query_tap("SELECT TOP 10 * FROM schema.table")
        assert "Unknown table" in str(err.value) or "does not exist" in str(err.value)

        # Store the result in a file
        temp_folder = create_temp_folder()
        filename = os.path.join(temp_folder.name, "query_tap.votable")
        epsa.query_tap("SELECT TOP 10 obs_id FROM ivoa.ObsCore", output_file=filename)
        assert os.path.exists(filename)

        temp_folder.cleanup()

    def test_get_observations_metadata(self):
        epsa = EinsteinProbeClass()
        meta = epsa.get_observations(get_metadata=True)

        assert meta is not None
        assert len(meta) > 0

        expected_cols = {"Column", "Description", "Unit", "Data Type", "UCD", "UType"}
        assert expected_cols.issubset(set(meta.colnames))

        # Check that some ObsCore columns appear in the metadata
        available = set(meta["Column"])
        assert {"s_ra", "s_dec"}.issubset(available)

    def test_get_observations_cone_coordinates(self):
        epsa = EinsteinProbeClass()

        results = epsa.get_observations(
            coordinates="81.1238 17.4175",
            radius=0.1,
            columns=["obs_id", "s_ra", "s_dec"],
        )

        assert results is not None
        assert {"obs_id", "s_ra", "s_dec"}.issubset(set(results.colnames))

    def test_get_observations_cone_target_name(self):
        epsa = EinsteinProbeClass()

        results = epsa.get_observations(
            target_name="V1589 Cyg",
            radius=0.1,
            columns=["obs_id", "s_ra", "s_dec", "target_name"],
        )

        assert results is not None
        assert {"obs_id", "s_ra", "s_dec", "target_name"}.issubset(set(results.colnames))

    def test_get_observations_filters(self):
        epsa = EinsteinProbeClass()

        # Discover one valid obs_collection value
        missions = epsa.query_tap(
            "SELECT DISTINCT TOP 10 obs_collection FROM ivoa.ObsCore WHERE obs_collection IS NOT NULL"
        )
        assert len(missions) > 0
        obs_collection = missions["obs_collection"][0]

        # Discover one valid instrument_name for that collection
        instruments = epsa.query_tap(
            "SELECT DISTINCT TOP 10 instrument_name "
            f"FROM ivoa.ObsCore WHERE obs_collection = '{obs_collection}' AND instrument_name IS NOT NULL"
        )
        instrument_name = instruments["instrument_name"][0] if len(instruments) > 0 else None

        # Run the filtered search
        filters = {"obs_collection": obs_collection}
        if instrument_name is not None:
            filters["instrument_name"] = instrument_name

        results = epsa.get_observations(
            columns=["obs_id", "obs_collection", "instrument_name", "dataproduct_type"],
            **filters,
        )

        assert results is not None
        assert {"obs_id", "obs_collection", "instrument_name", "dataproduct_type"}.issubset(
            set(results.colnames)
        )

        # If results exist, validate they match filters
        if len(results) > 0:
            assert set(results["obs_collection"]) == {obs_collection}
            if instrument_name is not None:
                assert set(results["instrument_name"]) == {instrument_name}

    def test_get_observations_output_file(self):
        epsa = EinsteinProbeClass()

        temp_folder = create_temp_folder()
        filename = os.path.join(temp_folder.name, "get_observations.votable")

        results = epsa.get_observations(
            coordinates="81.1238 17.4175",
            radius=0.1,
            columns=["obs_id", "s_ra", "s_dec"],
            output_file=filename,
        )

        assert os.path.exists(filename)
        assert results is not None
        assert {"obs_id", "s_ra", "s_dec"}.issubset(set(results.colnames))

        temp_folder.cleanup()

    def test_get_products(self):
        epsa = EinsteinProbeClass()

        table = epsa.get_products()

        assert table is not None
        assert len(table) > 0

        # Mandatory columns for download
        assert "filename" in table.colnames
        assert "filepath" in table.colnames

    def test_download_product(self, tmp_path):
        epsa = EinsteinProbeClass()

        table = epsa.get_products()
        assert len(table) > 0

        filename = table["filename"][0]

        local_path = epsa.download_product(
            filename=filename,
            path=str(tmp_path),
            output_filename=filename,
            verbose=True,
        )

        assert os.path.exists(local_path)
        assert os.path.getsize(local_path) > 0
