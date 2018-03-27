from ...utils.url_helpers import urljoin_keep_path

BASE_URL = 'http://example.com/foo/'


def test_urljoin_keep_path():
    assert urljoin_keep_path(BASE_URL, '') == BASE_URL
    assert urljoin_keep_path('', BASE_URL) == BASE_URL
    assert urljoin_keep_path(BASE_URL, 'bar') == 'http://example.com/foo/bar'
    assert urljoin_keep_path(BASE_URL, '/bar') == 'http://example.com/bar'
