# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import pytest
import requests
import logging
from requests.models import Response
from requests.structures import CaseInsensitiveDict
from astroquery.query import BaseQuery, BaseVOQuery
from astroquery.utils.mocks import MockResponse
from itertools import product

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
        # Set the status and headers of a range request, as a server would
        response._parse_range_header()
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
    test_instance = with_VO(extra_user_agents="test")
    user_agent = test_instance._session.headers['User-Agent']
    assert 'astroquery' in user_agent
    assert 'pyVO' in user_agent
    assert user_agent.endswith("test")
    assert user_agent.count('astroquery') == 1


def test_session_only_VO_header():
    """Test that we can add extra user agents."""
    test_instance = only_VO(extra_user_agents=["agent1", "agent2"])
    user_agent = test_instance._session.headers['User-Agent']
    assert all([string in user_agent for string in ["astroquery", "pyVO", "agent1", "agent2"]])


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


class _ServerResponse(EnhancedMockResponse):
    """A response whose ``content`` is the body sent by `_Server`."""

    @property
    def content(self):
        return self._body

    @content.setter
    def content(self, value):
        self._body = self._content = value


class _Server:
    """A mock server for the download tests below.

    ``body`` is the complete file.  Each GET is answered by the next entry of
    ``plan``: ``'ok'`` sends the requested bytes (honouring a Range header),
    ``'ignore-range'`` sends the whole file with status 200, ``('break', n)``
    sends n bytes and then raises, ``('short', n)`` sends n bytes and ends
    without an error.  ``during`` is called while the body is being sent.
    """

    def __init__(self, monkeypatch, body=TEST_FILE_CONTENT, plan=('ok',), during=None):
        self.body = body
        self.plan = list(plan)
        self.during = during
        self.ranges = []
        server = self

        def request(session, method, url, **kwargs):
            return server.respond(method, dict(session.headers))

        monkeypatch.setattr(requests.Session, 'request', request)

    def respond(self, method, session_headers):
        server = self
        response = _ServerResponse(b'')
        response._body = b''
        response.headers = CaseInsensitiveDict({'Accept-Ranges': 'bytes',
                                                'Content-Length': str(len(self.body))})
        response.status_code = 200
        if method == 'HEAD':
            return response
        action = self.plan.pop(0) if self.plan else 'ok'
        start = 0
        if 'Range' in session_headers and action != 'ignore-range':
            self.ranges.append(session_headers['Range'])
            start = int(session_headers['Range'].split('=')[1].split('-')[0])
            response.status_code = 206
            response.headers['Content-Length'] = str(len(self.body) - start)
            response.headers['Content-Range'] = f'bytes {start}-{len(self.body) - 1}/{len(self.body)}'
        data = self.body[start:]
        response._body = data

        def iter_content(chunk_size=None):
            if isinstance(action, tuple):
                kind, n = action
                yield data[:n]
                if server.during:
                    server.during()
                if kind == 'break':
                    raise requests.exceptions.ChunkedEncodingError("connection broken")
                return
            yield data[:5]
            if server.during:
                server.during()
            yield data[5:]

        response.iter_content = iter_content
        response.raise_for_status = lambda: None
        return response


def _names(path):
    return sorted(p.name for p in path.iterdir())


@pytest.mark.parametrize('as_path', [False, True])
@pytest.mark.parametrize('head_safe', [False, True])
def test_download_interrupted_then_resumed(base_query, monkeypatch, tmp_path, head_safe, as_path):
    """An interrupted transfer never puts partial data at the destination; the
    data received are kept as ``.part`` and a later call resumes from them."""
    local_file = tmp_path / 'test.txt'
    seen = []
    server = _Server(monkeypatch, plan=[('break', len(TEST_FILE_PARTIAL)), 'ok'],
                     during=lambda: seen.append(local_file.exists()))
    dest = local_file if as_path else str(local_file)

    with pytest.raises(requests.exceptions.ChunkedEncodingError):
        base_query._download_file('http://example.com/test.txt', dest, head_safe=head_safe)
    assert _names(tmp_path) == ['test.txt.part']
    assert (tmp_path / 'test.txt.part').read_bytes() == TEST_FILE_PARTIAL

    result = base_query._download_file('http://example.com/test.txt', dest, head_safe=head_safe,
                                       continuation=True)
    assert result == dest
    assert local_file.read_bytes() == TEST_FILE_CONTENT
    assert _names(tmp_path) == ['test.txt']
    assert server.ranges == [f'bytes={len(TEST_FILE_PARTIAL)}-{len(TEST_FILE_CONTENT) - 1}']
    assert seen == [False, False]
    assert 'Range' not in base_query._session.headers


