import os
import glob
import hashlib
import requests
import traceback
import pytest
from .. import log

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
            os.getenv("TMPDIR", "/tmp"), "astroquery-saved-data"
        )
        os.makedirs(data_dir, exist_ok=True)
    else:
        # the function should be called from module tests.
        # we need to find out which one
        test_modules = []
        for fs in traceback.extract_stack():
            fs_filename_split = fs.filename.split("/")
            if len(fs_filename_split) > 4 and \
               fs_filename_split[-1].startswith("test_") and \
               fs_filename_split[-2] == 'tests' and \
               fs_filename_split[-4] == 'astroquery':
                test_modules.append(os.path.dirname(fs.filename))

        if len(set(test_modules)) == 0:
            raise RuntimeError('It seems that "data_path" function was called not from one of the test modules.'
                               'Module-specific mock data_path can not be constructed')
        elif len(set(test_modules)) > 1:
            raise RuntimeError('It seems that "data_path" call stack includes several modules, '
                               f'this is probably a programming issue: {test_modules}')

        test_module = test_modules[0]

        data_dir = os.path.join(test_module, "data")

    return os.path.join(data_dir, filename + ".dat")


def fileid_for_request(url, params):
    return hashlib.md5(str((url, sorted(params.items()))).encode()).hexdigest()[:8]


def filename_for_request(url, params, output=False):
    fileid = fileid_for_request(url, params)
    return data_path(fileid, output=output)


def get_mockreturn(session, method, url, params=None, timeout=10, **kwargs):
    """
    Finds mock response based on the the request - URL and params (not headers or method)
    """

    filename = filename_for_request(url, params)
    try:
        content = open(filename, "rt").read()
    except FileNotFoundError:
        log.error(
            f'no stored mock data in {filename} for url="{url}" and params="{params}", '
            f'perhaps you need to clean test data and regenerate it? '
            f'It will be regenerated automatically if cleaned, try `rm -fv astroquery/heasarc/tests/data/* ./build`'
        )
        raise

    return MockResponse(content)


def save_response_of_get(session, method, url, params=None, timeout=10, **kwargs):
    """
    Performs remote requests, and saves the response in a unique filename, constructed from URL and params (not headers or method)
    """

    # _original_request is a monkeypatch-added attribute in patch_get
    text = requests.Session._original_request(
        session, method, url, params=params, timeout=timeout
    ).text

    filename = filename_for_request(url, params, output=True)

    with open(filename, "wt") as f:
        log.info(f'saving output to {filename} for url="{url}" and params="{params}"')
        # TODO: add doc and a reference to it here
        log.warning(
            f"you may want to run `cp -fv {os.path.dirname(filename)}/* astroquery/heasarc/tests/data/; rm -rfv build`"
            "`git add astroquery/heasarc/tests/data/*`."
        )
        f.write(text)

    return MockResponse(text)


@pytest.fixture(autouse=True)
def patch_get(request):
    """
    If the mode is not remote, patch `requests.Session` to either return saved local data or run save data new local data
    TODO: add reference to doc
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
        mp.setattr('astroquery.utils.testing_parametrization.fileid_for_request', patched_fileid_for_request)

    mp.reset_default_fileid_for_request = lambda: \
        mp.delattr('astroquery.utils.testing_parametrization.fileid_for_request')

    return mp


def have_mock_data():
    try:
        return len(glob.glob(data_path("*"))) > 0
    except RuntimeError:
        #TODO: this is questionable
        return False


parametrization_local_save_remote = pytest.mark.parametrize(
    "patch_get", [
        pytest.param("local", marks=[
            pytest.mark.skipif(not have_mock_data(),
                               reason=f"No test data found in {'/'.join(data_path('').split('/')[-4:])}. If remote_data is allowed, we'll generate some.")]),
        pytest.param("save", marks=[
            pytest.mark.remote_data,
            pytest.mark.skipif(have_mock_data(),
                               reason="found some test data: please delete them to save again.")]),
        pytest.param("remote", marks=[
            pytest.mark.remote_data,
            pytest.mark.skipif(not have_mock_data(),
                               reason="No test data found, [save] will run remote tests and save data.")])],
    indirect=True)
