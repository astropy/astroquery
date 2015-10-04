# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import socket
import json

from astropy.tests.helper import pytest

# save original socket method for restoration
socket_original = socket.socket


@pytest.fixture
def turn_off_internet(verbose=False):
    __tracebackhide__ = True
    if verbose:
        print("Internet access disabled")

    def guard(*args, **kwargs):
        pytest.fail("An attempt was made to connect to the internet")
    setattr(socket, 'socket', guard)
    return socket


@pytest.fixture
def turn_on_internet(verbose=False):
    if verbose:
        print("Internet access enabled")
    setattr(socket, 'socket', socket_original)
    return socket


class MockResponse(object):
    """
    A mocked/non-remote version of `astroquery.query.AstroResponse`
    """

    def __init__(self, content=None, url=None, headers={},
                 content_type=None, stream=False, auth=None, status_code=200):
        assert content is None or hasattr(content, 'decode')
        self.content = content
        self.raw = content
        self.headers = headers
        if content_type is not None:
            self.headers.update({'Content-Type': content_type})
        self.url = url
        self.auth = auth
        self.status_code = status_code

    def iter_lines(self):
        c = self.content.split(b"\n")
        for l in c:
            yield l

    def raise_for_status(self):
        pass

    def json(self):
        try:
            return json.loads(self.content)
        except TypeError:
            return json.loads(self.content.decode('utf-8'))

    @property
    def text(self):
        return self.content.decode(errors='replace')
