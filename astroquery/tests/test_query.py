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

# Mock responses for different scenarios
@pytest.fixture
def mock_head_response():
    """Create a mock HEAD response with no content."""
    response = EnhancedMockResponse(b'')  # HEAD response has no content
    response.headers = {
        'Accept-Ranges': 'bytes',
        'Content-Length': str(len(TEST_FILE_CONTENT))
    }
    return response

@pytest.fixture
def mock_response():
    """Create a mock response object with test content and headers."""
    response = EnhancedMockResponse(TEST_FILE_CONTENT)
    response.headers = {
        'Accept-Ranges': 'bytes',
        'Content-Length': str(len(TEST_FILE_CONTENT))
    }
    return response

@pytest.fixture
def mock_response_no_ranges():
    """Create a mock response object without Accept-Ranges header."""
    response = EnhancedMockResponse(TEST_FILE_CONTENT)
    response.headers = {
        'Content-Length': str(len(TEST_FILE_CONTENT))
    }
    return response

@pytest.fixture
def patch_get(request, mock_response, mock_head_response):
    """Patch the requests.Session.request method to return our mock response."""
    mp = request.getfixturevalue("monkeypatch")

    def mock_request(self, method, *args, **kwargs):
        # Handle HEAD requests
        if method == 'HEAD':
            return mock_head_response
            
        # Handle range requests
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
                    'Content-Range': f'bytes {start}-{start + len(TEST_FILE_REMAINDER) - 1}/{len(TEST_FILE_CONTENT)}'
                }
                return response
                
        # Default to normal GET response
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
    """Test downloading with verbose=False."""
    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    response = base_query._download_file(url, str(local_file), verbose=False, head_safe=head_safe)
    assert response.status_code == 200
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

@pytest.mark.parametrize('head_safe', [True, False])
def test_download_file_no_ranges_header(base_query, patch_get_no_ranges, tmp_path, head_safe):
    """Test downloading when server doesn't support partial content."""
    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    # Create a partial file
    local_file.write_bytes(TEST_FILE_PARTIAL)

    response = base_query._download_file(url, str(local_file), continuation=True, head_safe=head_safe)
    assert response.status_code == 200
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

# Remote tests using httpbin
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
