import os

import numpy as np
import pytest
from pytest_mock import mocker

from ...dastcom5 import Dastcom5

from astropy.table import Table


def test_asteroid_db_is_called_with_right_path(mocker):
    mock_np_fromfile = mocker.patch("poliastro.neos.dastcom5.np.fromfile")
    mock_open = mocker.patch("poliastro.neos.dastcom5.open")
    Dastcom5.asteroid_db()
    mock_open.assert_called_with(Dastcom5.ast_path, "rb")


def test_comet_db_is_called_with_right_path(mocker):
    mock_np_fromfile = mocker.patch("poliastro.neos.dastcom5.np.fromfile")
    mock_open = mocker.patch("poliastro.neos.dastcom5.open")
    Dastcom5.comet_db()
    mock_open.assert_called_with(Dastcom5.com_path, "rb")


def test_read_headers(mocker):
    mock_np_fromfile = mocker.patch("poliastro.neos.dastcom5.np.fromfile")
    mock_open = mocker.patch("poliastro.neos.dastcom5.open")
    Dastcom5.read_headers()
    mock_open.assert_any_call(
        os.path.join(Dastcom5.dbs_path, "dast5_le.dat"), "rb"
    )
    mock_open.assert_any_call(
        os.path.join(Dastcom5.dbs_path, "dcom5_le.dat"), "rb"
    )


def test_read_record(mocker):
    mock_np_fromfile = mocker.patch("poliastro.neos.dastcom5.np.fromfile")
    mock_open = mocker.patch("poliastro.neos.dastcom5.open")
    mock_read_headers = mocker.patch(
        "astroquery.dastcom5.Dastcom5.read_headers")
    mocked_ast_headers = np.array(
        [(3184, -1, b"00740473", b"00496815")],
        dtype=[
            ("IBIAS1", np.int32),
            ("IBIAS0", np.int32),
            ("ENDPT2", "|S8"),
            ("ENDPT1", "|S8"),
        ],
    )
    mocked_com_headers = np.array([(99999,)], dtype=[("IBIAS2", "<i4")])

    mock_read_headers.return_value = mocked_ast_headers, mocked_com_headers
    Dastcom5.read_record(740473)
    mock_open.assert_called_with(
        os.path.join(Dastcom5.dbs_path, "dast5_le.dat"), "rb"
    )
    Dastcom5.read_record(740473 + 1)
    mock_open.assert_called_with(
        os.path.join(Dastcom5.dbs_path, "dcom5_le.dat"), "rb"
    )


def test_download_dastcom5_raises_error_when_folder_exists(mocker):
    mock_request = mocker.patch("astroquery.dastcom5.urllib.request")
    mock_isdir = mocker.patch("astroquery.dastcom5.os.path.isdir")
    mock_zipfile = mocker.patch("astroquery.dastcom5.zipfile")
    mock_makedirs = mocker.patch("astroquery.dastcom5.os.makedirs")
    mock_isdir.side_effect = lambda x: x == os.path.join(
        Dastcom5.local_path, "dastcom5"
    )
    with pytest.raises(FileExistsError):
        Dastcom5.download_dastcom5()
    mock_isdir.assert_called_once_with(
        os.path.join(Dastcom5.local_path, "dastcom5")
    )


def test_download_dastcom5_creates_folder(mocker):
    mock_request = mocker.patch("astroquery.dastcom5.urllib.request")
    mock_isdir = mocker.patch("astroquery.dastcom5.os.path.isdir")
    mock_zipfile = mocker.patch("astroquery.dastcom5.zipfile")
    mock_makedirs = mocker.patch("astroquery.dastcom5.os.makedirs")
    mock_isdir.return_value = False
    mock_zipfile.is_zipfile.return_value = False
    Dastcom5.download_dastcom5()
    mock_makedirs.assert_called_once_with(Dastcom5.local_path)


def test_download_dastcom5_downloads_file(mocker):
    mock_download = mocker.patch(
        "astroquery.query.BaseQuery._download_file")
    mock_isdir = mocker.patch("astroquery.dastcom5.os.path.isdir")
    mock_zipfile = mocker.patch("astroquery.dastcom5.zipfile")
    mock_isdir.side_effect = lambda x: x == Dastcom5.local_path
    mock_zipfile.is_zipfile.return_value = False
    Dastcom5.download_dastcom5()
    mock_download.assert_called_once_with(
        url=Dastcom5.ftp_url + "dastcom5.zip",
        local_filepath=os.path.join(Dastcom5.local_path, "dastcom5.zip"),
    )
