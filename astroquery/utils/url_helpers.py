# Licensed under a 3-clause BSD style license - see LICENSE.rst
try:
    from astropy.extern.six.moves.urllib_parse import SplitResult, urlsplit
except ImportError:
    from six.moves.urllib_parse import SplitResult, urlsplit
import os.path


def urljoin_keep_path(url, path):
    """Join a base URL and a relative or absolute path. The important
    difference to :func:`urlparse.urljoin` (or
    :func:`urllib.parse.urljoin` on Python 3) is that `urljoin_keep_path`
    does not remove the last directory of the path found in the parameter
    `url` if it is in relative form. Compare the examples below to verify.

    Examples
    --------
    >>> urljoin_keep_path('http://example.com/foo', 'bar')
    'http://example.com/foo/bar'
    >>> from astropy.extern.six.moves.urllib import parse as urlparse
    >>> urlparse.urljoin('http://example.com/foo', 'bar')
    'http://example.com/bar'

    """
    # urlparse.SplitResult doesn't allow overriding attribute values,
    # so ``splitted_url.path = ...`` is not possible here, unfortunately.
    splitted_url = urlsplit(url)
    return SplitResult(splitted_url.scheme,
                       splitted_url.netloc,
                       join(splitted_url.path, path),
                       splitted_url.query,
                       splitted_url.fragment).geturl()


def join(a, *p):
    """Taken from python posixpath."""
    sep = '/'
    path = a
    if not p:
        path[:0] + sep
    for b in p:
        if b.startswith(sep):
            path = b
        elif not path or path.endswith(sep):
            path += b
        else:
            path += sep + b
    return path
