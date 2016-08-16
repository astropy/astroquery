# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import abc
import pickle
import hashlib
import os
import requests

from astropy.extern import six
from astropy.config import paths
from astropy import log
import astropy.units as u
from astropy.utils.console import ProgressBarOrSpinner
import astropy.utils.data

from . import version

__all__ = ['BaseQuery', 'QueryWithLogin']


def to_cache(response, cache_file):
    log.debug("Caching data to {0}".format(cache_file))
    with open(cache_file, "wb") as f:
        pickle.dump(response, f)


def _replace_none_iterable(iterable):
    return tuple('' if i is None else i for i in iterable)


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

    def request(self, session, cache_location=None, stream=False, auth=None):
        return session.request(self.method, self.url, params=self.params,
                               data=self.data, headers=self.headers,
                               files=self.files, timeout=self.timeout,
                               stream=stream, auth=auth)

    def hash(self):
        if self._hash is None:
            request_key = (self.method, self.url)
            for k in (self.params, self.data, self.headers, self.files):
                if isinstance(k, dict):
                    request_key += (tuple(sorted(k.items(),
                                                 key=_replace_none_iterable)),)
                elif isinstance(k, tuple) or isinstance(k, list):
                    request_key += (tuple(sorted(k,
                                                 key=_replace_none_iterable)),)
                elif k is None:
                    request_key += (None,)
                elif isinstance(k, six.string_types):
                    request_key += (k,)
                else:
                    raise TypeError("{0} must be a dict, tuple, str, or list")
            self._hash = hashlib.sha224(pickle.dumps(request_key)).hexdigest()
        return self._hash

    def request_file(self, cache_location):
        fn = os.path.join(cache_location, self.hash() + ".pickle")
        return fn

    def from_cache(self, cache_location):
        request_file = self.request_file(cache_location)
        try:
            with open(request_file, "rb") as f:
                response = pickle.load(f)
            if not isinstance(response, requests.Response):
                response = None
        except:
            response = None
        if response:
            log.debug("Retrieving data from {0}".format(request_file))
        return response


@six.add_metaclass(abc.ABCMeta)
class BaseQuery(object):
    """
    This is the base class for all the query classes in astroquery. It
    is implemented as an abstract class and must not be directly instantiated.
    """

    def __init__(self):
        S = self._session = requests.session()
        S.headers['User-Agent'] = (
            'astroquery/{vers} {olduseragent}'
            .format(vers=version.version,
                    olduseragent=S.headers['User-Agent']))

        self.cache_location = os.path.join(
            paths.get_cache_dir(), 'astroquery',
            self.__class__.__name__.split("Class")[0])
        if not os.path.exists(self.cache_location):
            os.makedirs(self.cache_location)
        self._cache_active = True

    def __call__(self, *args, **kwargs):
        """ init a fresh copy of self """
        return self.__class__(*args, **kwargs)

    def _request(self, method, url, params=None, data=None, headers=None,
                 files=None, save=False, savedir='', timeout=None, cache=True,
                 stream=False, auth=None):
        """
        A generic HTTP request method, similar to `requests.Session.request`
        but with added caching-related tools

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
        auth : None or dict
        files : None or dict
            See `requests.request`
        save : bool
            Whether to save the file to a local directory.  Caching will happen
            independent of this parameter if `BaseQuery.cache_location` is set,
            but the save location can be overridden if ``save==True``
        savedir : str
            The location to save the local file if you want to save it
            somewhere other than `BaseQuery.cache_location`

        Returns
        -------
        response : `requests.Response`
            The response from the server if ``save`` is False
        local_filepath : list
            a list of strings containing the downloaded local paths if ``save``
            is True
        """
        if save:
            local_filename = url.split('/')[-1]
            if os.name == 'nt':
                # Windows doesn't allow special characters in filenames like
                # ":" so replace them with an underscore
                local_filename = local_filename.replace(':', '_')
            local_filepath = os.path.join(self.cache_location or savedir or
                                          '.', local_filename)
            # REDUNDANT: spinner has this log.info("Downloading
            # {0}...".format(local_filename))
            self._download_file(url, local_filepath, timeout=timeout,
                                auth=auth, cache=cache)
            return local_filepath
        else:
            query = AstroQuery(method, url, params=params, data=data,
                               headers=headers, files=files, timeout=timeout)
            if ((self.cache_location is None) or (not self._cache_active) or
                    (not cache)):
                with suspend_cache(self):
                    response = query.request(self._session, stream=stream,
                                             auth=auth)
            else:
                response = query.from_cache(self.cache_location)
                if not response:
                    response = query.request(self._session,
                                             self.cache_location,
                                             stream=stream,
                                             auth=auth)
                    to_cache(response, query.request_file(self.cache_location))
            return response

    def _download_file(self, url, local_filepath, timeout=None, auth=None,
                       cache=False):
        """
        Download a file.  Resembles `astropy.utils.data.download_file` but uses
        the local ``_session``
        """
        response = self._session.get(url, timeout=timeout, stream=True,
                                     auth=auth)
        response.raise_for_status()
        if 'content-length' in response.headers:
            length = int(response.headers['content-length'])
        else:
            length = None

        if cache and os.path.exists(local_filepath):
            if length is not None:
                statinfo = os.stat(local_filepath)
                if statinfo.st_size != length:
                    log.warning("Found cached file {0} with size {1} that is "
                                "different from expected size {2}"
                                .format(local_filepath,
                                        statinfo.st_size,
                                        length))
                else:
                    log.info("Found cached file {0} with expected size {1}."
                             .format(local_filepath, statinfo.st_size))
                    response.close()
                    return
            else:
                log.info("Found cached file {0}.".format(local_filepath))
                response.close()
                return

        blocksize = astropy.utils.data.conf.download_block_size

        bytes_read = 0

        with ProgressBarOrSpinner(
            length, ('Downloading URL {0} to {1} ...'
                     .format(url, local_filepath))) as pb:
            with open(local_filepath, 'wb') as f:
                for block in response.iter_content(blocksize):
                    f.write(block)
                    bytes_read += blocksize
                    if length is not None:
                        pb.update(bytes_read if bytes_read <= length else
                                  length)
                    else:
                        pb.update(bytes_read)

        response.close()


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

    def __init__(self):
        super(QueryWithLogin, self).__init__()
        self._authenticated = False

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
            self._authenticated = self._login(*args, **kwargs)
        return self._authenticated

    def authenticated(self):
        return self._authenticated
