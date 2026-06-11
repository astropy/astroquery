# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
===========================
ESO Astroquery Module tests
===========================

European Southern Observatory (ESO)

"""

import os

import astropy.io.ascii
import pytest
from astropy.table import Table

from ...eso import Eso
from ...eso import core as eso_core
from ...eso.utils import _UserParams

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
EXPECTED_MAXREC = 1000
MONKEYPATCH_TABLE_LENGTH = 50


def data_path(filename):
    return os.path.join(DATA_DIR, filename)


DATA_FILES = {
    "ADQL": {
        "SELECT table_name FROM TAP_SCHEMA.tables "
        "WHERE schema_name='safcat' "
        "AND cat_id IN ( "
        "SELECT t1.cat_id "
        "FROM TAP_SCHEMA.tables t1 "
        "LEFT JOIN TAP_SCHEMA.tables t2 ON (t1.title = t2.title AND t1.version < t2.version) "
        "WHERE t2.title IS NULL) ORDER BY table_name": "query_list_catalogs_latest_versions.csv",
        "SELECT table_name FROM TAP_SCHEMA.tables "
        "WHERE schema_name='safcat' ORDER BY table_name": "query_list_catalogs_all_versions.csv",
        "select * from safcat.KiDS_DR4_1_ugriZYJHKs_cat_fits": "kids_dr4_sample.csv",
    }
}

catalog_list = [
    "AMBRE_V1",
    "ATLASGAL_V1",
    "COSMOS2015_Laigle_v1_1b_latestV7_fits_V1",
    "EREBOS_cat_fits_V1",
    "EREBOS_RV_cat_fits_V1",
    "GOODS_FORS2_V1",
    "GOODS_ISAAC_V1",
    "GOODS_VIMOS_SPEC_V1",
    "HUGS_GOODSS_K_V1",
    "HUGS_UDS_K_V1",
    "HUGS_UDS_Y_V1",
    "KiDS_DR3_0_ugri_src_fits_V2",
    "KiDS_DR3_1_ugri_shear_fits_V1",
    "video_er3_zyjhks_CDFS_catMetaData_fits_V2",
    "video_er3_zyjhks_ES1_catMetaData_fits_V2",
    "video_er3_zyjhks_XMM_catMetaData_fits_V3",
    "VIPERS_SPECTRO_PDR2_ESO_fits_V1",
    "vphas_er3_ugr_1r_2ihavphas_catMetaData_fits_V3",
    "VVV_MPHOT_Ks_V2",
    "VVV_VAR_V2",
    "XQ_100_summary_fits_V1",
    "ZCOSMOS_V2",
    "gcav_rxcj2129_YJKs_cat_fits_V1",
    "gcav_rxcj1515_YJKs_cat_fits_V1",
    "VVV_VIRAC_PM_V1",
    "MW_BULGE_PSFPHOT_V1",
    "VANDELS_spec_redshift_V3",
    "VEXAS_AllWISE_V1",
    "VEXAS_21_V1",
    "VEXAS_XRAY_V1",
    "VEXAS_SPEC_V1",
    "viking_er5_zyjj_1j_2hks_catMetaData_fits_V4",
    "VHS_CAT_V3",
    "KiDS_DR4_1_ugriZYJHKs_cat_fits",
    "NGTS_SOURCE_CAT_V2",
    "NGTS_LC_V2",
    "VVV_bandMergedSourceCat_V3",
    "FDS_Sourcecatalog_V1",
    "VANDELS_SPECTRO_V4",
    "VEXAS_DESW_V2",
    "VEXAS_SMW_V2",
    "VEXAS_PSW_V2",
    "VEXAS_SPEC_GOOD_V2",
    "PESSTO_TRAN_CAT_V3",
    "GNS_catalog_V1",
    "AMBRE_UVES_V1",
    "AMBRE_HARPS_V1",
    "PESSTO_MPHOT_V3",
    "legac_V3",
    "GES_2021_VRAD",
    "VIDEO_CAT_DR5",
    "COSMOS2020_CLASSIC_V2",
    "COSMOS2020_FARMER_V2",
    "AMUSED_MAIN_SOURCE_CAT_V1",
    "GES_DR5_1_V1",
    "HARPS_RVCAT_V1",
    "INSPIRE_V1",
    "UVISTA_5band_cat_dr6_rc_v1_fits_V5",
    "VVVX_VIRAC_V2_SOURCES",
    "VVVX_VIRAC_V2_REJECTED_SOURCES",
    "VVVX_VIRAC_V2_OBS",
    "VVVX_VIRAC_V2_LC",
    "VVVX_VIRAC_V2_REJECTED_LC",
    "KiDS_DR5_0_ugriZYJHKs_cat_fits",
    "PHANGS_DR1_NebCat",
    "atlas_er5_ugriz",
    "vmc_dr7_ksjy_V6",
    "vmc_dr7_mPhotJ_V6",
    "vmc_dr7_mPhotKs_V6",
    "vmc_dr7_mPhotY_V6",
    "vmc_dr7_yjks_rrLy_V2",
    "vmc_dr7_yjks_agbVar_V1",
    "vmc_dr7_yjks_lpvVar_V1",
    "vmc_dr7_yjks_eclBinVar_V3",
    "vmc_dr7_yjks_chephVar_V4",
    "vmc_dr7_yjks_ysoVar_V1",
    "vmc_dr7_yjks_qsos_V1",
    "vmc_dr7_yjks_extYKs_V1",
    "vmc_dr7_yjks_MlClass_V1",
    "vmc_dr7_yjks_extJKs_V1",
    "vmc_dr7_yjks_pm_V1",
    "vmc_dr7_yjks_psfSrc_V5",
    "vmc_dr7_yjks_back_V1",
    "vmc_dr7_yjks_varCat_V3",
]

catalog_list_all = [
    "AMBRE_V1",
    "atlas_er3_ugriz_catMetaData_fits_V2",
    "ATLASGAL_V1",
    "COSMOS2015_Laigle_v1_1b_latestV7_fits_V1",
    "EREBOS_cat_fits_V1",
    "EREBOS_RV_cat_fits_V1",
    "GES_iDR4_PIII2016_catalog_v3_fits_V2",
    "GOODS_FORS2_V1",
    "GOODS_ISAAC_V1",
    "GOODS_VIMOS_SPEC_V1",
    "HUGS_GOODSS_K_V1",
    "HUGS_UDS_K_V1",
    "HUGS_UDS_Y_V1",
    "KiDS_DR3_0_ugri_src_fits_V2",
    "KiDS_DR3_1_ugri_shear_fits_V1",
    "legac_DR1_fits_V1",
    "legac_DR2_fits_V2",
    "PESSTO_TRAN_CAT_fits_V2",
    "PESSTO_MPHOT_fits_V2",
    "UltraVISTA_V3",
    "VANDELS_META_SPECTRO_fits_V1",
    "VHS_CAT_V2",
    "video_er3_zyjhks_CDFS_catMetaData_fits_V2",
    "video_er3_zyjhks_ES1_catMetaData_fits_V2",
    "video_er3_zyjhks_XMM_catMetaData_fits_V3",
    "viking_er4_zyjj_1j_2hks_catMetaData_fits_V3",
    "VIPERS_SPECTRO_PDR2_ESO_fits_V1",
    "vmc_er4_ksjy_catMetaData_fits_V3",
    "vmc_er4_j_mPhotMetaData_fits_V3",
    "vmc_er4_ks_mPhotMetaData_fits_V3",
    "vmc_er4_y_mPhotMetaData_fits_V3",
    "vmc_er4_yjks_cepheidCatMetaData_fits_V3",
    "vmc_er4_yjks_eclBinCatMetaData_fits_V2",
    "vmc_er4_yjks_psfCatMetaData_fits_V2",
    "vmc_er4_yjks_rrLyrCatMetaData_fits_V1",
    "vphas_er3_ugr_1r_2ihavphas_catMetaData_fits_V3",
    "VVV_CAT_V2",
    "VVV_MPHOT_Ks_V2",
    "VVV_VAR_V2",
    "XQ_100_summary_fits_V1",
    "ZCOSMOS_V2",
    "VANDELS_META_SPECTRO_fits_V2",
    "gcav_rxcj2129_YJKs_cat_fits_V1",
    "gcav_rxcj1515_YJKs_cat_fits_V1",
    "KiDS_DR4_0_ugriZYJHKs_cat_fits_V3",
    "UVISTA_5band_cat_dr4_rc_v2_fits_V3",
    "atlas_er4_ugriz_catMetaData_fits_V3",
    "VVV_VIRAC_PM_V1",
    "NGTS_SOURCE_catalog_fits_V1",
    "NGTS_LC_catalog_fits_V1",
    "MW_BULGE_PSFPHOT_V1",
    "VANDELS_spec_redshift_V3",
    "VEXAS_AllWISE_V1",
    "VEXAS_SMW_V1",
    "VEXAS_21_V1",
    "VEXAS_PS1W_V1",
    "VEXAS_XRAY_V1",
    "VEXAS_SPEC_V1",
    "VEXAS_DESW_V1",
    "viking_er5_zyjj_1j_2hks_catMetaData_fits_V4",
    "VHS_CAT_V3",
    "KiDS_DR4_1_ugriZYJHKs_cat_fits",
    "vmc_dr5_sourceCat_yjks_V4",
    "vmc_dr5_var_yjKs_V1",
    "vmc_dr5_mPhotY_V4",
    "vmc_dr5_mPhotJ_V4",
    "vmc_dr5_mPhotKs_V4",
    "vmc_dr5_psf_yjks_V3",
    "NGTS_SOURCE_CAT_V2",
    "NGTS_LC_V2",
    "VVV_bandMergedSourceCat_V3",
    "FDS_Sourcecatalog_V1",
    "VANDELS_SPECTRO_V4",
    "VEXAS_DESW_V2",
    "VEXAS_SMW_V2",
    "VEXAS_PSW_V2",
    "VEXAS_SPEC_GOOD_V2",
    "PESSTO_TRAN_CAT_V3",
    "GNS_catalog_V1",
    "AMBRE_UVES_V1",
    "AMBRE_HARPS_V1",
    "PESSTO_MPHOT_V3",
    "legac_V3",
    "GES_2021_VRAD",
    "VIDEO_CAT_DR5",
    "GES_DR5",
    "COSMOS2020_CLASSIC_V2",
    "COSMOS2020_FARMER_V1",
    "vmc_dr6_yjks_varCat_V2",
    "vmc_dr6_yjks_psf_V4",
    "vmc_dr6_ksjy_V5",
    "vmc_dr6_mPhotJ_V5",
    "vmc_dr6_mPhotKs_V5",
    "vmc_dr6_mPhotY_V5",
    "COSMOS2020_FARMER_V2",
    "AMUSED_MAIN_SOURCE_CAT_V1",
    "UVISTA_5band_cat_dr5_rc_v1_fits_V4",
    "GES_DR5_1_V1",
    "HARPS_RVCAT_V1",
    "INSPIRE_V1",
    "UVISTA_5band_cat_dr6_rc_v1_fits_V5",
    "VVVX_VIRAC_V2_SOURCES",
    "VVVX_VIRAC_V2_REJECTED_SOURCES",
    "VVVX_VIRAC_V2_OBS",
    "VVVX_VIRAC_V2_LC",
    "VVVX_VIRAC_V2_REJECTED_LC",
    "KiDS_DR5_0_ugriZYJHKs_cat_fits",
    "PHANGS_DR1_NebCat",
    "atlas_er5_ugriz",
    "vmc_dr7_ksjy_V6",
    "vmc_dr7_mPhotJ_V6",
    "vmc_dr7_mPhotKs_V6",
    "vmc_dr7_mPhotY_V6",
    "vmc_dr7_yjks_rrLy_V2",
    "vmc_dr7_yjks_agbVar_V1",
    "vmc_dr7_yjks_lpvVar_V1",
    "vmc_dr7_yjks_eclBinVar_V3",
    "vmc_dr7_yjks_chephVar_V4",
    "vmc_dr7_yjks_ysoVar_V1",
    "vmc_dr7_yjks_qsos_V1",
    "vmc_dr7_yjks_extYKs_V1",
    "vmc_dr7_yjks_MlClass_V1",
    "vmc_dr7_yjks_extJKs_V1",
    "vmc_dr7_yjks_pm_V1",
    "vmc_dr7_yjks_psfSrc_V5",
    "vmc_dr7_yjks_back_V1",
    "vmc_dr7_yjks_varCat_V3",
]


def monkey_tap(query, **kwargs):
    _ = kwargs
    table_file = data_path(DATA_FILES["ADQL"][query])
    table = astropy.io.ascii.read(
        table_file, format="csv", header_start=0, data_start=1
    )
    return table


# These catalogue TAP tests are deliberately offline. They cover TAP_CAT
# endpoint routing and metadata compatibility without contacting the ESO archive.
@pytest.mark.parametrize("table_name, expected", [
    ("safcat.KiDS_DR4_1_ugriZYJHKs_cat_fits", True),
    ("KiDS_DR4_1_ugriZYJHKs_cat_fits", False),
])
def test_tap_cat_table_names_have_schema_prefix(monkeypatch, table_name, expected):
    eso = Eso()
    calls = []

    def fake_query_tap(query, *, tap_endpoint):
        calls.append((query, tap_endpoint))
        return Table({"table_name": [table_name]})

    # TAP_CAT can expose table names with or without the schema prefix depending
    # on TAP version, so this helper decides which query shape to use later.
    monkeypatch.setattr(eso, "query_tap", fake_query_tap)

    result = eso._tap_cat_table_names_have_schema_prefix(tap_endpoint="tap_cat")

    assert result is expected
    assert calls == [("select top 1 table_name from TAP_SCHEMA.tables", "tap_cat")]


@pytest.mark.parametrize("authenticated", [False, True])
def test_tap_uses_catalog_endpoint(monkeypatch, authenticated):
    eso = Eso()
    calls = []

    class FakeTAPService:
        def __init__(self, url, session=None):
            calls.append((url, session))

    # TAPService is monkeypatched so this verifies TAP_CAT endpoint/session
    # selection without opening a real pyvo connection to the ESO archive.
    monkeypatch.setattr(eso_core, "TAPService", FakeTAPService)
    monkeypatch.setattr(eso, "authenticated", lambda: True)
    monkeypatch.setattr(eso, "_get_auth_header", lambda: {"Authorization": "Bearer token"})

    eso.tap(authenticated=authenticated, tap_endpoint="tap_cat")

    expected_session = eso._session if authenticated else None
    assert calls == [(eso._tap_url("tap_cat"), expected_session)]


def test_query_tap_passes_catalog_endpoint_to_tap_and_retriever(monkeypatch):
    eso = Eso()
    fake_tap_service = object()
    fake_table = Table({"col": [1]})
    calls = []

    def fake_tap(authenticated=False, *, tap_endpoint="tap_obs"):
        calls.append(("tap", authenticated, tap_endpoint))
        return fake_tap_service

    def fake_retrieve(query, tap_service):
        calls.append(("retrieve", query, tap_service))
        return fake_table

    # query_tap is the free-ADQL entry point for catalogue queries, so it must
    # preserve tap_endpoint="tap_cat" down to the pyvo retrieval helper.
    monkeypatch.setattr(eso, "tap", fake_tap)
    monkeypatch.setattr(eso, "_try_retrieve_pyvo_table", fake_retrieve)

    result = eso.query_tap("select 1", authenticated=True, tap_endpoint="tap_cat")

    assert result is fake_table
    assert calls == [
        ("tap", True, "tap_cat"),
        ("retrieve", "select 1", fake_tap_service),
    ]


def test_columns_table_uses_tap_cat_metadata_query_without_schema_prefix(monkeypatch):
    eso = Eso()
    calls = []

    def fake_query_tap(query, *, tap_endpoint):
        calls.append((query, tap_endpoint))
        return Table({"column_name": ["ID"]})

    # Some TAP_CAT deployments list table names without "safcat.". When that is
    # detected, the helper strips the prefix before querying TAP_SCHEMA.columns.
    monkeypatch.setattr(eso, "_tap_cat_table_names_have_schema_prefix",
                        lambda *, tap_endpoint: False)
    monkeypatch.setattr(eso, "query_tap", fake_query_tap)

    result = eso._columns_table(
        "safcat.KiDS_DR4_1_ugriZYJHKs_cat_fits",
        tap_endpoint="tap_cat",
    )

    assert result["column_name"][0] == "ID"
    assert calls == [(
        "select column_name, datatype, unit, ucd "
        "from TAP_SCHEMA.columns "
        "where table_name = 'KiDS_DR4_1_ugriZYJHKs_cat_fits'",
        "tap_cat",
    )]


def test_list_column_uses_catalog_endpoint_for_help_and_count(monkeypatch):
    eso = Eso()
    calls = []

    def fake_columns_table(table_name, *, tap_endpoint):
        calls.append(("columns", table_name, tap_endpoint))
        return Table({"column_name": ["ID"], "datatype": ["int"], "unit": [""], "ucd": [""]})

    def fake_query_tap(query, *, tap_endpoint):
        calls.append(("count", query, tap_endpoint))
        return Table({"count": [7]})

    # list/help output needs two TAP calls: one for column metadata and one for
    # row count. Both must use the catalogue endpoint when helping catalogues.
    monkeypatch.setattr(eso, "_columns_table", fake_columns_table)
    monkeypatch.setattr(eso, "query_tap", fake_query_tap)

    eso._list_column("safcat.KiDS_DR4_1_ugriZYJHKs_cat_fits", tap_endpoint="tap_cat")

    assert calls == [
        ("columns", "safcat.KiDS_DR4_1_ugriZYJHKs_cat_fits", "tap_cat"),
        ("count", "select count(*) from safcat.KiDS_DR4_1_ugriZYJHKs_cat_fits", "tap_cat"),
    ]


def test_query_on_allowed_values_catalog_help_uses_catalog_endpoint(monkeypatch):
    eso = Eso()
    calls = []

    def fake_list_column(table_name, *, tap_endpoint):
        calls.append((table_name, tap_endpoint))

    # help=True should print/list valid catalogue columns and stop there; it
    # should not build or submit a data query to TAP.
    monkeypatch.setattr(eso, "_list_column", fake_list_column)
    monkeypatch.setattr(eso, "query_tap", lambda *args, **kwargs: pytest.fail("unexpected TAP query"))

    result = eso._query_on_allowed_values(_UserParams(
        table_name="safcat.KiDS_DR4_1_ugriZYJHKs_cat_fits",
        print_help=True,
        tap_endpoint="tap_cat",
    ))

    assert result is None
    assert calls == [("safcat.KiDS_DR4_1_ugriZYJHKs_cat_fits", "tap_cat")]


def test_query_on_allowed_values_catalog_payload_does_not_query_tap(monkeypatch):
    eso = Eso()

    # get_query_payload=True is a dry-run mode for inspecting catalogue ADQL, so
    # the method should return the generated query without contacting TAP_CAT.
    monkeypatch.setattr(eso, "query_tap", lambda *args, **kwargs: pytest.fail("unexpected TAP query"))

    result = eso._query_on_allowed_values(_UserParams(
        table_name="safcat.KiDS_DR4_1_ugriZYJHKs_cat_fits",
        columns="ID",
        column_filters={"MAG_AUTO": "< 10"},
        get_query_payload=True,
        tap_endpoint="tap_cat",
    ))

    assert result == "select ID from safcat.KiDS_DR4_1_ugriZYJHKs_cat_fits where MAG_AUTO < 10"


def test_list_catalogs_latest_versions(monkeypatch):
    eso = Eso()
    monkeypatch.setattr(eso, "query_tap", monkey_tap)
    saved_list = eso.list_catalogs(all_versions=False)
    assert isinstance(saved_list, list)
    assert len(saved_list) >= len(catalog_list)


def test_list_catalogs_all_versions(monkeypatch):
    eso = Eso()
    monkeypatch.setattr(eso, "query_tap", monkey_tap)
    saved_list = eso.list_catalogs(all_versions=True)
    assert isinstance(saved_list, list)
    assert len(saved_list) >= len(catalog_list_all)


def test_query_catalogs(monkeypatch):
    eso = Eso()
    eso.ROW_LIMIT = 5
    monkeypatch.setattr(eso, "query_tap", monkey_tap)
    result = eso.query_catalog("KiDS_DR4_1_ugriZYJHKs_cat_fits")
    assert isinstance(result, Table)
    assert len(result) <= 5


# These catalogue wrapper tests document the non-network paths. They verify
# query dry-runs and help routing without asking TAP_CAT for live data.
def test_query_catalog_get_query_payload_prefixes_catalog_schema(monkeypatch):
    eso = Eso()

    # get_query_payload=True is a dry-run mode. It should add the safcat schema
    # prefix for catalogue tables and return ADQL without making a TAP request.
    monkeypatch.setattr(eso, "query_tap", lambda *args, **kwargs: pytest.fail("unexpected TAP query"))

    query = eso.query_catalog(
        "KiDS_DR4_1_ugriZYJHKs_cat_fits",
        columns="ID",
        column_filters={"MAG_AUTO": "< 10"},
        get_query_payload=True,
    )

    assert query == (
        "select ID from safcat.KiDS_DR4_1_ugriZYJHKs_cat_fits "
        "where MAG_AUTO < 10"
    )


def test_query_catalog_help_uses_catalog_endpoint(monkeypatch):
    eso = Eso()
    calls = []

    def fake_list_column(table_name, *, tap_endpoint):
        calls.append((table_name, tap_endpoint))

    # help=True should route through the catalogue TAP endpoint so column help
    # describes catalogue columns rather than observation-table columns.
    monkeypatch.setattr(eso, "_list_column", fake_list_column)
    monkeypatch.setattr(eso, "query_tap", lambda *args, **kwargs: pytest.fail("unexpected TAP query"))

    result = eso.query_catalog("KiDS_DR4_1_ugriZYJHKs_cat_fits", help=True)

    assert result is None
    assert calls == [("safcat.KiDS_DR4_1_ugriZYJHKs_cat_fits", "tap_cat")]
