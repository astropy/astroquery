# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest
import requests
from pathlib import Path
from requests.models import Response
from astroquery.query import BaseQuery, BaseVOQuery
from astroquery.utils.mocks import MockResponse

# Test data directory
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

# Test data files
TEST_FILE_CONTENT = b'This is a test file with some content.'
TEST_FILE_PARTIAL = b'This is a partial'
TEST_FILE_REMAINDER = b' file with some content.'


class EnhancedMockResponse(MockResponse):
    """A MockResponse with additional attributes and methods needed by _download_file."""
    def __init__(self, content):
        super().__init__(content)
        self.headers = {}
        self.status_code = 200
        self.reason = 'OK'
        self.url = 'http://example.com/test.txt'
        self.request = type('Request', (), {'headers': {}})()
        self._content = content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP Error: {self.status_code}")

    def iter_content(self, chunk_size=None):
        if chunk_size is None:
            chunk_size = 8192
        content = self._content
        for ii in range(0, len(content), chunk_size):
            yield content[ii:ii + chunk_size]

    def close(self):
        self._content = None

    @property
    def content(self):
        if self._content is None:
            raise RuntimeError("Response content has been consumed")
        return self._content

    @content.setter
    def content(self, value):
        self._content = value


class MockResponse(Response):
    """A mocked Response object for testing."""
    def __init__(self, content=None):
        super().__init__()
        self._content = content


@pytest.fixture
def mock_response():
    """Create a mock response with test content."""
    response = EnhancedMockResponse(TEST_FILE_CONTENT)
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Content-Length'] = str(len(TEST_FILE_CONTENT))
    return response


@pytest.fixture
def mock_head_response():
    """Create a mock HEAD response with no content."""
    response = EnhancedMockResponse(b'')
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Content-Length'] = str(len(TEST_FILE_CONTENT))
    return response


@pytest.fixture
def mock_response_no_ranges():
    """Create a mock response without range support."""
    response = EnhancedMockResponse(TEST_FILE_CONTENT)
    response.headers['Content-Length'] = str(len(TEST_FILE_CONTENT))
    return response


@pytest.fixture
def base_query():
    """Create a BaseQuery instance for testing."""
    return BaseQuery()


@pytest.fixture
def patch_get(monkeypatch, mock_response, mock_head_response):
    """Patch requests.get to return our mock response."""
    def mock_request(method, url, headers=None, **kwargs):
        if method == 'HEAD':
            return mock_head_response

        if headers and 'Range' in headers:
            range_header = headers['Range']
            start = int(range_header.split('=')[1].split('-')[0])
            if start == len(TEST_FILE_PARTIAL):
                mock_response.content = TEST_FILE_REMAINDER
                mock_response.headers['Content-Range'] = (
                    f'bytes {start}-{len(TEST_FILE_CONTENT)-1}/{len(TEST_FILE_CONTENT)}'
                )
                mock_response.status_code = 206
            else:
                mock_response.content = TEST_FILE_CONTENT
        else:
            mock_response.content = TEST_FILE_CONTENT
            mock_response.status_code = 200
        return mock_response

    monkeypatch.setattr(requests.Session, 'request', mock_request)


@pytest.mark.parametrize('head_safe', [True, False])
def test_download_file_basic(base_query, patch_get, tmp_path, head_safe):
    """Test basic file download functionality."""
    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    response = base_query._download_file(url, str(local_file), head_safe=head_safe)
    assert response.status_code == 200
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT


@pytest.mark.parametrize('params', [
    {'head_safe': False, 'continuation': True, 'initial_content': None},
    {'head_safe': False, 'continuation': False, 'initial_content': None},
    {'head_safe': True, 'continuation': True, 'initial_content': None},
    {'head_safe': True, 'continuation': False, 'initial_content': None},
    {'head_safe': False, 'continuation': True, 'initial_content': TEST_FILE_PARTIAL},
    {'head_safe': False, 'continuation': False, 'initial_content': TEST_FILE_PARTIAL},
    {'head_safe': True, 'continuation': True, 'initial_content': TEST_FILE_PARTIAL},
    {'head_safe': True, 'continuation': False, 'initial_content': TEST_FILE_PARTIAL},
    {'head_safe': False, 'continuation': True, 'initial_content': TEST_FILE_CONTENT},
    {'head_safe': False, 'continuation': False, 'initial_content': TEST_FILE_CONTENT},
    {'head_safe': True, 'continuation': True, 'initial_content': TEST_FILE_CONTENT},
    {'head_safe': True, 'continuation': False, 'initial_content': TEST_FILE_CONTENT},
    {'head_safe': False, 'continuation': True, 'initial_content': b'wrong size'},
    {'head_safe': False, 'continuation': False, 'initial_content': b'wrong size'},
    {'head_safe': True, 'continuation': True, 'initial_content': b'wrong size'},
    {'head_safe': True, 'continuation': False, 'initial_content': b'wrong size'},
])
def test_download_file_with_existing(base_query, patch_get, tmp_path, params):
    """Test downloading with various combinations of head_safe, continuation, and existing file content."""
    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    # Create initial file state if initial_content is not None
    if params['initial_content'] is not None:
        local_file.write_bytes(params['initial_content'])

    response = base_query._download_file(url, str(local_file),
                                         head_safe=params['head_safe'],
                                         continuation=params['continuation'])
    assert response.status_code == 200
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT


