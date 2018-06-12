# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import os
import shutil
import pytest

from astroquery.utils.commons import TableList
from astropy.tests.helper import remote_data

from ... import esasky

ESASkyClass = esasky.core.ESASkyClass()


@remote_data
class TestESASky:

    ESASkyClass._isTest = "Remote Test"

    def test_esasky_query_region_maps(self):
        result = ESASkyClass.query_region_maps("M51", "5 arcmin")
        assert isinstance(result, TableList)

    def test_esasky_query_object_maps(self):
        result = ESASkyClass.query_object_maps("M51")
        assert isinstance(result, TableList)

    @pytest.mark.bigdata
    @pytest.mark.xfail(reason='Unknown.  This regularly fails on travis, but not locally.')
    def test_esasky_get_images(self):
        download_directory = "ESASkyRemoteTest"
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)

        missionsExceptHstAndIntegral = ESASkyClass.list_maps()
        missionsExceptHstAndIntegral.remove("HST")
        missionsExceptHstAndIntegral.remove("INTEGRAL")
        # Added May 10, 2018: there are no hits from SUZAKU
        missionsExceptHstAndIntegral.remove("SUZAKU")

        ESASkyClass.get_images("M51", missions=missionsExceptHstAndIntegral, download_dir=download_directory)

        for mission in missionsExceptHstAndIntegral:
            file_path = os.path.join(download_directory, ESASkyClass._MAPS_DOWNLOAD_DIR, mission)
            assert os.path.exists(file_path)

        shutil.rmtree(download_directory)

    def test_esasky_get_images_small(self):
        download_directory = "ESASkyRemoteTest"
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)

        # ISO is only ~ 800 kB
        missions = ['ISO']

        ESASkyClass.get_images("M51", missions=missions, download_dir=download_directory)

        for mission in missions:
            file_path = os.path.join(download_directory, ESASkyClass._MAPS_DOWNLOAD_DIR, mission)
            assert os.path.exists(file_path)

        shutil.rmtree(download_directory)

    @pytest.mark.xfail(reason='Internal Error. Please try later')
    def test_esasky_get_images_hst(self):
        download_directory = "ESASkyRemoteTest"
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)

        ESASkyClass.get_images("M7", radius="10 arcmin", missions="HST", download_dir=download_directory)

        file_path = os.path.join(download_directory, ESASkyClass._MAPS_DOWNLOAD_DIR, "HST")
        assert os.path.exists(file_path)

        shutil.rmtree(download_directory)

    def test_esasky_query_region_catalogs(self):
        result = ESASkyClass.query_region_catalogs("M51", "5 arcmin")
        assert isinstance(result, TableList)

    def test_esasky_query_object_catalogs(self):
        result = ESASkyClass.query_object_catalogs("M51")
        assert isinstance(result, TableList)
