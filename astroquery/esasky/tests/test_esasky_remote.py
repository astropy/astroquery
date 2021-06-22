# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import shutil
import pytest
from astroquery import log
from astroquery.utils.tap.model.taptable import TapTableMeta
from astroquery.utils.tap.model.tapcolumn import TapColumn
from astroquery.utils.commons import TableList
from astropy.io.fits.hdu.hdulist import HDUList

from ... import esasky

ESASkyClass = esasky.core.ESASkyClass()


@pytest.mark.remote_data
class TestESASky:

    def test_esasky_query_ids_maps(self):
        result = ESASkyClass.query_ids_maps(observation_ids=["lbsk03vbq", "ieag90010"], missions="HST-UV")
        assert isinstance(result, TableList)
        assert "lbsk03vbq" in result["HST-UV"].columns["observation_id"]
        assert "ieag90010" in result["HST-UV"].columns["observation_id"]

        result = ESASkyClass.query_ids_maps(observation_ids="lbsk03vbq")
        assert isinstance(result, TableList)
        assert "lbsk03vbq" in result["HST-UV"].columns["observation_id"]

        result = ESASkyClass.query_ids_maps(observation_ids=["lbsk03vbq", "ieag90010", "1342221275", "1342221848"],
                                            missions=["Herschel", "HST-UV"])
        assert isinstance(result, TableList)
        assert "lbsk03vbq" in result["HST-UV"].columns["observation_id"]
        assert "ieag90010" in result["HST-UV"].columns["observation_id"]
        assert "1342221275" in result["HERSCHEL"].columns["observation_id"]
        assert "1342221848" in result["HERSCHEL"].columns["observation_id"]

    def test_esasky_query_ids_catalogs(self):
        result = ESASkyClass.query_ids_catalogs(source_ids=["2CXO J090341.1-322609", "2CXO J090353.8-322642"],
                                                catalogs="CHANDRA-SC2")
        assert isinstance(result, TableList)
        assert "2CXO J090341.1-322609" in result["CHANDRA-SC2"].columns["name"]
        assert "2CXO J090353.8-322642" in result["CHANDRA-SC2"].columns["name"]

        result = ESASkyClass.query_ids_catalogs(source_ids=["2CXO J090341.1-322609"])
        assert isinstance(result, TableList)
        assert "2CXO J090341.1-322609" in result["CHANDRA-SC2"].columns["name"]

        result = ESASkyClass.query_ids_catalogs(source_ids=["2CXO J090341.1-322609", "2CXO J090353.8-322642", "44899",
                                                            "45057"],
                                                catalogs=["CHANDRA-SC2", "Hipparcos-2"])
        assert isinstance(result, TableList)
        assert "2CXO J090341.1-322609" in result["CHANDRA-SC2"].columns["name"]
        assert "2CXO J090353.8-322642" in result["CHANDRA-SC2"].columns["name"]
        assert "44899" in result["HIPPARCOS-2"].columns["name"]
        assert "45057" in result["HIPPARCOS-2"].columns["name"]

    def test_esasky_query_ids_spectra(self):
        result = ESASkyClass.query_ids_spectra(observation_ids=["0001730501", "0011420101"], missions="XMM-NEWTON")
        assert isinstance(result, TableList)
        assert "0001730501" in result["XMM-NEWTON"].columns["observation_id"]
        assert "0011420101" in result["XMM-NEWTON"].columns["observation_id"]

        result = ESASkyClass.query_ids_spectra(observation_ids="0001730501")
        assert isinstance(result, TableList)
        assert "0001730501" in result["XMM-NEWTON"].columns["observation_id"]

        result = ESASkyClass.query_ids_spectra(observation_ids=["0001730501", "0011420101", "1342246640"],
                                               missions=["XMM-NEWTON", "Herschel"])

        assert isinstance(result, TableList)
        assert "0001730501" in result["XMM-NEWTON"].columns["observation_id"]
        assert "0011420101" in result["XMM-NEWTON"].columns["observation_id"]
        assert "1342246640" in result["HERSCHEL"].columns["observation_id"]

    def test_esasky_get_images_obs_id(self):
        download_directory = "ESASkyRemoteTest"
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)

        missions = ["SUZAKU", "ISO-IR", "Chandra", "XMM-OM-OPTICAL", "XMM", "XMM-OM-UV", "HST-IR", "Herschel",
                    "Spitzer", "HST-UV", "HST-OPTICAL", "INTEGRAL"]

        result = ESASkyClass.get_images(observation_ids=["100001010", "01500403", "21171", "0852000101", "0851180201",
                                                         "0851180201", "n3tr01c3q", "1342247257", "30002561-25100",
                                                         "hst_07553_3h_wfpc2_f160bw_pc", "ocli05leq", "88600210001"],
                                        missions=missions, download_dir=download_directory)

        for mission in missions:
            file_path = os.path.join(download_directory, mission)
            assert os.path.exists(file_path)
            log.info("Checking {} data.".format(mission))
            if mission.upper() == "HERSCHEL":
                assert(isinstance(result[mission.upper()][0]["250"], HDUList))
                assert(isinstance(result[mission.upper()][0]["350"], HDUList))
                assert(isinstance(result[mission.upper()][0]["500"], HDUList))
            else:
                assert(isinstance(result[mission.upper()][0], HDUList))

        result = None

        shutil.rmtree(download_directory)

    def test_esasky_get_spectra_obs_id(self):
        download_directory = "ESASkyRemoteTest"
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)

        missions = ["ISO-IR", "Chandra", "IUE", "XMM-NEWTON", "HST-IR", "Herschel", "HST-UV", "HST-OPTICAL"]

        result = ESASkyClass.get_spectra(observation_ids=["02101201", "1005", "LWR13178", "0001730201", "ibh706cqq",
                                                          "1342253595", "z1ax0102t", "oeik2s020"],
                                         missions=missions, download_dir=download_directory)

        for mission in missions:
            file_path = os.path.join(download_directory, mission)
            assert os.path.exists(file_path)
            log.info("Checking {} data.".format(mission))
            if mission.upper() == "HERSCHEL":
                assert(isinstance(result[mission.upper()]["1342253595"]["WBS"]["WBS-V_USB_4b"], HDUList))
                assert(isinstance(result[mission.upper()]["1342253595"]["HRS"]["HRS-H_LSB_4b"], HDUList))
            else:
                assert(isinstance(result[mission.upper()][0], HDUList))

        result = None

        shutil.rmtree(download_directory)

    def test_esasky_query_region_maps(self):
        result = ESASkyClass.query_region_maps(position="M51", radius="5 arcmin")
        assert isinstance(result, TableList)

    def test_esasky_query_object_maps(self):
        result = ESASkyClass.query_object_maps(position="M51")
        assert isinstance(result, TableList)

    @pytest.mark.bigdata
    def test_esasky_get_images(self):
        download_directory = "ESASkyRemoteTest"
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)

        missions = ESASkyClass.list_maps()
        # Remove very large map missions & missions with many results
        # & missions without proper download url (INTEGRAL, SUZAKU, ALMA, AKARI)
        missions = [mission for mission in missions if mission not in
                    ("HST-OPTICAL", "HST-IR", "HST-UV", "XMM-OM-UV", "INTEGRAL", "SUZAKU", "ALMA", "AKARI")]

        ESASkyClass.get_images(position="M51", missions=missions, download_dir=download_directory)

        for mission in missions:
            file_path = os.path.join(download_directory, mission)
            assert os.path.exists(file_path)

        shutil.rmtree(download_directory)

    def test_esasky_get_images_small(self):
        download_directory = "ESASkyRemoteTest"
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)

        # ISO is only ~ 163 kB
        missions = ['ISO-IR']

        ESASkyClass.get_images(position="M6", radius="12arcmin", missions=missions, download_dir=download_directory)

        for mission in missions:
            file_path = os.path.join(download_directory, mission)
            assert os.path.exists(file_path)

        shutil.rmtree(download_directory)

    @pytest.mark.bigdata
    def test_esasky_get_images_hst(self):
        download_directory = "ESASkyRemoteTest"
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)

        ESASkyClass.get_images(position="M11", radius="2.1 deg", missions="HST-UV", download_dir=download_directory)

        file_path = os.path.join(download_directory, "HST-UV")
        assert os.path.exists(file_path)

        shutil.rmtree(download_directory)

    def test_esasky_query_region_catalogs(self):
        result = ESASkyClass.query_region_catalogs(position="M51", radius="5 arcmin")
        assert isinstance(result, TableList)

    def test_esasky_query_object_catalogs(self):
        result = ESASkyClass.query_object_catalogs(position="M51")
        assert isinstance(result, TableList)

    def test_esasky_get_maps(self):
        download_directory = "ESASkyRemoteTest"
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)

        file_path = os.path.join(download_directory, 'ISO-IR')

        all_maps = ESASkyClass.query_object_maps(position="M51")
        iso_maps = ESASkyClass.query_object_maps(position="M51", missions='ISO-IR')
        # Remove a few maps, so the other list will have downloadable ones, too
        iso_maps['ISO-IR'].remove_rows([0, 1])
        ESASkyClass.get_maps(iso_maps, download_dir=download_directory)
        assert len(os.listdir(file_path)) == len(all_maps['ISO-IR']) - 2

        iso_maps2 = dict({'ISO-IR': all_maps['ISO-IR'][:2]})
        ESASkyClass.get_maps(iso_maps2, download_dir=download_directory)
        assert len(os.listdir(file_path)) == len(all_maps['ISO-IR'])

        shutil.rmtree(download_directory)

    def test_esasky_query_region_spectra(self):
        result = ESASkyClass.query_region_spectra(position="M51", radius="5 arcmin")
        assert isinstance(result, TableList)

    def test_esasky_query_object_spectra(self):
        result = ESASkyClass.query_object_spectra(position="M51")
        assert isinstance(result, TableList)

    @pytest.mark.bigdata
    def test_esasky_get_spectra(self):
        download_directory = "ESASkyRemoteTest"
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)

        missions = ESASkyClass.list_spectra()
        # HST-IR has no data, LAMOST does not support download
        missions = [mission for mission in missions if mission not in ("HST-IR", "LAMOST")]
        ESASkyClass.get_spectra(position="M1", missions=missions, download_dir=download_directory)

        for mission in missions:
            file_path = os.path.join(download_directory, mission)
            assert os.path.exists(file_path)

        shutil.rmtree(download_directory)

    def test_esasky_get_spectra_small(self):
        download_directory = "ESASkyRemoteTest"
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)

        missions = ['HST-IR']

        ESASkyClass.get_spectra(position="M1", radius="9arcmin", missions=missions, download_dir=download_directory)

        for mission in missions:
            file_path = os.path.join(download_directory, mission)
            assert os.path.exists(file_path)

        shutil.rmtree(download_directory)

    def test_esasky_get_spectra_from_table(self):
        download_directory = "ESASkyRemoteTest"
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)

        file_path = os.path.join(download_directory, 'ISO-IR')

        all_spectra = ESASkyClass.query_object_spectra(position="M51")
        iso_spectra = ESASkyClass.query_object_spectra(position="M51", missions='ISO-IR')
        # Remove a few maps, so the other list will have downloadable ones, too
        iso_spectra['ISO-IR'].remove_rows([0, 1])
        ESASkyClass.get_spectra_from_table(query_table_list=iso_spectra, download_dir=download_directory)
        assert len(os.listdir(file_path)) == len(all_spectra['ISO-IR']) - 2

        iso_spectra2 = dict({'ISO-IR': all_spectra['ISO-IR'][:2]})
        ESASkyClass.get_spectra_from_table(query_table_list=iso_spectra2, download_dir=download_directory)
        assert len(os.listdir(file_path)) == len(all_spectra['ISO-IR'])

        shutil.rmtree(download_directory)

    def test_query(self):
        result = ESASkyClass.query(query="SELECT * from observations.mv_v_esasky_xmm_om_uv_fdw")
        assert len(result) == 2000  # Default row limit is 2000

    def test_get_tables(self):
        table_names = ESASkyClass.get_tables(only_names=True)
        assert len(table_names) > 70
        tables = ESASkyClass.get_tables(only_names=False)
        assert isinstance(tables[0], TapTableMeta)
        assert len(table_names) == len(tables)

    def test_get_columns(self):
        column_names = ESASkyClass.get_columns(table_name='observations.mv_v_esasky_xmm_om_uv_fdw', only_names=True)
        assert len(column_names) == 17

        columns = ESASkyClass.get_columns(table_name='observations.mv_v_esasky_xmm_om_uv_fdw', only_names=False)
        assert isinstance(columns[0], TapColumn)
        assert len(column_names) == len(columns)
