import requests
import os
import pytest

from time import mktime
from datetime import datetime

from astropy.config import paths

from astroquery.query import QueryWithLogin
from astroquery import cache_conf

URL1 = "http://fakeurl.edu"
URL2 = "http://fakeurl.ac.uk"

TEXT1 = "Penguin"
TEXT2 = "Walrus"


def _create_response(response_text):
    mock_response = requests.Response()
    mock_response._content = response_text
    mock_response.request = requests.PreparedRequest()
    mock_response.status_code = 200
    return mock_response


@pytest.fixture
def changing_mocked_response(monkeypatch):
    """Provide responses that can change after being queried once."""
    first_responses = {URL1: _create_response(TEXT1), "ceb": _create_response(TEXT1)}
    default_response = _create_response(TEXT2)

    def get_mockreturn(*args, **kwargs):
        return first_responses.pop(args[2], default_response)

    monkeypatch.setattr(requests.Session, "request", get_mockreturn)


class CacheTestClass(QueryWithLogin):
    """Bare bones class for testing caching"""

    def test_func(self, requrl):

        return self._request(method="GET", url=requrl)

    def _login(self, username):

        return self._request(method="GET", url=username).content == "Penguin"


def test_conf():
    cache_conf.reset()

    default_timeout = cache_conf.cache_timeout
    default_active = cache_conf.cache_active

    assert default_timeout == 604800
    assert default_active is True

    with cache_conf.set_temp("cache_timeout", 5):
        assert cache_conf.cache_timeout == 5

    with cache_conf.set_temp("cache_active", False):
        assert cache_conf.cache_active is False

    assert cache_conf.cache_timeout == default_timeout
    assert cache_conf.cache_active == default_active

    cache_conf.cache_timeout = 5
    cache_conf.cache_active = False
    cache_conf.reset()

    assert cache_conf.cache_timeout == default_timeout
    assert cache_conf.cache_active == default_active


def test_basic_caching(changing_mocked_response):
    cache_conf.reset()

    mytest = CacheTestClass()
    assert cache_conf.cache_active

    mytest.clear_cache()
    assert len(os.listdir(mytest.cache_location)) == 0

    resp = mytest.test_func(URL1)
    assert resp.content == TEXT1
    assert len(os.listdir(mytest.cache_location)) == 1

    resp = mytest.test_func(URL2)  # query that has not been cached
    assert resp.content == TEXT2
    assert len(os.listdir(mytest.cache_location)) == 2

    resp = mytest.test_func(URL1)
    assert resp.content == TEXT1  # query that was cached
    assert len(os.listdir(mytest.cache_location)) == 2  # no new cache file

    mytest.clear_cache()
    assert len(os.listdir(mytest.cache_location)) == 0

    resp = mytest.test_func(URL1)
    assert resp.content == TEXT2  # Now get new response


def test_change_location(tmp_path):
    cache_conf.reset()

    mytest = CacheTestClass()
    default_cache_location = mytest.cache_location

    assert paths.get_cache_dir() in str(default_cache_location)
    assert "astroquery" in mytest.cache_location.parts
    assert mytest.name in mytest.cache_location.parts

    new_loc = tmp_path.joinpath("new_dir")
    mytest.cache_location = new_loc
    assert mytest.cache_location == new_loc

    mytest.reset_cache_location()
    assert mytest.cache_location == default_cache_location

    new_loc.mkdir(parents=True, exist_ok=True)
    with paths.set_temp_cache(new_loc):
        assert str(new_loc) in str(mytest.cache_location)
        assert "astroquery" in mytest.cache_location.parts
        assert mytest.name in mytest.cache_location.parts


def test_login(changing_mocked_response):
    cache_conf.reset()

    mytest = CacheTestClass()
    assert cache_conf.cache_active

    mytest.clear_cache()
    assert len(os.listdir(mytest.cache_location)) == 0

    mytest.login("ceb")
    assert mytest.authenticated()
    assert len(os.listdir(mytest.cache_location)) == 0  # request should not be cached

    mytest.login("ceb")
    assert not mytest.authenticated()  # Should not be accessing cache


def test_timeout(changing_mocked_response, monkeypatch):
    cache_conf.reset()

    mytest = CacheTestClass()
    assert cache_conf.cache_active

    mytest.clear_cache()
    assert len(os.listdir(mytest.cache_location)) == 0

    resp = mytest.test_func(URL1)  # should be cached
    assert resp.content == TEXT1

    resp = mytest.test_func(URL1)  # should access cached value
    assert resp.content == TEXT1

    # Changing the file date so the cache will consider it expired
    cache_file = next(mytest.cache_location.iterdir())
    modTime = mktime(datetime(1970, 1, 1).timetuple())
    os.utime(cache_file, (modTime, modTime))

    resp = mytest.test_func(URL1)
    assert resp.content == TEXT2  # now see the new response

    # Testing a cache timeout of "none"
    cache_conf.cache_timeout = None
    # Ensure response can only come from cache.
    monkeypatch.delattr(requests.Session, "request")

    resp = mytest.test_func(URL1)
    assert resp.content == TEXT2  # cache is accessed


def test_deactivate_directly(changing_mocked_response):
    cache_conf.reset()

    mytest = CacheTestClass()
    cache_conf.cache_active = False

    mytest.clear_cache()
    assert len(os.listdir(mytest.cache_location)) == 0

    resp = mytest.test_func(URL1)
    assert resp.content == TEXT1
    assert len(os.listdir(mytest.cache_location)) == 0

    resp = mytest.test_func(URL1)
    assert resp.content == TEXT2
    assert len(os.listdir(mytest.cache_location)) == 0

    cache_conf.reset()
    assert cache_conf.cache_active is True


def test_deactivate_with_set_temp(changing_mocked_response):
    mytest = CacheTestClass()
    with cache_conf.set_temp('cache_active', False):
        mytest.clear_cache()
        assert len(os.listdir(mytest.cache_location)) == 0

        resp = mytest.test_func(URL1)
        assert resp.content == TEXT1
        assert len(os.listdir(mytest.cache_location)) == 0

        resp = mytest.test_func(URL1)
        assert resp.content == TEXT2
        assert len(os.listdir(mytest.cache_location)) == 0

    assert cache_conf.cache_active is True
