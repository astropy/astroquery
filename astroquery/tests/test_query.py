# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astroquery.query import BaseQuery, BaseVOQuery
import os
import pytest
import requests
from pathlib import Path
from astroquery.utils.mocks import MockResponse

# Test data directory
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

# Test data files
TEST_FILE = DATA_DIR / 'test_file.txt'
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
        self._content_consumed = False
        self._original_content = content  # Keep original content for assertions

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP Error: {self.status_code}")

    def iter_content(self, chunk_size=None):
        if chunk_size is None:
            chunk_size = 8192
        content = self._content
        for i in range(0, len(content), chunk_size):
            yield content[i:i + chunk_size]

    def close(self):
        self._content_consumed = True

    @property
    def content(self):
        if self._content_consumed:
            return self._original_content  # Return original content for assertions
        return self._content

    @content.setter
    def content(self, value):
        self._content = value
        self._original_content = value
        self._content_consumed = False

@pytest.fixture
def mock_response():
    """Create a mock response object with test content and headers."""
    response = EnhancedMockResponse(TEST_FILE_CONTENT)
    response.headers = {
        'Accept-Ranges': 'bytes',
        'Content-Length': str(len(TEST_FILE_CONTENT)),
        'Content-Type': 'application/octet-stream'
    }
    return response

@pytest.fixture
def mock_response_no_ranges():
    """Create a mock response object without Accept-Ranges header."""
    response = EnhancedMockResponse(TEST_FILE_CONTENT)
    response.headers = {
        'Content-Length': str(len(TEST_FILE_CONTENT)),
        'Content-Type': 'application/octet-stream'
    }
    return response

@pytest.fixture
def patch_get(request, mock_response):
    """Patch the requests.Session.request method to return our mock response."""
    mp = request.getfixturevalue("monkeypatch")

    def mock_request(self, *args, **kwargs):
        # Check for Range header in both session and request headers
        range_header = None
        if hasattr(self, 'headers') and 'Range' in self.headers:
            range_header = self.headers['Range']
        elif 'headers' in kwargs and 'Range' in kwargs['headers']:
            range_header = kwargs['headers']['Range']

        if range_header:
            # Simulate partial content response
            start = int(range_header.split('=')[1].split('-')[0])
            if start == len(TEST_FILE_PARTIAL):
                response = EnhancedMockResponse(TEST_FILE_REMAINDER)
                response.headers = {
                    'Accept-Ranges': 'bytes',
                    'Content-Length': str(len(TEST_FILE_REMAINDER)),
                    'Content-Range': f'bytes {start}-{start + len(TEST_FILE_REMAINDER) - 1}/{len(TEST_FILE_CONTENT)}',
                    'Content-Type': 'application/octet-stream'
                }
                return response
        return mock_response

    mp.setattr(requests.Session, 'request', mock_request)
    return mp

@pytest.fixture
def patch_get_no_ranges(request, mock_response_no_ranges):
    """Patch the requests.Session.request method to return response without Accept-Ranges."""
    mp = request.getfixturevalue("monkeypatch")

    def mock_request(*args, **kwargs):
        return mock_response_no_ranges

    mp.setattr(requests.Session, 'request', mock_request)
    return mp

@pytest.fixture
def base_query():
    """Create a BaseQuery instance for testing."""
    return BaseQuery()

def test_download_file_basic(base_query, patch_get, tmp_path):
    """Test basic file download functionality."""
    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    response = base_query._download_file(url, str(local_file))
    assert response.content == TEST_FILE_CONTENT
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

def test_download_file_continuation(base_query, patch_get, tmp_path):
    """Test downloading with continuation (partial file exists)."""
    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    # Create a partial file with only the first part
    local_file.write_bytes(TEST_FILE_PARTIAL)

    response = base_query._download_file(url, str(local_file), continuation=True)
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

def test_download_file_no_continuation(base_query, patch_get, tmp_path):
    """Test downloading without continuation (partial file exists)."""
    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    # Create a partial file
    local_file.write_bytes(b'This is a partial')

    response = base_query._download_file(url, str(local_file), continuation=False)
    assert response.content == TEST_FILE_CONTENT
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

