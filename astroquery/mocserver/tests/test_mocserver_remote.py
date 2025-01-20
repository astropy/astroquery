# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest

from astropy.table import Table
from astropy.time import Time

try:
    from mocpy import MOC, STMOC, TimeMOC

    HAS_MOCPY = True
except ImportError:
    HAS_MOCPY = False

from ..core import MOCServer


@pytest.mark.remote_data
@pytest.mark.skipif(not HAS_MOCPY, reason="mocpy is required")
class TestMOCServerRemote:
    # test of MAXREC payload
    @pytest.mark.parametrize("max_rec", [3, 10])
    def test_max_rec_param(self, max_rec):
        result = MOCServer.query_region(
            region=MOC.from_str("0/0-11"),
            max_rec=max_rec,
            get_query_payload=False,
            fields=["ID"],
        )
        assert max_rec == len(result)

    # test of field_l when retrieving dataset records
    @pytest.mark.parametrize(
        "field_l",
        [
            ["ID"],
            ["data_ucd", "vizier_popularity", "ID"],
        ],
    )
    def test_field_l_param(self, field_l):
        table = MOCServer.query_region(
            region=MOC.from_str("20/0"), fields=field_l, get_query_payload=False
        )
        assert isinstance(table, Table)
        assert set(table.colnames).issubset(set(field_l))

    # test of moc_order payload
    @pytest.mark.parametrize("moc_order", [1, 3])
    def test_moc_order_param(self, moc_order):
        moc_region = MOC.from_str("10/0-9")
        result = MOCServer.query_region(
            region=moc_region,
            return_moc=True,
            max_norder=moc_order,
            intersect="enclosed",
        )
        assert isinstance(result, MOC)
        assert result.max_order == moc_order

    def test_stmoc_as_outputs(self):
        # chose a dataset with a MOC with few cells
        stmoc = MOCServer.query_region(
            criteria="ID=CDS/J/AJ/157/109/table1", return_moc="stmoc"
        )
        assert isinstance(stmoc, STMOC)

    def test_temporal_mocs_as_inputs(self):
        tmoc = TimeMOC.from_str("11/1")
        result = MOCServer.query_region(
            region=tmoc,
            fields=["t_min"],
            max_rec=100,
            criteria="dataproduct_type='image'&&t_min=*",
        )
        min_time_result = Time(result["t_min"].value, format="mjd")
        # the resulting datasets should only have starting times after the
        # beginning of the T-MOC
        assert all(tmoc.min_time < min_time_result)

    def test_no_region(self):
        result = MOCServer.query_region(
            criteria="moc_sky_fraction>0.5&&moc_sky_fraction=*",
            fields=["ID", "moc_sky_fraction"],
            max_rec=100,
        )
        assert all(result["moc_sky_fraction"] > 0.5)

    def test_query_hips(self):
        result = MOCServer.query_hips(coordinate_system="venus", fields="hips_frame")
        assert all(result["hips_frame"] == "venus")

    def test_list_fields(self):
        # with keyword
        moc_fields = MOCServer.list_fields("moc")
        assert all("moc" in field for field in moc_fields["field_name"])
        type_moc = moc_fields[moc_fields["field_name"] == "moc_type"]
        # this was the occurrence number in 2024, can only be higher in the future
        assert type_moc["occurrence"][0] >= 34000
        # without keyword
        all_fields = MOCServer.list_fields()
        assert len(all_fields) > 100
        assert "ID" in list(all_fields["field_name"])
