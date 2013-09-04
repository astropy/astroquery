import socket
from astropy.tests.helper import pytest

# save original socket method for restoration
socket_original = socket.socket

@pytest.fixture
def turn_off_internet():
    def guard(*args, **kwargs):
        raise Exception("An attempt was made to connect to the internet")
    setattr(socket, 'socket', guard)
    return socket

@pytest.fixture
def turn_on_internet():
    setattr(socket, 'socket', socket_original)
    return socket