def test_download_short_body_is_not_published(base_query, monkeypatch, tmp_path):
    """A body shorter than Content-Length, without a transport error, is rejected
    and the existing destination file is left untouched."""
    local_file = tmp_path / 'test.txt'
    local_file.write_bytes(b'old version')
    _Server(monkeypatch, plan=[('short', 10)])

    with pytest.raises(OSError, match='incomplete'):
        base_query._download_file('http://example.com/test.txt', str(local_file), continuation=False)
    assert local_file.read_bytes() == b'old version'
    assert (tmp_path / 'test.txt.part').read_bytes() == TEST_FILE_CONTENT[:10]
    assert _names(tmp_path) == ['test.txt', 'test.txt.part']


def test_download_server_ignores_range(base_query, monkeypatch, tmp_path):
    """If the server answers a Range request with the whole file, the partial
    data are discarded instead of being prepended to it."""
    (tmp_path / 'test.txt.part').write_bytes(TEST_FILE_PARTIAL)
    _Server(monkeypatch, plan=['ok', 'ignore-range'])

    base_query._download_file('http://example.com/test.txt', str(tmp_path / 'test.txt'),
                              continuation=True)
    assert (tmp_path / 'test.txt').read_bytes() == TEST_FILE_CONTENT
    assert _names(tmp_path) == ['test.txt']


def test_download_destination_kept_during_transfer(base_query, monkeypatch, tmp_path):
    """While a file is being downloaded again, readers still see the old complete
    file, which is replaced only at the end."""
    local_file = tmp_path / 'test.txt'
    local_file.write_bytes(b'previous complete file')
    seen = []
    _Server(monkeypatch, during=lambda: seen.append(local_file.read_bytes()))

    base_query._download_file('http://example.com/test.txt', str(local_file), continuation=False)
    assert seen == [b'previous complete file']
    assert local_file.read_bytes() == TEST_FILE_CONTENT
    assert _names(tmp_path) == ['test.txt']


@pytest.mark.parametrize('content', [b'', TEST_FILE_CONTENT, TEST_FILE_CONTENT + b'extra'])
def test_download_existing_part(base_query, monkeypatch, tmp_path, content):
    """An empty, complete or oversized ``.part`` file gives the right result."""
    (tmp_path / 'test.txt.part').write_bytes(content)
    _Server(monkeypatch)
    base_query._download_file('http://example.com/test.txt', str(tmp_path / 'test.txt'),
                              continuation=True)
    assert (tmp_path / 'test.txt').read_bytes() == TEST_FILE_CONTENT
    assert _names(tmp_path) == ['test.txt']


def test_download_legacy_partial_destination(base_query, monkeypatch, tmp_path):
    """An incomplete destination file written by an older astroquery is resumed."""
    (tmp_path / 'test.txt').write_bytes(TEST_FILE_PARTIAL)
    server = _Server(monkeypatch)
    base_query._download_file('http://example.com/test.txt', str(tmp_path / 'test.txt'),
                              continuation=True)
    assert (tmp_path / 'test.txt').read_bytes() == TEST_FILE_CONTENT
    assert server.ranges == [f'bytes={len(TEST_FILE_PARTIAL)}-{len(TEST_FILE_CONTENT) - 1}']
    assert _names(tmp_path) == ['test.txt']


def test_download_stale_part_removed(base_query, monkeypatch, tmp_path):
    """A leftover ``.part`` is removed by a successful download that did not use it."""
    (tmp_path / 'test.txt.part').write_bytes(b'stale')
    _Server(monkeypatch)
    base_query._download_file('http://example.com/test.txt', str(tmp_path / 'test.txt'),
                              continuation=False)
    assert _names(tmp_path) == ['test.txt']


def test_download_failed_rename_keeps_data_as_part(base_query, monkeypatch, tmp_path):
    """If the final rename fails, the downloaded data are kept as ``.part`` and no
    temporary file is left behind."""
    import astroquery.query
    _Server(monkeypatch)
    real_replace = astroquery.query._replace_file

    def failing_replace(src, dst):
        if dst.endswith('test.txt'):
            raise PermissionError("denied")
        return real_replace(src, dst)

    monkeypatch.setattr(astroquery.query, '_replace_file', failing_replace)
    with pytest.raises(PermissionError):
        base_query._download_file('http://example.com/test.txt', str(tmp_path / 'test.txt'))
    assert _names(tmp_path) == ['test.txt.part']
    assert (tmp_path / 'test.txt.part').read_bytes() == TEST_FILE_CONTENT


