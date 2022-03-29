from asyncio.log import logger
import os
import json
import glob
import hashlib
import requests
import pytest
from difflib import Differ, SequenceMatcher
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

    return os.path.join(data_dir, filename + ".json")


def fileid_for_request(url, params):
    return hashlib.md5(str((url, sorted(params.items()))).encode()).hexdigest()[:8]


def filename_for_request(url, params, output=False):
    fileid = fileid_for_request(url, params)
    return data_path(fileid, output=output)


def request_dict_to_string_list(request_dict):
    return json.dumps(request_dict, sort_keys=True, indent=4).split("\n")


def get_mockreturn(session, method, url, params=None, timeout=10, **kwargs):

    filename = filename_for_request(url, params)
    try:
        with open(filename, "rt") as f:
            content = json.load(f)['response_text']    
    except (json.decoder.JSONDecodeError, IndexError) as e:
        log.error(
            f'stored mock data in {filename} for url="{url}" and params="{params}"',
            f'causes IndexError: {e}. You might need to regenerate it.'
        )
        raise
    except FileNotFoundError:
        log.error(
            f'no stored mock data in {filename} for url="{url}" and params="{params}", '
            f'perhaps you need to clean test data and regenerate it? '
            f'It will be regenerated automatically if cleaned, try `rm -fv astroquery/heasarc/tests/data/* ./build`'
        )

        unavailable_request = request_to_dict(url, params)

        log.error('overall, have %s mock data entries', len(list_mock_data()))

        
                
        available_requests = []
        for available_mock_data in list_mock_data():
            with open(available_mock_data) as f:
                available_request = json.load(f)['request']
                a = request_dict_to_string_list(available_request)
                ua = request_dict_to_string_list(unavailable_request)
                try:
                    available_requests.append([
                        SequenceMatcher(a=a, b=ua).ratio(),
                        Differ().compare(a=a, b=ua),
                    ])
                except json.decoder.JSONDecodeError as e:
                    log.warning('undecodable mock result in %s', available_mock_data)
                    continue
                
        for ratio, differ in sorted(available_requests):
            log.error('available: %s %s', ratio, "\n".join(differ))
            

        raise

    return MockResponse(content)


def request_to_dict(url: str, params: dict):
    return {"url": url, "params": params}


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
            "`git add astroquery/heasarc/tests/data/*`."
        )
        json.dump({
            "request": request_to_dict(url, params),
            "response_text": text,
        }, f)

    return MockResponse(text)


@pytest.fixture(autouse=True)
def patch_get(request):
    """
    If the mode is not remote, patch `requests.Session` to either return saved local data or run save data new local data
    """
    mode = request.param
    mp = request.getfixturevalue("monkeypatch")

    if mode != "remote":
        requests.Session._original_request = requests.Session.request
        mp.setattr(
            requests.Session,
            "request",
            {"save": save_response_of_get, "local": get_mockreturn}[mode],
        )

    mp.assume_fileid_for_request = lambda patched_fileid_for_request: \
        mp.setattr('astroquery.heasarc.tests.parametrization.fileid_for_request', patched_fileid_for_request)

    mp.reset_default_fileid_for_request = lambda: \
        mp.delattr('astroquery.heasarc.tests.parametrization.fileid_for_request')

    return mp


def list_mock_data():
    return glob.glob(data_path("*"))
    

def have_mock_data():
    return len(list_mock_data()) > 0


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
