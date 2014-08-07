# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import abc
import pickle
import hashlib
import requests
import os
import warnings

from astropy.extern import six
from astropy.config import paths

__all__ = ['BaseQuery', 'QueryWithLogin']


class AstroResponse(object):

    def __init__(self, response=None, url=None, encoding=None, content=None):
        if response is None:
            self.url = url
            self.encoding = encoding
            self.content = content
        elif isinstance(response, requests.Response):
            self.url = response.url
            self.encoding = response.encoding
            self.content = response.content
        elif not hasattr(response, 'content'):
            raise TypeError("{0} is not a requests.Response".format(response))
        elif not isinstance(response, requests.Response):
            self.url = response.url
            self.content = response.content
            warnings.warn("Response has 'content' attribute but is not a "
                          "requests.Response object.  This is expected when "
                          "running local tests but not otherwise.")

    def to_cache(self, cache_file):
        with open(cache_file, "wb") as f:
            pickle.dump(self, f)


class AstroQuery(object):

    def __init__(self, method, url, params=None, data=None, headers=None,
                 files=None, timeout=None):
        self.method = method
        self.url = url
        self.params = params
        self.data = data
        self.headers = headers
        self.files = files
        self._hash = None
        self.timeout = timeout

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        if hasattr(value, 'to'):
            self._timeout = value.to(u.s).value
        else:
            self._timeout = value

    def request(self, session, cache_location=None):
        return AstroResponse(session.request(self.method, self.url,
                                             params=self.params,
                                             data=self.data,
                                             headers=self.headers,
                                             files=self.files,
                                             timeout=self.timeout))

    def hash(self):
        if self._hash is None:
            request_key = (self.method, self.url)
            for k in (self.params, self.data, self.headers, self.files):
                if isinstance(k, dict):
                    request_key += (tuple(sorted(k.items())),)
                elif isinstance(k, tuple) or isinstance(k, list):
                    request_key += (tuple(sorted(k)),)
                elif k is None:
                    request_key += (None,)
                elif isinstance(k, six.string_types):
                    request_key += (k,)
                else:
                    raise TypeError("{0} must be a dict, tuple, str, or list")
            self._hash = hashlib.sha224(pickle.dumps(request_key)).hexdigest() 
        return self._hash

    def request_file(self, cache_location):
        return os.path.join(cache_location, self.hash() + ".pickle")

    def from_cache(self, cache_location):
        request_file = self.request_file(cache_location)
        try:
            with open(request_file, "rb") as f:
                response = pickle.load(f)
            if not isinstance(response, AstroResponse):
                response = None
        except:
            response = None
        return response


@six.add_metaclass(abc.ABCMeta)
class BaseQuery(object):
    """
    This is the base class for all the query classes in astroquery. It
    is implemented as an abstract class and must not be directly instantiated.
    """

    def __init__(self):
        self.__session = requests.session()
        self.cache_location = os.path.join(paths.get_cache_dir(), 'astroquery',
                                           self.__class__.__name__.split("Class")[0])
        if not os.path.exists(self.cache_location):
            os.makedirs(self.cache_location)
        self._cache_active = True

    def __call__(self, *args, **kwargs):
        """ init a fresh copy of self """
        return self.__class__(*args, **kwargs)

    def _request(self, method, url, params=None, data=None, headers=None,
                files=None, save=False, savedir='', timeout=None):
        """
        A generic HTTP request method, similar to `requests.Session.request` but
        with added caching-related tools

        This is a low-level method not generally intended for use by astroquery
        end-users.  As such, it is likely to be renamed to, e.g., `_request` in
        the near future.

        Parameters
        ----------
        method : 'GET' or 'POST'
        url : str
        params : None or dict
        data : None or dict
        headers : None or dict
        files : None or dict
            See `requests.request`
        save : bool
            Whether to save the file to a local directory.  Caching will happen independent of
            this parameter if `BaseQuery.cache_location` is set, but the save location can be
            overridden if ``save==True``
        savedir : str
            The location to save the local file if you want to save it
            somewhere other than `BaseQuery.cache_location`
        """
        if save:
            local_filename = url.split('/')[-1]
            local_filepath = os.path.join(self.cache_location or savedir or '.', local_filename)
            print("Downloading {0}...".format(local_filename))
            with suspend_cache(self):  # Never cache file downloads: they are already saved on disk
                r = self._request(method, url, save=False, params=params,
                                 headers=headers, data=data, files=files,
                                 timeout=timeout)
                with open(local_filepath, 'wb') as f:
                    f.write(r.content)
            return local_filepath
        else:
            query = AstroQuery(method, url, params=params, data=data,
                               headers=headers, files=files, timeout=timeout)
            if (self.cache_location is None) or (not self._cache_active):
                response = query.request(self.__session)
            else:
                response = query.from_cache(self.cache_location)
                if not response:
                    response = query.request(self.__session, self.cache_location)
                    response.to_cache(query.request_file(self.cache_location))
            return response


class suspend_cache:
    """
    A context manager that suspends caching.
    """
    def __init__(self, obj):
        self.obj = obj

    def __enter__(self):
        self.obj._cache_active = False

    def __exit__(self, exc_type, exc_value, traceback):
        self.obj._cache_active = True
        return False


class QueryWithLogin(BaseQuery):
    """
    This is the base class for all the query classes which are required to
    have a login to access the data.

    The abstract method _login() must be implemented. It is wrapped by the
    login() method, which turns off the cache. This way, login credentials
    are not stored in the cache.
    """

    @abc.abstractmethod
    def _login(self, *args, **kwargs):
        """
        login to non-public data as a known user

        Parameters
        ----------
        Keyword arguments that can be used to create
        the data payload(dict) sent via `requests.post`
        """
        pass

    def login(self, *args, **kwargs):
        with suspend_cache(self):
            result = self._login(*args, **kwargs)
        return result
