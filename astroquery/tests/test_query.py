# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest
import requests
import logging
from pathlib import Path
from requests.models import Response
from requests.structures import CaseInsensitiveDict
from astroquery.query import BaseQuery, BaseVOQuery
from astroquery.utils.mocks import MockResponse
from itertools import product

# Test data directory
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

# Test data files
TEST_FILE_CONTENT = b'This is a test file with some content.'
TEST_FILE_PARTIAL = b'This is a test file'
TEST_FILE_REMAINDER = b' with some content.'

# Get the logger for astroquery
log = logging.getLogger('astroquery')


class with_VO(BaseVOQuery, BaseQuery):
    pass


class without_VO(BaseQuery):
    pass


class only_VO(BaseVOQuery):
    pass


class EnhancedMockResponse(MockResponse):
    """A mock response that supports range requests."""

    def __init__(self, content, accept_ranges=True):
        """Initialize the response with content."""
        self.headers = CaseInsensitiveDict()
        self._range_start = None
        self._range_end = None
        super().__init__(content=content)
        if accept_ranges:
            self.headers['accept-ranges'] = 'bytes'
        self.headers['content-length'] = str(len(self._content))

    def _parse_range_header(self):
        """Parse range header and set internal range values."""
        if 'Range' in self.headers:
            range_header = self.headers['Range']
            start_str = range_header.split('=')[1].split('-')[0]
            end_str = range_header.split('-')[1]
            self._range_start = int(start_str)
            self._range_end = int(end_str) if end_str else len(self._content) - 1
            self.status_code = 206
            # Set content-range header to include total length
            self.headers['content-range'] = f'bytes {self._range_start}-{self._range_end}/{len(self._content)}'
            # Set content-length to length of range being returned
            range_length = self._range_end - self._range_start + 1
            self.headers['content-length'] = str(range_length)
        else:
            self._range_start = None
            self._range_end = None
            self.status_code = 200
            self.headers['content-length'] = str(len(self._content))

    @property
    def content(self):
        """Get the content, respecting any range request."""
        self._parse_range_header()
        if self._range_start is not None:
            # Return only the requested range
            return self._content[self._range_start:self._range_end + 1]
        return self._content

    @content.setter
    def content(self, value):
        """Set the content and update content-length header."""
        self._content = value
        self.headers['content-length'] = str(len(value))

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP Error: {self.status_code}")

    def iter_content(self, chunk_size=None):
        """Iterate over content respecting range request."""
        if chunk_size is None:
            chunk_size = 8192
        content = self.content  # This will respect any range request
        for ii in range(0, len(content), chunk_size):
            yield content[ii:ii + chunk_size]

    def close(self):
        self._content = None


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

    def mock_request(self, method, url, **kwargs):
        if method == 'HEAD':
            response = mock_head_response
            response.headers['content-length'] = str(len(TEST_FILE_CONTENT))
            return response

        response = EnhancedMockResponse(TEST_FILE_CONTENT)
        # Copy any headers from the session
        for key, value in self.headers.items():
            response.headers[key] = value
        return response

    monkeypatch.setattr(requests.Session, 'request', mock_request)


@pytest.mark.parametrize(
    'head_safe,continuation,initial_content,cache,log_level',
    list(product(
        [False, True],  # head_safe
        [False, True],  # continuation
        [None, TEST_FILE_PARTIAL, TEST_FILE_CONTENT, b''],  # initial_content
        [False, True],  # cache
        ['DEBUG', 'INFO'],  # log_level
    ))
)
def test_download_file_with_existing(base_query, patch_get, tmp_path, head_safe,
                                     continuation, initial_content, cache, log_level):
    """Test downloading with various combinations of head_safe, continuation, cache, and existing file content."""
    # Set logging level for this test
    log.setLevel(log_level)

    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    # Create initial file state if initial_content is not None
    if initial_content is not None:
        local_file.write_bytes(initial_content)

    local_filepath = base_query._download_file(
        url, str(local_file),
        head_safe=head_safe,
        continuation=continuation,
        cache=cache)

    assert local_filepath == str(local_file)
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

    # Reset logging level after test
    log.setLevel('INFO')


@pytest.mark.parametrize(
    'head_safe,log_level',
    list(product(
        [True, False],  # head_safe
        ['DEBUG', 'INFO'],  # log_level
    ))
)
def test_download_file_basic(base_query, patch_get, tmp_path, head_safe, log_level):
    """Test basic file download functionality."""
    # Set logging level for this test
    log.setLevel(log_level)

    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    local_filepath = base_query._download_file(url, str(local_file), head_safe=head_safe)
    assert local_filepath == str(local_file)
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

    # Reset logging level after test
    log.setLevel('INFO')