@pytest.mark.parametrize('head_safe', [True, False])
def test_download_file_no_verbose(base_query, patch_get, tmp_path, head_safe):
    """Test downloading without progress bar."""
    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    response = base_query._download_file(url, str(local_file), verbose=False, head_safe=head_safe)
    assert response.status_code == 200
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT


@pytest.mark.parametrize('head_safe', [True, False])
def test_download_file_no_ranges_header(base_query, mock_response_no_ranges, monkeypatch, tmp_path, head_safe):
    """Test downloading when server doesn't support range requests."""
    def mock_request(method, url, headers=None, **kwargs):
        if method == 'HEAD':
            return mock_response_no_ranges
        return mock_response_no_ranges

    monkeypatch.setattr(requests.Session, 'request', mock_request)

    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    response = base_query._download_file(url, str(local_file), head_safe=head_safe)
    assert response.status_code == 200
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT


@pytest.mark.remote_data
class TestDownloadFileRemote:
    """Test _download_file with actual HTTP requests using httpbin."""

    @pytest.fixture
    def base_query(self):
        return BaseQuery()

    @pytest.mark.parametrize('head_safe', [True, False])
    def test_download_file_remote(self, base_query, tmp_path, head_safe):
        """Test downloading from httpbin."""
        url = 'https://httpbin.org/range/1000'
        local_file = tmp_path / 'remote_test.txt'

        response = base_query._download_file(url, str(local_file), head_safe=head_safe)
        assert response.status_code == 200
        assert local_file.exists()
        assert len(local_file.read_bytes()) == 1000

    @pytest.mark.parametrize('head_safe', [True, False])
    def test_download_file_remote_continuation(self, base_query, tmp_path, head_safe):
        """Test downloading with continuation from httpbin."""
        url = 'https://httpbin.org/range/1000'
        local_file = tmp_path / 'remote_test.txt'

        # First get the first 500 bytes as our partial file
        headers = {'Range': 'bytes=0-499'}
        response = requests.get(url, headers=headers)
        assert response.status_code == 206
        assert response.headers['Content-Range'] == 'bytes 0-499/1000'
        partial_content = response.content
        assert len(partial_content) == 500

        # Write the partial content
        local_file.write_bytes(partial_content)

        # Now use _download_file with continuation to get the rest
        response = base_query._download_file(url, str(local_file), continuation=True, head_safe=head_safe)
        assert response.status_code == 206
        assert response.headers['Content-Range'] == 'bytes 500-999/1000'
        assert local_file.exists()

        # Get the complete file for comparison
        complete_response = requests.get(url)
        complete_content = complete_response.content
        assert len(complete_content) == 1000

        # Verify that our partial + continuation matches the complete file
        assert local_file.read_bytes() == complete_content

    @pytest.mark.parametrize('head_safe', [True, False])
    def test_download_file_remote_large(self, base_query, tmp_path, head_safe):
        """Test downloading a larger file from httpbin."""
        url = 'https://httpbin.org/range/10000'
        local_file = tmp_path / 'remote_test_large.txt'

        response = base_query._download_file(url, str(local_file), head_safe=head_safe)
        assert response.status_code == 200
        assert local_file.exists()
        assert len(local_file.read_bytes()) == 10000


def test_session_VO_header():
    """Test that the session header includes both astroquery and pyVO."""
    test_VO_instance = BaseVOQuery()
    assert 'astroquery' in test_VO_instance._session.headers['User-Agent']
    assert 'pyVO' in test_VO_instance._session.headers['User-Agent']


def test_session_nonVO_header():
    """Test that the session header includes astroquery but not pyVO."""
    test_instance = BaseQuery()
    assert 'astroquery' in test_instance._session.headers['User-Agent']
    assert 'pyVO' not in test_instance._session.headers['User-Agent']


def test_session_hooks():
    """Test that the session hooks are properly set."""
    test_instance = BaseQuery()
    assert test_instance._response_hook in test_instance._session.hooks['response']
