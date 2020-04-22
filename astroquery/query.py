# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import abc
import inspect
import pickle
import getpass
import hashlib
import keyring
import io
import os
import requests

import six
from astropy.config import paths
from astropy.logger import log
import astropy.units as u
from astropy.utils.console import ProgressBarOrSpinner
import astropy.utils.data

from . import version
from .utils import system_tools

__all__ = ['BaseQuery', 'QueryWithLogin']


def to_cache(response, cache_file):
    log.debug("Caching data to {0}".format(cache_file))
    with open(cache_file, "wb") as f:
        pickle.dump(response, f)


def _replace_none_iterable(iterable):
    return tuple('' if i is None else i for i in iterable)


class AstroQuery(object):

    def __init__(self, method, url,
                 params=None, data=None, headers=None,
                 files=None, timeout=None, json=None):
        self.method = method
        self.url = url
        self.params = params
        self.data = data
        self.json = json
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

    def request(self, session, cache_location=None, stream=False,
                auth=None, verify=True, allow_redirects=True,
                json=None):
        return session.request(self.method, self.url, params=self.params,
                               data=self.data, headers=self.headers,
                               files=self.files, timeout=self.timeout,
                               stream=stream, auth=auth, verify=verify,
                               allow_redirects=allow_redirects,
                               json=json)

    def hash(self):
        if self._hash is None:
            request_key = (self.method, self.url)
            for k in (self.params, self.data, self.json,
                      self.headers, self.files):
                if isinstance(k, dict):
                    entry = (tuple(sorted(k.items(),
                                          key=_replace_none_iterable)))
                    entry = tuple((k_, v_.read()) if hasattr(v_, 'read')
                                  else (k_, v_) for k_, v_ in entry)
                    for k_, v_ in entry:
                        if hasattr(v_, 'read') and hasattr(v_, 'seek'):
                            v_.seek(0)

                    request_key += entry
                elif isinstance(k, tuple) or isinstance(k, list):
                    request_key += (tuple(sorted(k,
                                                 key=_replace_none_iterable)),)
                elif k is None:
                    request_key += (None,)
                elif isinstance(k, six.string_types):
                    request_key += (k,)
                else:
                    raise TypeError("{0} must be a dict, tuple, str, or "
                                    "list".format(k))
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
        except IOError:  # TODO: change to FileNotFoundError once drop py2 support
            response = None
        if response:
            log.debug("Retrieving data from {0}".format(request_file))
        return response


class LoginABCMeta(abc.ABCMeta):
    """
    The goal of this metaclass is to copy the docstring and signature from
    ._login methods, implemented in subclasses, to a .login method that is
    visible by the users.

    It also inherits from the ABCMeta metaclass as _login is an abstract
    method.

    """

    def __new__(cls, name, bases, attrs):
        newcls = super(LoginABCMeta, cls).__new__(cls, name, bases, attrs)

        if '_login' in attrs and name not in ('BaseQuery', 'QueryWithLogin'):
            # skip theses two classes, BaseQuery and QueryWithLogin, so
            # below bases[0] should always be QueryWithLogin.
            def login(*args, **kwargs):
                bases[0].login(*args, **kwargs)

            login.__doc__ = attrs['_login'].__doc__
            if not six.PY2:
                login.__signature__ = inspect.signature(attrs['_login'])
            setattr(newcls, login.__name__, login)

        return newcls


