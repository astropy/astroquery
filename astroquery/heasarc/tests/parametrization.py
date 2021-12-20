import os
import glob
import hashlib
import requests
import pytest
from ... import log

"""
This is an attempt to reduce code duplication between remote and local tests.

if there is test data:
    runs as usual, except all tests have two versions with the same code: remote and local
else
    runs remote test patched so that the test data is stored in a temporary directory.
    advice is given to copy the newly generated test data into the repository
"""


class MockResponse:
    def __init__(self, text):
        self.text = text
        self.content = text.encode()


def data_path(filename, output=False):
    if output:
        data_dir = os.path.join(
            os.getenv("TMPDIR", "/tmp"), "astroquery-heasarc-saved-data"
        )
        os.makedirs(data_dir, exist_ok=True)
    else:
        data_dir = os.path.join(os.path.dirname(__file__), "data")

    return os.path.join(data_dir, filename + ".dat")


def filename_for_request(url, params, output=False):
    fileid = hashlib.md5(str((url, sorted(params.items()))).encode()).hexdigest()[:8]
    return data_path(fileid, output=output)


# TODO: are get_mockreturn args up-to-date in example in https://astroquery.readthedocs.io/en/latest/testing.html ?
def get_mockreturn(session, method, url, params=None, timeout=10, **kwargs):

    filename = filename_for_request(url, params)
    try:
        content = open(filename, "rt").read()
    except FileNotFoundError:
        log.error(
            f'no stored mock data in {filename} for url="{url}" and params="{params}"'
            "perhaps you need to clean test data and regenerate it? "
            "It will be regenerated automatically if cleaned, try `rm -fv astroquery/heasarc/tests/data/* build`"
        )
        raise

    return MockResponse(content)


def save_response_of_get(session, method, url, params=None, timeout=10, **kwargs):
    # _original_request is a monkeypatch-added attribute in patch_get
    text = requests.Session._original_request(
        session, method, url, params=params, timeout=timeout
    ).text

    filename = filename_for_request(url, params, output=True)

    with open(filename, "wt") as f:
        log.info(f'saving output to {filename} for url="{url}" and params="{params}"')
        log.warning(
            f"you may want to run `cp -fv {os.path.dirname(filename)}/* astroquery/heasarc/tests/data/; rm -rfv build`"
        )
        f.write(text)

    return MockResponse(text)


@pytest.fixture(autouse=True)
def patch_get(request):
    mode = request.param
    mp = request.getfixturevalue("monkeypatch")

    if mode != "remote":
        requests.Session._original_request = requests.Session.request
        mp.setattr(
            requests.Session,
            "request",
            {"save": save_response_of_get, "local": get_mockreturn}[mode],
        )
    return mp


def have_mock_data():
    return len(glob.glob(data_path("*"))) > 0


parametrization_local_save_remote = pytest.mark.parametrize(
    "patch_get", [
        pytest.param("local", marks=[
            pytest.mark.skipif(not have_mock_data(),
                               reason="No test data found. If remote_data is allowed, we'll generate some.")]),
        pytest.param("save", marks=[
            pytest.mark.remote_data,
            pytest.mark.skipif(have_mock_data(),
                               reason="found some test data: please delete them to save again.")]),
        pytest.param("remote", marks=[
            pytest.mark.remote_data,
            pytest.mark.skipif(not have_mock_data(),
                               reason="No test data found, [save] will run remote tests and save data.")])],
    indirect=True)
