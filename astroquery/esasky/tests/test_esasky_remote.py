# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
from pathlib import Path

import pytest
from astropy.io.fits.hdu.hdulist import HDUList

from astroquery.utils.commons import TableList
from astroquery.utils.tap.model.tapcolumn import TapColumn
from astroquery.utils.tap.model.taptable import TapTableMeta
from astroquery.esasky import ESASky


@pytest.mark.remote_data
class TestESASky:

    def test_esasky_query_ids_maps(self):
        result = ESASky.query_ids_maps(observation_ids=["lbsk03vbq", "ieag90010"], missions="HST-UV")
        assert isinstance(result, TableList)
        assert "lbsk03vbq" in result["HST-UV"].columns["observation_id"]
        assert "ieag90010" in result["HST-UV"].columns["observation_id"]

        result = ESASky.query_ids_maps(observation_ids="lbsk03vbq")
        assert isinstance(result, TableList)
        assert "lbsk03vbq" in result["HST-UV"].columns["observation_id"]

        result = ESASky.query_ids_maps(observation_ids=["lbsk03vbq", "ieag90010", "1342221275", "1342221848"],
                                       missions=["Herschel", "HST-UV"])
        assert isinstance(result, TableList)
        assert "lbsk03vbq" in result["HST-UV"].columns["observation_id"]
        assert "ieag90010" in result["HST-UV"].columns["observation_id"]
        assert "1342221275" in result["HERSCHEL"].columns["observation_id"]
        assert "1342221848" in result["HERSCHEL"].columns["observation_id"]

    def test_esasky_query_ids_catalogs(self):
        result = ESASky.query_ids_catalogs(source_ids=["2CXO J090341.1-322609", "2CXO J090353.8-322642"],
                                           catalogs="CHANDRA-SC2")
        assert isinstance(result, TableList)
        assert "2CXO J090341.1-322609" in result["CHANDRA-SC2"].columns["name"]
        assert "2CXO J090353.8-322642" in result["CHANDRA-SC2"].columns["name"]

        result = ESASky.query_ids_catalogs(source_ids=["2CXO J090341.1-322609",
                                                       "2CXO J090353.8-322642", "44899", "45057"],
                                           catalogs=["CHANDRA-SC2", "Hipparcos-2"])
        assert isinstance(result, TableList)
        assert "2CXO J090341.1-322609" in result["CHANDRA-SC2"].columns["name"]
        assert "2CXO J090353.8-322642" in result["CHANDRA-SC2"].columns["name"]
        assert "44899" in result["HIPPARCOS-2"].columns["name"]
        assert "45057" in result["HIPPARCOS-2"].columns["name"]

    def test_esasky_query_ids_spectra(self):
        result = ESASky.query_ids_spectra(observation_ids=["0001730501", "0011420101"], missions="XMM-NEWTON")
        assert isinstance(result, TableList)
        assert "0001730501" in result["XMM-NEWTON"].columns["observation_id"]
        assert "0011420101" in result["XMM-NEWTON"].columns["observation_id"]

        result = ESASky.query_ids_spectra(observation_ids="0001730501")
        assert isinstance(result, TableList)
        assert "0001730501" in result["XMM-NEWTON"].columns["observation_id"]

        result = ESASky.query_ids_spectra(observation_ids=["0001730501", "0011420101", "1342246640"],
                                          missions=["XMM-NEWTON", "Herschel"])

        assert isinstance(result, TableList)
        assert "0001730501" in result["XMM-NEWTON"].columns["observation_id"]
        assert "0011420101" in result["XMM-NEWTON"].columns["observation_id"]
        assert "1342246640" in result["HERSCHEL"].columns["observation_id"]

    @pytest.mark.parametrize("mission, obsid",
                             zip(["SUZAKU", "ISO-IR", "Chandra", "XMM-OM-OPTICAL",
                                  "XMM", "XMM-OM-UV", "HST-IR", "Herschel",
                                  "Spitzer", "HST-UV", "HST-OPTICAL", "INTEGRAL"],
                                 ["100001010", "01500403", "21171", "0852000101",
                                  "0851180201", "0851180201", "n3tr01c3q", "1342247257",
                                  "30002561-25100", "hst_07553_3h_wfpc2_f160bw_pc", "ocli05leq", "88600210001"]))
    def test_esasky_get_images_obs_id(self, tmp_path, mission, obsid):
        result = ESASky.get_images(observation_ids=obsid,
                                   missions=mission, download_dir=tmp_path)

        assert Path(tmp_path, mission.upper()).exists()
        if mission == "Herschel":
            assert isinstance(result[mission.upper()][0]["250"], HDUList)
            assert isinstance(result[mission.upper()][0]["350"], HDUList)
            assert isinstance(result[mission.upper()][0]["500"], HDUList)
        else:
            assert isinstance(result[mission.upper()][0], HDUList)
            for hdu_list in result[mission.upper()]:
                hdu_list.close()

    @pytest.mark.parametrize("mission, observation_id",
                             zip(["ISO-IR", "Chandra", "IUE", "XMM-NEWTON",
                                  "HST-IR", "Herschel", "HST-UV", "HST-OPTICAL"],
                                 ["02101201", "1005", "LWR13178", "0001730201",
                                  "ibh706cqq", "1342253595", "z1ax0102t", "oeik2s020"]))
    def test_esasky_get_spectra_obs_id(self, tmp_path, mission, observation_id):
        result = ESASky.get_spectra(observation_ids=observation_id,
                                    missions=mission, download_dir=tmp_path)

        assert Path(tmp_path, mission.upper()).exists()
        if mission == "Herschel":
            assert isinstance(result[mission.upper()]["1342253595"]["WBS"]["WBS-V_USB_4b"], HDUList)
            assert isinstance(result[mission.upper()]["1342253595"]["HRS"]["HRS-H_LSB_4b"], HDUList)
        else:
            assert isinstance(result[mission.upper()][0], HDUList)
            result[mission.upper()][0].close()

    def test_esasky_query_region_maps(self):
        result = ESASky.query_region_maps(position="M51", radius="5 arcmin")
        assert isinstance(result, TableList)

    def test_esasky_query_object_maps(self):
        result = ESASky.query_object_maps(position="M51")
        assert isinstance(result, TableList)

    @pytest.mark.bigdata
    @pytest.mark.parametrize("mission", ['XMM', 'Chandra', 'XMM-OM-OPTICAL',
                                         'ISO-IR', 'Herschel', 'Spitzer'])
    def test_esasky_get_images(self, tmp_path, mission):
        result = ESASky.get_images(position="M51", missions=mission, download_dir=tmp_path)
        assert tmp_path.stat().st_size

        if mission != "Herschel" and result:
            for hdu_list in result[mission.upper()]:
                hdu_list.close()

    @pytest.mark.bigdata
    def test_esasky_get_images_for_erosita(self, tmp_path):
        mission = 'eROSITA'
        result = ESASky.get_images(position="67.84 -61.44", missions=mission, download_dir=tmp_path)
        assert tmp_path.stat().st_size

        for hdu_list in result[mission.upper()]:
            hdu_list.close()

    @pytest.mark.bigdata
    @pytest.mark.parametrize('mission, position',
                             zip(['JWST-MID-IR', 'JWST-NEAR-IR'],
                                 ['340.50123388127435 -69.17904779241904', '225.6864099965157 -3.0315781490149467']))
    def test_esasky_get_images_jwst(self, tmp_path, mission, position):
        result = ESASky.get_images(position=position, missions=mission, download_dir=tmp_path)
        assert tmp_path.stat().st_size
        for hdu_list in result[mission.upper()]:
            hdu_list.close()

    @pytest.mark.bigdata
    def test_esasky_get_images_hst(self, tmp_path):
        ESASky.get_images(position="M11", radius="2.1 deg", missions="HST-UV",
                          download_dir=tmp_path)
        assert Path(tmp_path, "HST-UV").exists()

    def test_esasky_query_region_catalogs(self):
        result = ESASky.query_region_catalogs(position="M51", radius="5 arcmin")
        assert isinstance(result, TableList)

    def test_esasky_query_object_catalogs(self):
        result = ESASky.query_object_catalogs(position="M51")
        assert isinstance(result, TableList)

    def test_esasky_get_maps(self, tmp_path):
        mission = 'ISO-IR'
        file_path = Path(tmp_path, mission)

        all_maps = ESASky.query_object_maps(position="M51")
        iso_maps = ESASky.query_object_maps(position="M51", missions=mission)
        # Remove a few maps, so the other list will have downloadable ones, too
        iso_maps[mission].remove_rows([0, 1])
        result = ESASky.get_maps(iso_maps, download_dir=tmp_path)
        assert len(os.listdir(file_path)) == len(all_maps[mission]) - 2
        for hdu_list in result[mission]:
            hdu_list.close()

        iso_maps2 = dict({mission: all_maps[mission][:2]})
        result = ESASky.get_maps(iso_maps2, download_dir=tmp_path)
        assert len(os.listdir(file_path)) == len(all_maps[mission])
        for hdu_list in result[mission]:
            hdu_list.close()

    def test_esasky_query_region_spectra(self):
        result = ESASky.query_region_spectra(position="M51", radius="5 arcmin")
        assert isinstance(result, TableList)

    def test_esasky_query_object_spectra(self):
        result = ESASky.query_object_spectra(position="M51")
        assert isinstance(result, TableList)

    @pytest.mark.bigdata
    @pytest.mark.parametrize("mission", ["XMM-NEWTON", "Chandra", "IUE", "HST-UV",
                                         "HST-OPTICAL", "ISO-IR", "Herschel"])
    def test_esasky_get_spectra(self, tmp_path, mission):
        # Not all missions are tested here:
        # - HST-IR, JWST-MID-IR and CHEOPS have no data
        # - LAMOST does not support download
        # - JWST-NEAR-IR returns a zip file with many fits files in it, unsupported
        result = ESASky.get_spectra(position="M1", missions=mission, radius='15 arcsec', download_dir=tmp_path)
        assert Path(tmp_path, mission.upper()).exists()

        if mission != "Herschel":
            for hdu_list in result[mission.upper()]:
                hdu_list.close()

    def test_esasky_get_spectra_small(self, tmp_path):
        missions = ['HST-IR']

        ESASky.get_spectra(position="M1", radius="9arcmin", missions=missions,
                           download_dir=tmp_path)

        for mission in missions:
            assert Path(tmp_path, mission).exists()

    def test_esasky_get_spectra_from_table(self, tmp_path):
        mission = 'ISO-IR'
        file_path = Path(tmp_path, mission)

        all_spectra = ESASky.query_object_spectra(position="M51")
        iso_spectra = ESASky.query_object_spectra(position="M51", missions=mission)
        # Remove a few maps, so the other list will have downloadable ones, too
        iso_spectra[mission].remove_rows([0, 1])
        result = ESASky.get_spectra_from_table(query_table_list=iso_spectra, download_dir=tmp_path)
        for hdu_list in result[mission]:
            hdu_list.close()
        assert len(os.listdir(file_path)) == len(all_spectra[mission]) - 2

        iso_spectra2 = dict({mission: all_spectra[mission][:2]})
        result = ESASky.get_spectra_from_table(query_table_list=iso_spectra2, download_dir=tmp_path)
        for hdu_list in result[mission]:
            hdu_list.close()
        assert len(os.listdir(file_path)) == len(all_spectra[mission])

    def test_query(self):
        result = ESASky.query(query="SELECT * from observations.mv_v_esasky_xmm_om_uv_fdw")
        assert len(result) == 2000  # Default row limit is 2000

    def test_get_tables(self):
        table_names = ESASky.get_tables(only_names=True)
        assert len(table_names) > 70
        tables = ESASky.get_tables(only_names=False)
        assert isinstance(tables[0], TapTableMeta)
        assert len(table_names) == len(tables)

    def test_get_columns(self):
        column_names = ESASky.get_columns(table_name='observations.mv_v_esasky_xmm_om_uv_fdw', only_names=True)
        assert len(column_names) == 17

        columns = ESASky.get_columns(table_name='observations.mv_v_esasky_xmm_om_uv_fdw', only_names=False)
        assert isinstance(columns[0], TapColumn)
        assert len(column_names) == len(columns)

    def test_esasky_query_sso(self):
        result = ESASky.query_sso(sso_name="ceres")
        assert isinstance(result, TableList)
        assert "HST" in result.keys()
        assert "XMM" in result.keys()
        assert "HERSCHEL" in result.keys()
        assert len(result["HST"]) >= 176

        result = ESASky.query_sso(sso_name="ceres", missions="HST", row_limit=1)
        assert isinstance(result, TableList)
        assert "HST" in result.keys()
        assert "XMM" not in result.keys()
        assert "HERSCHEL" not in result.keys()
        assert len(result["HST"]) == 1

        result = ESASky.query_sso(sso_name="io", sso_type="SATELLITE", missions=["HST", "XMM"])
        assert isinstance(result, TableList)
        assert "HST" in result.keys()
        assert "XMM" in result.keys()
        assert "HERSCHEL" not in result.keys()

    def test_esasky_query_sso_ambiguous_name(self):
        with pytest.raises(ValueError) as err:
            ESASky.query_sso(sso_name="io")
            assert 'Try narrowing your search' in str(err)

    def test_esasky_find_sso(self):
        sso = ESASky.find_sso(sso_name="Io")
        assert len(sso) >= 2
        assert "Io" in sso[0]['aliases'] or "Io" in sso[0]['sso_name']

        sso = ESASky.find_sso(sso_name="Io", sso_type="asteroid")
        assert len(sso) >= 1
        assert "Io" in sso[0]['aliases'] or "Io" in sso[0]['sso_name']
        assert "ASTEROID" in sso[0]['sso_type']

        assert ESASky.find_sso(sso_name="Not an SSO") is None

    def test_esasky_list_sso(self):
        assert len(ESASky.list_sso()) >= 3

    def test_esasky_get_images_sso(self, tmp_path):
        table_list = ESASky.query_sso(sso_name="ceres")
        assert "HERSCHEL" in table_list.keys()
        fits_files = ESASky.get_images_sso(table_list=table_list, missions="XMM",
                                           download_dir=tmp_path)
        assert "HERSCHEL" not in fits_files
        assert "XMM" in fits_files
        assert isinstance(fits_files["XMM"][0], HDUList)

        fits_files = ESASky.get_images_sso(sso_name="ceres", missions="XMM",
                                           download_dir=tmp_path)
        assert "HERSCHEL" not in fits_files
        assert "XMM" in fits_files
        assert isinstance(fits_files["XMM"][0], HDUList)

        assert Path(tmp_path, "XMM").exists()