@six.add_metaclass(LoginABCMeta)
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

    def _request(self, method, url,
                 params=None, data=None, headers=None,
                 files=None, save=False, savedir='', timeout=None, cache=True,
                 stream=False, auth=None, continuation=True, verify=True,
                 allow_redirects=True,
                 json=None):
        """
        A generic HTTP request method, similar to `requests.Session.request`
        but with added caching-related tools

        This is a low-level method not generally intended for use by astroquery
        end-users.  However, it should _always_ be used by astroquery
        developers; direct uses of `urllib` or `requests` are almost never
        correct.

        Parameters
        ----------
        method : str
            'GET' or 'POST'
        url : str
        params : None or dict
        data : None or dict
        json : None or dict
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
        timeout : int
        cache : bool
        verify : bool
            Verify the server's TLS certificate?
            (see http://docs.python-requests.org/en/master/_modules/requests/sessions/?highlight=verify)
        continuation : bool
            If the file is partly downloaded to the target location, this
            parameter will try to continue the download where it left off.
            See `_download_file`.
        stream : bool

        Returns
        -------
        response : `requests.Response`
            The response from the server if ``save`` is False
        local_filepath : list
            a list of strings containing the downloaded local paths if ``save``
            is True
        """
        req_kwargs = dict(
            params=params,
            data=data,
            headers=headers,
            files=files,
            timeout=timeout,
            json=json
        )
        if save:
            local_filename = url.split('/')[-1]
            if os.name == 'nt':
                # Windows doesn't allow special characters in filenames like
                # ":" so replace them with an underscore
                local_filename = local_filename.replace(':', '_')
            local_filepath = os.path.join(savedir or self.cache_location or '.', local_filename)

            self._download_file(url, local_filepath, cache=cache,
                                continuation=continuation, method=method,
                                allow_redirects=allow_redirects,
                                auth=auth, **req_kwargs)
            return local_filepath
        else:
            query = AstroQuery(method, url, **req_kwargs)
            if ((self.cache_location is None) or (not self._cache_active) or (not cache)):
                with suspend_cache(self):
                    response = query.request(self._session, stream=stream,
                                             auth=auth, verify=verify,
                                             allow_redirects=allow_redirects,
                                             json=json)
            else:
                response = query.from_cache(self.cache_location)
                if not response:
                    response = query.request(self._session,
                                             self.cache_location,
                                             stream=stream,
                                             auth=auth,
                                             allow_redirects=allow_redirects,
                                             verify=verify,
                                             json=json)
                    to_cache(response, query.request_file(self.cache_location))
            self._last_query = query
            return response

    def _download_file(self, url, local_filepath, timeout=None, auth=None,
                       continuation=True, cache=False, method="GET",
                       head_safe=False, **kwargs):
        """
        Download a file.  Resembles `astropy.utils.data.download_file` but uses
        the local ``_session``

        Parameters
        ----------
        url : string
        local_filepath : string
        timeout : int
        auth : dict or None
        continuation : bool
            If the file has already been partially downloaded *and* the server
            supports HTTP "range" requests, the download will be continued
            where it left off.
        cache : bool
        method : "GET" or "POST"
        head_safe : bool
        """

        if head_safe:
            response = self._session.request("HEAD", url,
                                             timeout=timeout, stream=True,
                                             auth=auth, **kwargs)
        else:
            response = self._session.request(method, url,
                                             timeout=timeout, stream=True,
                                             auth=auth, **kwargs)

        response.raise_for_status()
        if 'content-length' in response.headers:
            length = int(response.headers['content-length'])
            if length == 0:
                log.warn('URL {0} has length=0'.format(url))
        else:
            length = None

        if ((os.path.exists(local_filepath)
             and ('Accept-Ranges' in response.headers)
             and continuation)):
            open_mode = 'ab'

            existing_file_length = os.stat(local_filepath).st_size
            if length is not None and existing_file_length >= length:
                # all done!
                log.info("Found cached file {0} with expected size {1}."
                         .format(local_filepath, existing_file_length))
                return
            elif existing_file_length == 0:
                open_mode = 'wb'
            else:
                log.info("Continuing download of file {0}, with {1} bytes to "
                         "go ({2}%)".format(local_filepath,
                                            length - existing_file_length,
                                            (length-existing_file_length)/length*100))

                # bytes are indexed from 0:
                # https://en.wikipedia.org/wiki/List_of_HTTP_header_fields#range-request-header
                end = "{0}".format(length-1) if length is not None else ""
                self._session.headers['Range'] = "bytes={0}-{1}".format(existing_file_length,
                                                                        end)

                response = self._session.request(method, url,
                                                 timeout=timeout, stream=True,
                                                 auth=auth, **kwargs)
                response.raise_for_status()

        elif cache and os.path.exists(local_filepath):
            if length is not None:
                statinfo = os.stat(local_filepath)
                if statinfo.st_size != length:
                    log.warning("Found cached file {0} with size {1} that is "
                                "different from expected size {2}"
                                .format(local_filepath,
                                        statinfo.st_size,
                                        length))
                    open_mode = 'wb'
                else:
                    log.info("Found cached file {0} with expected size {1}."
                             .format(local_filepath, statinfo.st_size))
                    response.close()
                    return
            else:
                log.info("Found cached file {0}.".format(local_filepath))
                response.close()
                return
        else:
            open_mode = 'wb'
            if head_safe:
                response = self._session.request(method, url,
                                                 timeout=timeout, stream=True,
                                                 auth=auth, **kwargs)
                response.raise_for_status()

        blocksize = astropy.utils.data.conf.download_block_size

        bytes_read = 0

        # Only show progress bar if logging level is INFO or lower.
        if log.getEffectiveLevel() <= 20:
            progress_stream = None  # Astropy default
        else:
            progress_stream = io.StringIO()

        with ProgressBarOrSpinner(
                length, ('Downloading URL {0} to {1} ...'
                         .format(url, local_filepath)),
                file=progress_stream) as pb:
            with open(local_filepath, open_mode) as f:
                for block in response.iter_content(blocksize):
                    f.write(block)
                    bytes_read += blocksize
                    if length is not None:
                        pb.update(bytes_read if bytes_read <= length else
                                  length)
                    else:
                        pb.update(bytes_read)

        response.close()
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

    def __init__(self):
        super(QueryWithLogin, self).__init__()
        self._authenticated = False

    def _get_password(self, service_name, username, reenter=False):
        """Get password from keyring or prompt."""

        password_from_keyring = None
        if reenter is False:
            try:
                password_from_keyring = keyring.get_password(
                    service_name, username)
            except keyring.errors.KeyringError as exc:
                log.warning("Failed to get a valid keyring for password "
                            "storage: {}".format(exc))

        if password_from_keyring is None:
            log.warning("No password was found in the keychain for the "
                        "provided username.")
            if system_tools.in_ipynb():
                log.warning("You may be using an ipython notebook:"
                            " the password form will appear in your terminal.")
            password = getpass.getpass("{0}, enter your password:\n"
                                       .format(username))
        else:
            password = password_from_keyring

        return password, password_from_keyring

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
