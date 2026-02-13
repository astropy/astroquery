# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
===========================
ESO Astroquery Module tests
===========================

European Southern Observatory (ESO)

"""

import os

import astropy.io.ascii
from astropy.table import Table

from ...eso import Eso

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
EXPECTED_MAXREC = 1000
MONKEYPATCH_TABLE_LENGTH = 50


def data_path(filename):
    return os.path.join(DATA_DIR, filename)


DATA_FILES = {
    "ADQL": {
        "SELECT table_name FROM TAP_SCHEMA.tables as ref "
        "LEFT OUTER JOIN TAP_SCHEMA.keys AS k ON ref.table_name = k.from_table "
        "LEFT OUTER JOIN TAP_SCHEMA.key_columns AS kc ON k.key_id = kc.key_id "
        "WHERE schema_name='safcat' "
        "AND cat_id IN ( "
        "SELECT t1.cat_id "
        "FROM TAP_SCHEMA.tables t1 "
        "LEFT JOIN TAP_SCHEMA.tables t2 ON (t1.title = t2.title AND t1.version < t2.version) "
        "WHERE t2.title IS NULL)": "query_list_catalogues_latest_versions.csv",
        "SELECT table_name FROM TAP_SCHEMA.tables as ref "
        "LEFT OUTER JOIN TAP_SCHEMA.keys AS k ON ref.table_name = k.from_table "
        "LEFT OUTER JOIN TAP_SCHEMA.key_columns AS kc ON k.key_id = kc.key_id "
        "WHERE schema_name='safcat'": "query_list_catalogues_all_versions.csv",
        "SELECT * FROM safcat.KiDS_DR4_1_ugriZYJHKs_cat_fits": "kids_dr4_sample.csv",
    }
}

catalogue_list = [
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
    "FDS_SourceCatalogue_V1",
    "VANDELS_SPECTRO_V4",
    "VEXAS_DESW_V2",
    "VEXAS_SMW_V2",
    "VEXAS_PSW_V2",
    "VEXAS_SPEC_GOOD_V2",
    "PESSTO_TRAN_CAT_V3",
    "GNS_catalogue_V1",
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
    "VVVX_VIRAC_V2_LC",
    "VVVX_VIRAC_V2_REJECTED_LC",
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

catalogue_list_all = [
    "AMBRE_V1",
    "atlas_er3_ugriz_catMetaData_fits_V2",
    "ATLASGAL_V1",
    "COSMOS2015_Laigle_v1_1b_latestV7_fits_V1",
    "EREBOS_cat_fits_V1",
    "EREBOS_RV_cat_fits_V1",
    "GES_iDR4_PIII2016_Catalogue_v3_fits_V2",
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
    "NGTS_SOURCE_CATALOGUE_fits_V1",
    "NGTS_LC_CATALOGUE_fits_V1",
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
    "FDS_SourceCatalogue_V1",
    "VANDELS_SPECTRO_V4",
    "VEXAS_DESW_V2",
    "VEXAS_SMW_V2",
    "VEXAS_PSW_V2",
    "VEXAS_SPEC_GOOD_V2",
    "PESSTO_TRAN_CAT_V3",
    "GNS_catalogue_V1",
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
    "VVVX_VIRAC_V2_LC",
    "VVVX_VIRAC_V2_REJECTED_LC",
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


def test_list_catalogues_latest_versions(monkeypatch):
    eso = Eso()
    monkeypatch.setattr(eso, "query_tap", monkey_tap)
    saved_list = eso.list_catalogues(all_versions=False)
    assert isinstance(saved_list, list)
    assert set(catalogue_list) <= set(saved_list)


def test_list_catalogues_all_versions(monkeypatch):
    eso = Eso()
    monkeypatch.setattr(eso, "query_tap", monkey_tap)
    saved_list = eso.list_catalogues(all_versions=True)
    assert isinstance(saved_list, list)
    assert len(saved_list) >= len(catalogue_list_all)


def test_query_catalogues(monkeypatch):
    eso = Eso()
    monkeypatch.setattr(eso, "query_tap", monkey_tap)
    result = eso.query_catalogue("KiDS_DR4_1_ugriZYJHKs_cat_fits", ROW_LIMIT=5)
    assert isinstance(result, Table)
    assert len(result) <= 5
