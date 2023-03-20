# Licensed under a 3-clause BSD style license - see LICENSE.rst
from pathlib import Path
import tarfile

import pytest

from ..core import HSAClass


pytestmark = pytest.mark.remote_data


PACS_ENDINGS = ["571.xml", "571.jpg", "214.fits.gz", "008.fits.gz",
                "674.fits.gz", "350.fits.gz", "README.pdf"]
SPIRE_ENDINGS = ["898.xml", "898.jpg", "141.fits.gz", "045.fits.gz", "952.fits.gz",
                 "974.fits.gz", "715.fits.gz", "547.fits.gz", "770.fits.gz",
                 "856.fits.gz", "148.fits.gz", "025.fits.gz", "538.fits.gz",
                 "070.fits.gz", "434.fits.gz", "637.fits.gz", "835.fits.gz",
                 "372.fits.gz", "248.fits.gz", "README.pdf"]


@pytest.mark.parametrize(
    "method,kwargs,expected_filename,expected_endings",
    [("download_data", {}, "1342191813.tar", PACS_ENDINGS),
     ("download_data", {"filename": "output_file"}, "output_file.tar", PACS_ENDINGS),
     ("download_data", {"compress": "true"}, "1342191813.tgz", PACS_ENDINGS),
     ("download_data", {"observation_id": "1342191188", "instrument_name": "SPIRE", "product_level": "LEVEL2", },
      "1342191188.tar", SPIRE_ENDINGS),
     ("get_observation", {}, "1342191813.tar", PACS_ENDINGS)])
def test_download_data_observation(method, kwargs, expected_filename, expected_endings, tmp_path):
    parameters = {"observation_id": "1342191813",
                  'instrument_name': "PACS",
                  'product_level': 'LEVEL3',
                  'cache': False,
                  'download_dir': tmp_path}
    parameters.update(kwargs)
    if method == "download_data":
        res = HSAClass().download_data(**parameters, retrieval_type="OBSERVATION")
    elif method == "get_observation":
        res = HSAClass().get_observation(**parameters)
    assert Path(res) == tmp_path / expected_filename
    assert Path(res).is_file()
    with tarfile.open(res) as tar:
        names = tar.getnames()
    assert len(names) == len(expected_endings)
    for name, ending in zip(names, expected_endings):
        assert name.endswith(ending)


@pytest.mark.parametrize(
    "method,kwargs,expected_filename",
    [("download_data", {}, "1342191813.jpg"),
     ("download_data", {"filename": "output_file"}, "output_file.jpg"),
     ("get_postcard", {}, "1342191813.jpg")])
def test_download_data_postcard(method, kwargs, expected_filename, tmp_path):
    parameters = {"observation_id": "1342191813",
                  'instrument_name': "PACS",
                  'cache': False,
                  'download_dir': tmp_path}
    if method == "download_data":
        res = HSAClass().download_data(**parameters, **kwargs, retrieval_type="POSTCARD")
    elif method == "get_postcard":
        res = HSAClass().get_postcard(**parameters, **kwargs)
    assert Path(res) == tmp_path / expected_filename
    assert Path(res).is_file()
