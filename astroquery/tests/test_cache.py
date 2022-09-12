import pytest
import requests
import os

from time import sleep
from pathlib import Path

from astropy.config import paths

from astroquery.query import QueryWithLogin
from astroquery import conf

URL1 = "http://fakeurl.edu"
URL2 = "http://fakeurl.ac.uk"

TEXT1 = "Penguin"
TEXT2 = "Walrus"


def set_response(resp_text, resp_status=200):
    """Function that allows us to set a specific mock response for cache testing"""

    def get_mockreturn(url, *args, **kwargs):
        """Generate a mock return to a requests call"""

        myresp = requests.Response()
        myresp._content = resp_text
        myresp.request = requests.PreparedRequest()
        myresp.status_code = resp_status

        return myresp

    requests.Session.request = get_mockreturn


class TestClass(QueryWithLogin):
    """Bare bones class for testing caching"""

    def test_func(self, requrl):

        return self._request(method="GET", url=requrl)

    def _login(self, username):

        resp = self._request(method="GET", url=username)

        if resp.content == "Penguin":
            return True
        else:
            return False


def test_conf():
    default_timeout = conf.cache_timeout
    default_active = conf.cache_active

    assert default_timeout == 604800
    assert default_active is True

    with conf.set_temp("cache_timeout", 5):
        assert conf.cache_timeout == 5

    with conf.set_temp("cache_active", False):
        assert conf.cache_active is False

    assert conf.cache_timeout == default_timeout
    assert conf.cache_active == default_active

    conf.cache_timeout = 5
    conf.cache_active = False
    conf.reset()

    assert conf.cache_timeout == default_timeout
    assert conf.cache_active == default_active


def test_basic_caching():

    mytest = TestClass()
    assert conf.cache_active

    mytest.clear_cache()
    assert len(os.listdir(mytest.get_cache_location())) == 0

    set_response(TEXT1)

    resp = mytest.test_func(URL1)
    assert resp.content == TEXT1
    assert len(os.listdir(mytest.get_cache_location())) == 1

    set_response(TEXT2)

    resp = mytest.test_func(URL2)  # query that has not been cached
    assert resp.content == TEXT2
    assert len(os.listdir(mytest.get_cache_location())) == 2

    resp = mytest.test_func(URL1)
    assert resp.content == TEXT1  # query that was cached
    assert len(os.listdir(mytest.get_cache_location())) == 2  # no new cache file

    mytest.clear_cache()
    assert len(os.listdir(mytest.get_cache_location())) == 0

    resp = mytest.test_func(URL1)
    assert resp.content == TEXT2  # Now get new response


def test_change_location(tmpdir):

    mytest = TestClass()
    default_cache_location = mytest.get_cache_location()

    assert paths.get_cache_dir() in default_cache_location
    assert "astroquery" in mytest.get_cache_location()
    assert mytest.name in mytest.get_cache_location()

    new_loc = os.path.join(tmpdir, "new_dir")
    mytest.cache_location = new_loc
    assert mytest.get_cache_location() == new_loc

    mytest.reset_cache_location()
    assert mytest.get_cache_location() == default_cache_location

    Path(new_loc).mkdir(parents=True, exist_ok=True)
    with paths.set_temp_cache(new_loc):
        assert new_loc in mytest.get_cache_location()
        assert "astroquery" in mytest.get_cache_location()
        assert mytest.name in mytest.get_cache_location()


def test_login():

    mytest = TestClass()
    assert conf.cache_active

    mytest.clear_cache()
    assert len(os.listdir(mytest.get_cache_location())) == 0

    set_response(TEXT1)  # Text 1 is set as the approved password

    mytest.login("ceb")
    assert mytest.authenticated()
    assert len(os.listdir(mytest.get_cache_location())) == 0  # request should not be cached

    set_response(TEXT2)  # Text 2 is not the approved password

    mytest.login("ceb")
    assert not mytest.authenticated()  # Should not be accessing cache


def test_timeout():

    mytest = TestClass()
    assert conf.cache_active

    mytest.clear_cache()
    assert len(os.listdir(mytest.get_cache_location())) == 0

    conf.cache_timeout = 2  # Set to 2 sec so we can reach timeout easily

    set_response(TEXT1)  # setting the response

    resp = mytest.test_func(URL1)  # should be cached
    assert resp.content == TEXT1

    set_response(TEXT2)  # changing the respont

    resp = mytest.test_func(URL1)  # should access cached value
    assert resp.content == TEXT1

    sleep(2)  # run out cache time
    resp = mytest.test_func(URL1)
    assert resp.content == TEXT2  # no see the new response


def test_deactivate():

    mytest = TestClass()
    conf.cache_active = False

    mytest.clear_cache()
    assert len(os.listdir(mytest.get_cache_location())) == 0

    set_response(TEXT1)

    resp = mytest.test_func(URL1)
    assert resp.content == TEXT1
    assert len(os.listdir(mytest.get_cache_location())) == 0

    set_response(TEXT2)

    resp = mytest.test_func(URL1)
    assert resp.content == TEXT2
    assert len(os.listdir(mytest.get_cache_location())) == 0