@pytest.mark.parametrize(
    'head_safe,log_level',
    list(product(
        [True, False],  # head_safe
        ['DEBUG', 'INFO'],  # log_level
    ))
)
def test_download_file_no_verbose(base_query, patch_get, tmp_path, head_safe, log_level):
    """Test downloading without progress bar."""
    # Set logging level for this test
    log.setLevel(log_level)

    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    local_filepath = base_query._download_file(url, str(local_file), verbose=False, head_safe=head_safe)
    assert local_filepath == str(local_file)
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

    # Reset logging level after test
    log.setLevel('INFO')


@pytest.mark.parametrize(
    'head_safe,log_level',
    list(product(
        [True, False],  # head_safe
        ['DEBUG', 'INFO'],  # log_level
    ))
)
def test_download_file_no_ranges_header(base_query, mock_response_no_ranges, monkeypatch,
                                        tmp_path, head_safe, log_level):
    """Test downloading when server doesn't support range requests."""
    # Set logging level for this test
    log.setLevel(log_level)

    def mock_request(method, url, headers=None, **kwargs):
        if method == 'HEAD':
            return mock_response_no_ranges
        return mock_response_no_ranges

    monkeypatch.setattr(requests.Session, 'request', mock_request)

    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    local_filepath = base_query._download_file(url, str(local_file), head_safe=head_safe)
    assert local_filepath == str(local_file)
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

    # Reset logging level after test
    log.setLevel('INFO')


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

        local_filepath = base_query._download_file(url, str(local_file), head_safe=head_safe)
        assert local_filepath == str(local_file)
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
        local_filepath = base_query._download_file(url, str(local_file), continuation=True, head_safe=head_safe)
        assert local_filepath == str(local_file)
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

        local_filepath = base_query._download_file(url, str(local_file), head_safe=head_safe)
        assert local_filepath == str(local_file)
        assert local_file.exists()
        assert len(local_file.read_bytes()) == 10000


def test_session_VO_header():
    """Test that the session header includes both astroquery and pyVO."""
    test_instance = with_VO()
    user_agent = test_instance._session.headers['User-Agent']
    assert 'astroquery' in user_agent
    assert 'pyVO' in user_agent
    assert user_agent.count('astroquery') == 1


def test_session_nonVO_header():
    """Test that the session header includes astroquery but not pyVO."""
    test_instance = without_VO()
    user_agent = test_instance._session.headers['User-Agent']
    assert 'astroquery' in user_agent
    assert 'pyVO' not in user_agent
    assert user_agent.count('astroquery') == 1


def test_session_hooks():
    """Test that the session hooks are properly set."""
    # Test that we don't override the session in the BaseVOQuery
    test_instance = with_VO()
    assert len(test_instance._session.hooks['response']) > 0
    test_VO_instance = only_VO()
    assert len(test_VO_instance._session.hooks['response']) == 0


@pytest.mark.parametrize('log_level', ['DEBUG', 'INFO'])
def test_download_file_caching(base_query, patch_get, tmp_path, log_level):
    """Test that caching works correctly with different file states."""
    # Set logging level for this test
    log.setLevel(log_level)

    url = 'http://example.com/test.txt'
    local_file = tmp_path / 'test.txt'

    # First download with cache=True
    local_filepath = base_query._download_file(url, str(local_file), cache=True)
    assert local_filepath == str(local_file)
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

    # Second download with cache=True should use cached file
    local_filepath = base_query._download_file(url, str(local_file), cache=True)
    assert local_filepath == str(local_file)
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

    # Download with cache=False should redownload
    local_filepath = base_query._download_file(url, str(local_file), cache=False)
    assert local_filepath == str(local_file)
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

    # Test with partial file
    local_file.write_bytes(TEST_FILE_PARTIAL)
    local_filepath = base_query._download_file(url, str(local_file), cache=True)
    assert local_filepath == str(local_file)
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

    # Test with wrong size file
    local_file.write_bytes(b'wrong size')
    local_filepath = base_query._download_file(url, str(local_file), cache=True)
    assert local_filepath == str(local_file)
    assert local_file.exists()
    assert local_file.read_bytes() == TEST_FILE_CONTENT

    # Reset logging level after test
    log.setLevel('INFO')
