# Licensed under a 3-clause BSD style license - see LICENSE.rst
from pathlib import Path
import tarfile

import pytest
from requests.exceptions import ChunkedEncodingError

from ..core import HSAClass



PACS_ENDINGS = ["571.xml", "571.jpg", "214.fits.gz", "008.fits.gz",
                "674.fits.gz", "350.fits.gz", "README.pdf"]
SPIRE_ENDINGS = ["898.xml", "898.jpg", "141.fits.gz", "045.fits.gz", "952.fits.gz",
                 "974.fits.gz", "715.fits.gz", "547.fits.gz", "770.fits.gz",
                 "856.fits.gz", "148.fits.gz", "025.fits.gz", "538.fits.gz",
                 "070.fits.gz", "434.fits.gz", "637.fits.gz", "835.fits.gz",
                 "372.fits.gz","248.fits.gz", "README.pdf"]


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
            names = tar.getnames()
        assert len(names) == len(PACS_ENDINGS)
        for name, ending in zip(names, PACS_ENDINGS):
            assert name.endswith(ending)

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
            names = tar.getnames()
        assert len(names) == len(PACS_ENDINGS)
        for name, ending in zip(names, PACS_ENDINGS):
            assert name.endswith(ending)

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
            names = tar.getnames()
        assert len(names) == len(PACS_ENDINGS)
        for name, ending in zip(names, PACS_ENDINGS):
            assert name.endswith(ending)

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
            names = tar.getnames()
        assert len(names) == len(SPIRE_ENDINGS)
        for name, ending in zip(names, SPIRE_ENDINGS):
            assert name.endswith(ending)

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
            names = tar.getnames()
        assert len(names) == len(PACS_ENDINGS)
        for name, ending in zip(names, PACS_ENDINGS):
            assert name.endswith(ending)

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