def test_download_file_existing_complete(base_query, patch_get, tmp_path):
    """Test downloading when file already exists with correct size."""
    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    # Create a complete file with correct size
    local_file.write_bytes(TEST_FILE_CONTENT)

    response = base_query._download_file(url, str(local_file))
    assert response.content == TEST_FILE_CONTENT
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

def test_download_file_existing_wrong_size(base_query, patch_get, tmp_path):
    """Test downloading when file exists but has wrong size."""
    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    # Create a file with wrong size
    local_file.write_bytes(b'Wrong size content')

    response = base_query._download_file(url, str(local_file))
    assert response.content == TEST_FILE_CONTENT
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

def test_download_file_head_safe(base_query, patch_get, tmp_path):
    """Test downloading with head_safe=True."""
    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    response = base_query._download_file(url, str(local_file), head_safe=True)
    assert response.content == TEST_FILE_CONTENT
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

def test_download_file_no_verbose(base_query, patch_get, tmp_path):
    """Test downloading with verbose=False."""
    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    response = base_query._download_file(url, str(local_file), verbose=False)
    assert response.content == TEST_FILE_CONTENT
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

def test_download_file_no_ranges_header(base_query, patch_get_no_ranges, tmp_path):
    """Test downloading when server doesn't support partial content."""
    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    # Create a partial file
    local_file.write_bytes(TEST_FILE_PARTIAL)

    response = base_query._download_file(url, str(local_file), continuation=True)
    assert response.content == TEST_FILE_CONTENT
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

# Remote tests using httpbin
@pytest.mark.remote_data
class TestDownloadFileRemote:
    """Test _download_file with actual HTTP requests using httpbin."""

    @pytest.fixture
    def base_query(self):
        return BaseQuery()

    def test_download_file_remote(self, base_query, tmp_path):
        """Test downloading from httpbin."""
        url = 'https://httpbin.org/range/1000'
        local_file = tmp_path / 'remote_test.txt'

        response = base_query._download_file(url, str(local_file))
        assert response.status_code == 200
        assert local_file.exists()
        assert len(local_file.read_bytes()) == 1000

    def test_download_file_remote_continuation(self, base_query, tmp_path):
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
        response = base_query._download_file(url, str(local_file), continuation=True)
        assert response.status_code == 206
        assert response.headers['Content-Range'] == 'bytes 500-999/1000'
        assert local_file.exists()

        # Get the complete file for comparison
        complete_response = requests.get(url)
        complete_content = complete_response.content
        assert len(complete_content) == 1000

        # Verify that our partial + continuation matches the complete file
        assert local_file.read_bytes() == complete_content

    def test_download_file_remote_large(self, base_query, tmp_path):
        """Test downloading a larger file from httpbin."""
        url = 'https://httpbin.org/range/10000'
        local_file = tmp_path / 'remote_test_large.txt'

        response = base_query._download_file(url, str(local_file))
        assert response.status_code == 200
        assert local_file.exists()
        assert len(local_file.read_bytes()) == 10000

class with_VO(BaseVOQuery, BaseQuery):
    pass


class without_VO(BaseQuery):
    pass


class only_VO(BaseVOQuery):
    pass


def test_session_VO_header():
    test_instance = with_VO()
    user_agent = test_instance._session.headers['User-Agent']
    assert 'astroquery' in user_agent
    assert 'pyVO' in user_agent
    assert user_agent.count('astroquery') == 1


def test_session_nonVO_header():
    test_instance = without_VO()
    user_agent = test_instance._session.headers['User-Agent']
    assert 'astroquery' in user_agent
    assert 'pyVO' not in user_agent
    assert user_agent.count('astroquery') == 1


def test_session_hooks():
    # Test that we don't override the session in the BaseVOQuery
    test_instance = with_VO()
    assert len(test_instance._session.hooks['response']) > 0

    test_VO_instance = only_VO()
    assert len(test_VO_instance._session.hooks['response']) == 0
