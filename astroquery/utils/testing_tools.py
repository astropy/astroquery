# Licensed under a 3-clause BSD style license - see LICENSE.rst

import socket

import pytest

# Import MockResponse to keep the API while it's temporarily factored out to
# a separate file to avoid requiring pytest as a dependency in non-test code
from .mocks import MockResponse

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
