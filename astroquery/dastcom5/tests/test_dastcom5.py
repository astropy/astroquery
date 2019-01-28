import os
from unittest import mock

import numpy as np
import pytest

from ...dastcom5 import Dastcom5

from astropy.table import Table


@mock.patch("astroquery.dastcom5.np.fromfile")
@mock.patch("astroquery.dastcom5.open")
def test_asteroid_db_is_called_with_right_path(mock_open, mock_np_fromfile):
    Dastcom5.asteroid_db()
    mock_open.assert_called_with(Dastcom5.ast_path, "rb")


@mock.patch("astroquery.dastcom5.np.fromfile")
@mock.patch("astroquery.dastcom5.open")
def test_comet_db_is_called_with_right_path(mock_open, mock_np_fromfile):
    Dastcom5.comet_db()
    mock_open.assert_called_with(Dastcom5.com_path, "rb")


@mock.patch("astroquery.dastcom5.np.fromfile")
@mock.patch("astroquery.dastcom5.open")
def test_read_headers(mock_open, mock_np_fromfile):
    Dastcom5.read_headers()
    mock_open.assert_any_call(
        os.path.join(Dastcom5.dbs_path, "dast5_le.dat"), "rb"
    )
    mock_open.assert_any_call(
        os.path.join(Dastcom5.dbs_path, "dcom5_le.dat"), "rb"
    )


@mock.patch("astroquery.dastcom5.Dastcom5.read_headers")
@mock.patch("astroquery.dastcom5.np.fromfile")
@mock.patch("astroquery.dastcom5.open")
def test_read_record(mock_open, mock_np_fromfile, mock_read_headers):
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


@mock.patch("astroquery.dastcom5.os.makedirs")
@mock.patch("astroquery.dastcom5.zipfile")
@mock.patch("astroquery.dastcom5.os.path.isdir")
@mock.patch("astroquery.dastcom5.urllib.request")
def test_download_dastcom5_raises_error_when_folder_exists(
    mock_request, mock_isdir, mock_zipfile, mock_makedirs
):
    mock_isdir.side_effect = lambda x: x == os.path.join(
        Dastcom5.local_path, "dastcom5"
    )
    with pytest.raises(FileExistsError):
        Dastcom5.download_dastcom5()
    mock_isdir.assert_called_once_with(
        os.path.join(Dastcom5.local_path, "dastcom5")
    )


@mock.patch("astroquery.dastcom5.urllib.request")
@mock.patch("astroquery.dastcom5.os.makedirs")
@mock.patch("astroquery.dastcom5.zipfile")
@mock.patch("astroquery.dastcom5.os.path.isdir")
def test_download_dastcom5_creates_folder(
    mock_isdir, mock_zipfile, mock_makedirs, mock_request
):
    mock_isdir.return_value = False
    mock_zipfile.is_zipfile.return_value = False
    Dastcom5.download_dastcom5()
    mock_makedirs.assert_called_once_with(Dastcom5.local_path)


@mock.patch("astroquery.dastcom5.zipfile")
@mock.patch("astroquery.dastcom5.os.path.isdir")
@mock.patch("astroquery.dastcom5.urllib.request.urlretrieve")
def test_download_dastcom5_downloads_file(mock_request, mock_isdir, mock_zipfile):
    mock_isdir.side_effect = lambda x: x == Dastcom5.local_path
    mock_zipfile.is_zipfile.return_value = False
    Dastcom5.download_dastcom5()
    mock_request.assert_called_once_with(
        Dastcom5.FTP_DB_URL + "dastcom5.zip",
        os.path.join(Dastcom5.local_path, "dastcom5.zip"),
        Dastcom5._show_download_progress,
    )
