# Licensed under a 3-clause BSD style license - see LICENSE.rst
from pathlib import Path
import tarfile

import pytest
from requests.exceptions import ChunkedEncodingError

from ..core import HSAClass

spire_chksum = [10233, 10762, 9019, 10869, 3944, 11328, 3921, 10999, 10959, 11342, 10974, 3944, 11335, 11323, 11078, 11321, 11089, 11314, 11108, 6281]

pacs_chksum = [10208, 10755, 8917, 10028, 3924, 3935, 6291]


@pytest.mark.remote_data
class TestHSARemote:
    retries = 2

    def access_archive_with_retries(self, f, params):
        for _ in range(self.retries):
            try:
                res = f(**params)
                return res
            except ChunkedEncodingError:
                pass
        return None

    def test_download_data_observation_pacs(self, tmp_path):
        obs_id = "1342191813"
        parameters = {'retrieval_type': "OBSERVATION",
                      'observation_id': obs_id,
                      'instrument_name': "PACS",
                      'product_level': 'LEVEL3',
                      'cache': False,
                      'download_dir': tmp_path}
        expected_res = Path(tmp_path, obs_id + ".tar")
        hsa = HSAClass()
        res = self.access_archive_with_retries(hsa.download_data, parameters)
        if res is None:
            pytest.xfail(f"Archive broke the connection {self.retries} times, unable to test")
        assert Path(res) == expected_res
        assert Path(res).is_file()
        with tarfile.open(res) as tar:
            chksum = [m.chksum for m in tar.getmembers()]
        assert chksum.sort() == pacs_chksum.sort()

    def test_download_data_observation_pacs_filename(self, tmp_path):
        obs_id = "1342191813"
        fname = "output_file"
        parameters = {'retrieval_type': "OBSERVATION",
                      'observation_id': obs_id,
                      'instrument_name': "PACS",
                      'product_level': 'LEVEL3',
                      'filename': fname,
                      'cache': False,
                      'download_dir': tmp_path}
        expected_res = Path(tmp_path, fname + ".tar")
        hsa = HSAClass()
        res = self.access_archive_with_retries(hsa.download_data, parameters)
        if res is None:
            pytest.xfail(f"Archive broke the connection {self.retries} times, unable to test")
        assert Path(res) == expected_res
        assert Path(res).is_file()
        with tarfile.open(res) as tar:
            chksum = [m.chksum for m in tar.getmembers()]
        assert chksum.sort() == pacs_chksum.sort()

    def test_download_data_observation_pacs_compressed(self, tmp_path):
        obs_id = "1342191813"
        parameters = {'retrieval_type': "OBSERVATION",
                      'observation_id': obs_id,
                      'instrument_name': "PACS",
                      'product_level': 'LEVEL3',
                      'compress': 'true',
                      'cache': False,
                      'download_dir': tmp_path}
        expected_res = Path(tmp_path, obs_id + ".tgz")
        hsa = HSAClass()
        res = self.access_archive_with_retries(hsa.download_data, parameters)
        if res is None:
            pytest.xfail(f"Archive broke the connection {self.retries} times, unable to test")
        assert Path(res) == expected_res
        assert Path(res).is_file()
        with tarfile.open(res) as tar:
            chksum = [m.chksum for m in tar.getmembers()]
        assert chksum.sort() == pacs_chksum.sort()

    def test_download_data_observation_spire(self, tmp_path):
        obs_id = "1342191188"
        parameters = {'retrieval_type': "OBSERVATION",
                      'observation_id': obs_id,
                      'instrument_name': "SPIRE",
                      'product_level': 'LEVEL2',
                      'cache': False,
                      'download_dir': tmp_path}
        expected_res = Path(tmp_path, obs_id + ".tar")
        hsa = HSAClass()
        res = self.access_archive_with_retries(hsa.download_data, parameters)
        if res is None:
            pytest.xfail(f"Archive broke the connection {self.retries} times, unable to test")
        assert Path(res) == expected_res
        assert Path(res).is_file()
        with tarfile.open(res) as tar:
            chksum = [m.chksum for m in tar.getmembers()]
        assert chksum.sort() == spire_chksum.sort()

    def test_download_data_postcard_pacs(self, tmp_path):
        obs_id = "1342191813"
        parameters = {'retrieval_type': "POSTCARD",
                      'observation_id': obs_id,
                      'instrument_name': "PACS",
                      'cache': False,
                      'download_dir': tmp_path}
        expected_res = Path(tmp_path, obs_id + ".jpg")
        hsa = HSAClass()
        res = self.access_archive_with_retries(hsa.download_data, parameters)
        if res is None:
            pytest.xfail(f"Archive broke the connection {self.retries} times, unable to test")
        assert Path(res) == expected_res
        assert Path(res).is_file()

    def test_download_data_postcard_pacs_filename(self, tmp_path):
        obs_id = "1342191813"
        fname = "output_file"
        parameters = {'retrieval_type': "POSTCARD",
                      'observation_id': obs_id,
                      'instrument_name': "PACS",
                      'filename': fname,
                      'cache': False,
                      'download_dir': tmp_path}
        expected_res = Path(tmp_path, fname + ".jpg")
        hsa = HSAClass()
        res = self.access_archive_with_retries(hsa.download_data, parameters)
        if res is None:
            pytest.xfail(f"Archive broke the connection {self.retries} times, unable to test")
        assert Path(res) == expected_res
        assert Path(res).is_file()

    def test_get_observation(self, tmp_path):
        obs_id = "1342191813"
        parameters = {'observation_id': obs_id,
                      'instrument_name': "PACS",
                      'product_level': 'LEVEL3',
                      'cache': False,
                      'download_dir': tmp_path}
        expected_res = Path(tmp_path, obs_id + ".tar")
        hsa = HSAClass()
        res = self.access_archive_with_retries(hsa.get_observation, parameters)
        if res is None:
            pytest.xfail(f"Archive broke the connection {self.retries} times, unable to test")
        assert Path(res) == expected_res
        assert Path(res).is_file()
        with tarfile.open(res) as tar:
            chksum = [m.chksum for m in tar.getmembers()]
        assert chksum.sort() == pacs_chksum.sort()

    def test_get_postcard(self, tmp_path):
        obs_id = "1342191813"
        parameters = {'observation_id': obs_id,
                      'instrument_name': "PACS",
                      'cache': False,
                      'download_dir': tmp_path}
        expected_res = Path(tmp_path, obs_id + ".jpg")
        hsa = HSAClass()
        res = self.access_archive_with_retries(hsa.get_postcard, parameters)
        if res is None:
            pytest.xfail(f"Archive broke the connection {self.retries} times, unable to test")
        assert Path(res) == expected_res
        assert Path(res).is_file()