def test_download_head_length_differs_from_get(base_query, monkeypatch, tmp_path):
    """The size check uses the Content-Length of the GET response, not of the HEAD."""
    server = _Server(monkeypatch)
    real_respond = server.respond

    def respond(method, session_headers):
        response = real_respond(method, session_headers)
        if method == 'HEAD':
            response.headers['Content-Length'] = '5'
        return response

    server.respond = respond
    base_query._download_file('http://example.com/test.txt', str(tmp_path / 'test.txt'), head_safe=True)
    assert (tmp_path / 'test.txt').read_bytes() == TEST_FILE_CONTENT
    assert _names(tmp_path) == ['test.txt']


def test_download_wrong_content_range(base_query, monkeypatch, tmp_path):
    """A 206 response for a different range than requested is not appended."""
    (tmp_path / 'test.txt.part').write_bytes(TEST_FILE_PARTIAL)
    server = _Server(monkeypatch)
    real_respond = server.respond

    def respond(method, session_headers):
        response = real_respond(method, session_headers)
        if 'Range' in session_headers:
            response.headers['Content-Range'] = f'bytes 0-{len(TEST_FILE_CONTENT) - 1}/{len(TEST_FILE_CONTENT)}'
        return response

    server.respond = respond
    base_query._download_file('http://example.com/test.txt', str(tmp_path / 'test.txt'), continuation=True)
    assert (tmp_path / 'test.txt').read_bytes() == TEST_FILE_CONTENT
    assert _names(tmp_path) == ['test.txt']


def test_download_failed_resume_keeps_larger_part(base_query, monkeypatch, tmp_path):
    """A resume that fails with less data than the existing ``.part`` leaves the ``.part`` alone."""
    (tmp_path / 'test.txt.part').write_bytes(TEST_FILE_PARTIAL)
    _Server(monkeypatch)
    import astroquery.query

    def failing_copy(src, dst):
        with open(dst, 'wb') as f:
            f.write(b'Th')
        raise KeyboardInterrupt

    monkeypatch.setattr(astroquery.query.shutil, 'copyfile', failing_copy)
    with pytest.raises(KeyboardInterrupt):
        base_query._download_file('http://example.com/test.txt', str(tmp_path / 'test.txt'),
                                  continuation=True)
    assert _names(tmp_path) == ['test.txt.part']
    assert (tmp_path / 'test.txt.part').read_bytes() == TEST_FILE_PARTIAL


def test_download_destination_in_use_but_complete(base_query, monkeypatch, tmp_path):
    """If dest cannot be replaced (e.g. open on Windows) but already holds the
    complete file, the download succeeds and leaves no temporary file."""
    import astroquery.query
    local_file = tmp_path / 'test.txt'
    local_file.write_bytes(TEST_FILE_CONTENT)
    _Server(monkeypatch)
    real_replace = astroquery.query._replace_file

    def failing_replace(src, dst):
        if dst.endswith('test.txt'):
            raise PermissionError("in use")
        return real_replace(src, dst)

    monkeypatch.setattr(astroquery.query, '_replace_file', failing_replace)
    base_query._download_file('http://example.com/test.txt', str(local_file), continuation=False)
    assert local_file.read_bytes() == TEST_FILE_CONTENT
    assert _names(tmp_path) == ['test.txt']


def test_download_verbose_false_and_cache(base_query, monkeypatch, tmp_path):
    """verbose=False writes atomically too, and cache=True with a different-size
    file replaces it only at the end."""
    local_file = tmp_path / 'test.txt'
    local_file.write_bytes(b'short')
    _Server(monkeypatch)
    base_query._download_file('http://example.com/test.txt', str(local_file), cache=True,
                              continuation=False, verbose=False)
    assert local_file.read_bytes() == TEST_FILE_CONTENT
    assert _names(tmp_path) == ['test.txt']


@pytest.mark.skipif('not hasattr(os, "symlink")')
def test_download_through_symlink(base_query, monkeypatch, tmp_path):
    """A symlink at the destination is kept and its target is updated."""
    target = tmp_path / 'target.txt'
    target.write_bytes(b'old')
    link = tmp_path / 'link.txt'
    try:
        os.symlink(target, link)
    except OSError:
        pytest.skip("symlinks not permitted")
    _Server(monkeypatch)
    base_query._download_file('http://example.com/test.txt', str(link), continuation=False)
    assert link.is_symlink()
    assert target.read_bytes() == TEST_FILE_CONTENT
