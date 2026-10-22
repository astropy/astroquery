# Licensed under a 3-clause BSD style license - see LICENSE.rst
import abc
import inspect
import pickle
import copy
import getpass
import hashlib
import keyring
import io
import os
import platform
import requests
import shutil
import textwrap
import time
import uuid

from datetime import datetime, timezone, timedelta
from pathlib import Path

from astropy.config import paths
import astropy.units as u
from astropy.utils.console import ProgressBarOrSpinner
import astropy.utils.data
from astropy.utils import deprecated

import pyvo

from astroquery import version, log, cache_conf
from astroquery.utils import system_tools


__all__ = ['BaseVOQuery', 'BaseQuery', 'QueryWithLogin']


def to_cache(original_response, cache_file):
    log.debug("Caching data to {0}".format(cache_file))

    # Copying a TAPService instance with an auth session produces some warnings
    # as a side affect. The hooks are not needed in the cache, so we remove
    # them before caching and restore them afterwards.
    # Related pyvo issue: https://github.com/astropy/pyvo/issues/755
    hooks = None
    if hasattr(original_response, 'request'):
        hooks = original_response.request.hooks
        del original_response.request.hooks
    if hasattr(original_response, 'history'):
        for r in original_response.history:
            if hasattr(r, 'request'):
                del r.request.hooks
    response_copy = copy.deepcopy(original_response)
    if hooks:
        original_response.request.hooks = hooks
    # Write to a temporary file next to the cache entry and rename it into
    # place, so that a reader never sees a partly written entry (for example
    # when the process is interrupted, or when processes share a cache).
    tmp_file = _temporary_path(cache_file, ".tmp")
    try:
        with open(tmp_file, "wb") as f:
            pickle.dump(response_copy, f, protocol=4)
        try:
            _replace_file(tmp_file, cache_file)
        except PermissionError as exc:
            # For example on Windows, while another process reads the entry.
            # Caching is best effort, so keep the existing entry rather than
            # failing the query.
            log.warning(f"Could not update cache file {cache_file}: {exc}")
            os.remove(tmp_file)
    except BaseException:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        raise


def _temporary_path(path, suffix):
    """A unique file name next to ``path``, used to write ``path`` atomically."""
    return f"{os.fspath(path)}.{uuid.uuid4().hex[:8]}{suffix}"


def _header(headers, name):
    """Look up a response header by name, ignoring case."""
    name = name.lower()
    return next((value for key, value in headers.items() if key.lower() == name), None)


def _replace_file(src, dst):
    """`os.replace`, retried briefly on Windows, where it fails while ``dst`` is open."""
    for attempt in range(5):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if os.name != 'nt' or attempt == 4:
                raise
            time.sleep(0.1 * 2 ** attempt)


def _replace_none_iterable(iterable):
    return tuple('' if i is None else i for i in iterable)


class AstroQuery:

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
                elif isinstance(k, str):
                    request_key += (k,)
                else:
                    raise TypeError("{0} must be a dict, tuple, str, or "
                                    "list".format(k))
            self._hash = hashlib.sha224(pickle.dumps(request_key)).hexdigest()
        return self._hash

    def request_file(self, cache_location):
        fn = cache_location.joinpath(self.hash() + ".pickle")
        return fn

    def from_cache(self, cache_location, cache_timeout):
        request_file = self.request_file(cache_location)
        try:
            if cache_timeout == -1:
                expired = False
            else:
                current_time = datetime.now(timezone.utc)
                cache_time = datetime.fromtimestamp(request_file.stat().st_mtime, timezone.utc)
                expired = current_time-cache_time > timedelta(seconds=cache_timeout)
            if not expired:
                with open(request_file, "rb") as f:
                    response = pickle.load(f)
                if not isinstance(response, requests.Response):
                    response = None
            else:
                log.debug(f"Cache expired for {request_file}...")
                response = None
        except FileNotFoundError:
            response = None
        except (EOFError, pickle.UnpicklingError) as exc:
            log.warning(f"Ignoring unreadable cache file {request_file}: {exc}")
            response = None
        if response:
            log.debug("Retrieved data from {0}".format(request_file))
        return response

    def remove_cache_file(self, cache_location):
        """
        Remove the cache file - may be needed if a query fails during parsing
        (successful request, but failed return)
        """
        request_file = self.request_file(cache_location)

        if request_file.exists:
            request_file.unlink()
        else:
            raise FileNotFoundError(f"Tried to remove cache file {request_file} but "
                                    "it does not exist")


class LoginABCMeta(abc.ABCMeta):
    """
    The goal of this metaclass is to copy the docstring and signature from
    ._login methods, implemented in subclasses, to a .login method that is
    visible by the users.

    It also inherits from the ABCMeta metaclass as _login is an abstract
    method.

    """

    def __new__(cls, name, bases, attrs):
        newcls = super().__new__(cls, name, bases, attrs)

        if '_login' in attrs and name not in ('BaseQuery', 'QueryWithLogin'):
            # skip theses two classes, BaseQuery and QueryWithLogin, so
            # below bases[0] should always be QueryWithLogin.
            def login(*args, **kwargs):
                bases[0].login(*args, **kwargs)

            login.__doc__ = attrs['_login'].__doc__
            login.__signature__ = inspect.signature(attrs['_login'])
            setattr(newcls, login.__name__, login)

        return newcls


class BaseVOQuery:
    """
    Bare minimum base query that sets the Session header to include both astroquery and pyvo.
    Use in modules that rely on PyVO, either on its own or in combination with ``BaseQuery`` (be mindful
    about resolution order of base classes!).
    """
    def __init__(self, *, extra_user_agents=None):
        """Create an instance of BaseVOQuery.

        Parameters
        ----------
        extra_user_agents : str | list(str)
            Extra user agents to be added to the ones already provided by astroquery.
        """
        super().__init__()
        if not hasattr(self, '_session'):
            # We don't want to override another, e.g. already authenticated session from another baseclass
            self._session = requests.Session()

        user_agents = self._session.headers['User-Agent'].split()
        if 'astroquery' in user_agents[0]:
            if 'pyVO' not in user_agents[1]:
                user_agents[0] = f"astroquery/{version.version} pyVO/{pyvo.__version__}"
        elif 'pyVO' in user_agents[0]:
            user_agents[0] = f"astroquery/{version.version} pyVO/{pyvo.__version__}"
        else:
            user_agents = [f"astroquery/{version.version} pyVO/{pyvo.__version__} "
                           f"Python/{platform.python_version()} ({platform.system()})"] + user_agents

        if extra_user_agents:
            if isinstance(extra_user_agents, str):
                user_agents += [extra_user_agents]
            else:
                user_agents += extra_user_agents

        self._session.headers['User-Agent'] = " ".join(user_agents)

        self.name = self.__class__.__name__.split("Class")[0]

    def __call__(self, *args, **kwargs):
        """ init a fresh copy of self """
        return self.__class__(*args, **kwargs)


class BaseQuery(metaclass=LoginABCMeta):
    """
    This is the base class for all the query classes in astroquery. It
    is implemented as an abstract class and must not be directly instantiated.
    """

    def __init__(self):
        self._session = requests.Session()
        self._session.hooks['response'].append(self._response_hook)
        self._session.headers['User-Agent'] = (
            f"astroquery/{version.version} Python/{platform.python_version()} ({platform.system()}) "
            f"{self._session.headers['User-Agent']}")

        self.name = self.__class__.__name__.split("Class")[0]
        self._cache_location = None

    def __call__(self, *args, **kwargs):
        """ init a fresh copy of self """
        return self.__class__(*args, **kwargs)

    def _response_hook(self, response, *args, **kwargs):
        loglevel = log.getEffectiveLevel()

        if loglevel >= 10:
            # Log request at DEBUG severity
            request_hdrs = '\n'.join(f'{k}: {v}' for k, v in response.request.headers.items())
            request_log = textwrap.indent(
                f"-----------------------------------------\n"
                f"{response.request.method} {response.request.url}\n"
                f"{request_hdrs}\n"
                f"\n"
                f"{response.request.body}\n"
                f"-----------------------------------------", '\t')
            log.debug(f"HTTP request\n{request_log}")
        if loglevel >= 5:
            # Log response at super-DEBUG severity
            response_hdrs = '\n'.join(f'{k}: {v}' for k, v in response.headers.items())
            if kwargs.get('stream'):
                response_log = textwrap.indent(
                    f"-----------------------------------------\n"
                    f"{response.status_code} {response.reason} {response.url}\n"
                    f"{response_hdrs}\n"
                    "Streaming Data\n"
                    f"-----------------------------------------", '\t')
            else:
                response_log = textwrap.indent(
                    f"-----------------------------------------\n"
                    f"{response.status_code} {response.reason} {response.url}\n"
                    f"{response_hdrs}\n"
                    f"\n"
                    f"{response.text}\n"
                    f"-----------------------------------------", '\t')
            log.log(5, f"HTTP response\n{response_log}")

    @property
    def cache_location(self):
        cl = self._cache_location or Path(paths.get_cache_dir(), 'astroquery', self.name)
        cl.mkdir(parents=True, exist_ok=True)
        return cl

    @cache_location.setter
    def cache_location(self, loc):
        self._cache_location = Path(loc)

    def reset_cache_location(self):
        """Resets the cache location to the default astropy cache"""
        self._cache_location = None

    def clear_cache(self):
        """Removes all cache files."""
        for fle in self.cache_location.glob("*.pickle"):
            fle.unlink()
        # Temporary files left by an interrupted write of a cache entry
        for fle in self.cache_location.glob("*.pickle.*.tmp"):
            fle.unlink()

    def _request(self, method, url,
                 params=None, data=None, headers=None,
                 files=None, save=False, savedir='', timeout=None, cache=None,
                 stream=False, auth=None, continuation=True, verify=True,
                 allow_redirects=True,
                 json=None, return_response_on_save=False):
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
            Optional, if specified, overrides global cache settings.
        verify : bool
            Verify the server's TLS certificate?
            (see https://docs.python-requests.org/en/master/_modules/requests/sessions/?highlight=verify)
        continuation : bool
            If the file is partly downloaded to the target location, this
            parameter will try to continue the download where it left off.
            See `_download_file`.
        stream : bool
        return_response_on_save : bool
            If ``save``, also return the server response. The default is to only
            return the local file path.

        Returns
        -------
        response : `requests.Response`
            The response from the server if ``save`` is False
        local_filepath : list
            a list of strings containing the downloaded local paths if ``save``
            is True and ``return_response_on_save`` is False.
        (local_filepath, response) : tuple(list, `requests.Response`)
            a tuple containing a list of strings containing the downloaded local paths,
            and the server response object, if ``save`` is True and ``return_response_on_save``
            is True.
        """

        if cache is None:  # Global caching not overridden
            cache = cache_conf.cache_active

        if save:
            local_filename = url.split('/')[-1]
            if os.name == 'nt':
                # Windows doesn't allow special characters in filenames like
                # ":" so replace them with an underscore
                local_filename = local_filename.replace(':', '_')

            local_filepath = os.path.join(savedir or self.cache_location or '.', local_filename)

            response = self._download_file(url, local_filepath, cache=cache, timeout=timeout,
                                           continuation=continuation, method=method,
                                           allow_redirects=allow_redirects,
                                           auth=auth, params=params, data=data, headers=headers,
                                           files=files, json=json)
            if return_response_on_save:
                return local_filepath, response
            else:
                return local_filepath
        else:
            query = AstroQuery(method, url, params=params, data=data, headers=headers,
                               files=files, timeout=timeout, json=json)
            if not cache:
                with cache_conf.set_temp("cache_active", False):
                    response = query.request(self._session, stream=stream,
                                             auth=auth, verify=verify,
                                             allow_redirects=allow_redirects,
                                             json=json)
            else:
                response = query.from_cache(self.cache_location, cache_conf.cache_timeout)
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
                       head_safe=False, verbose=True, **kwargs):
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
            where it left off.  Partial downloads are kept as
            ``local_filepath + '.part'``.
        cache : bool
            Cache downloaded file. Defaults to False.
        method : "GET" or "POST"
        head_safe : bool
        verbose : bool
            Whether to show download progress. Defaults to True.

        Notes
        -----
        The data are written to a temporary file next to ``local_filepath``,
        checked against the ``Content-Length`` of the response that delivered
        them, and renamed to ``local_filepath`` only when complete.  ``local_filepath``
        therefore never holds a partial download, also when several processes
        download the same file at the same time.  If the transfer is
        interrupted by an exception, the data received so far are kept as
        ``local_filepath + '.part'`` for a later call with
        ``continuation=True``.  A process that is killed outright leaves its
        temporary file (``local_filepath + '.<8 hex digits>.part'``) behind.
        """
        dest = os.fspath(local_filepath)
        if os.path.islink(dest):
            # Update the file the link points to, as writing through it would
            dest = os.path.realpath(dest)
        part_filepath = dest + '.part'

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
                log.warning('URL {0} has length=0'.format(url))
        else:
            length = None

        resumable = ('Accept-Ranges' in response.headers) and length is not None

        existing_file_length = os.stat(dest).st_size if os.path.exists(dest) else None
        if existing_file_length:
            if continuation and resumable and existing_file_length >= length:
                log.info(f"Found cached file {dest} with size {existing_file_length} = {length}.")
                response.close()
                return local_filepath
            if cache and length is not None and existing_file_length == length:
                log.info(f"Found cached file {dest} with expected size {existing_file_length}.")
                response.close()
                return local_filepath

        # Data to resume from: the partial download kept by an interrupted
        # call, or an incomplete file written in place by an older astroquery.
        # They are copied rather than moved, so that both stay usable by other
        # processes meanwhile.
        resume_from = None
        if continuation and resumable:
            if os.path.exists(part_filepath) and os.stat(part_filepath).st_size > 0:
                resume_from = part_filepath
            elif existing_file_length:
                resume_from = dest

        if resume_from is None and existing_file_length and cache:
            if length is not None:
                log.warning(f"Found cached file {dest} with size {existing_file_length} "
                            f"that is different from expected size {length}.  ")
                if continuation:
                    log.warning("Continuation was requested but is not possible because "
                                "'Accepts-Ranges' is not in the response headers.")
            else:
                # The server doesn't return a Content-Length header, but the
                # file is already cached.  One such case is dynamically
                # generated files in the MAST Archive.
                log.warning(f"Could not verify length of cached file {dest}. "
                            "Re-downloading the file.")

        tmp_filepath = _temporary_path(dest, '.part')
        try:
            offset = 0
            if resume_from is not None:
                shutil.copyfile(resume_from, tmp_filepath)
                offset = os.stat(tmp_filepath).st_size
                if offset > length:
                    log.warning(f"Found partial download of {dest} with size {offset}, "
                                f"larger than the expected {length}.  Overwriting.")
                    offset = 0

            if resume_from is not None and offset == length:
                log.info(f"Found complete partial download of {dest} with size {length}.")
                transfer = False
            elif offset > 0:
                transfer = True
                log.info("Continuing download of file {0}, with {1} bytes to "
                         "go ({2}%)".format(dest, length - offset,
                                            (length - offset) / length * 100))
                # bytes are indexed from 0:
                # https://en.wikipedia.org/wiki/List_of_HTTP_header_fields#range-request-header
                self._session.headers['Range'] = "bytes={0}-{1}".format(offset, length - 1)
                log.debug(f"Continuing with range={self._session.headers['Range']}")
                try:
                    response = self._session.request(method, url,
                                                     timeout=timeout, stream=True,
                                                     auth=auth, **kwargs)
                    response.raise_for_status()
                finally:
                    self._session.headers.pop('Range', None)
                content_range = _header(response.headers, 'Content-Range') or ''
                if response.status_code != 206 or not content_range.startswith(f'bytes {offset}-'):
                    log.warning(f"The server did not continue the download of {dest} "
                                f"(status {response.status_code}).  Downloading the whole file.")
                    if response.status_code == 206:
                        # A different range than requested: fetch the whole file
                        response = self._session.request(method, url,
                                                         timeout=timeout, stream=True,
                                                         auth=auth, **kwargs)
                        response.raise_for_status()
                    offset = 0
            else:
                transfer = True
                if head_safe:
                    response = self._session.request(method, url,
                                                     timeout=timeout, stream=True,
                                                     auth=auth, **kwargs)
                    response.raise_for_status()

            if transfer:
                open_mode = 'ab' if offset else 'wb'
                blocksize = astropy.utils.data.conf.download_block_size

                log.debug(f"Downloading URL {url} to {dest} with size {length} "
                          f"by blocks of {blocksize} with open_mode={open_mode}")

                bytes_read = offset

                # Only show progress bar if logging level is INFO or lower.
                if log.getEffectiveLevel() <= 20:
                    progress_stream = None  # Astropy default
                else:
                    progress_stream = io.StringIO()

                with open(tmp_filepath, open_mode) as f:
                    if verbose:
                        with ProgressBarOrSpinner(length, f'Downloading URL {url} to {dest} ...',
                                                  file=progress_stream) as pb:
                            for block in response.iter_content(blocksize):
                                f.write(block)
                                bytes_read += len(block)
                                if length is not None:
                                    pb.update(bytes_read if bytes_read <= length else length)
                                else:
                                    pb.update(bytes_read)
                    else:
                        f.write(response.content)
                    f.flush()
                    os.fsync(f.fileno())

                # Check the size against the Content-Length of the response
                # that delivered the data (a HEAD response may differ).  This is
                # only possible when the body was not compressed in transit, as
                # requests decompresses it.
                body_length = _header(response.headers, 'Content-Length')
                encoding = (_header(response.headers, 'Content-Encoding') or 'identity').lower()
                if body_length is not None and encoding in ('', 'identity'):
                    expected = offset + int(body_length)
                    received = os.stat(tmp_filepath).st_size
                    if received != expected:
                        raise OSError(f"Download of {url} to {dest} is incomplete: "
                                      f"received {received} bytes, expected {expected}.")
                    if length is not None and expected != length:
                        log.warning(f"The size of {url} was first reported as {length} bytes, "
                                    f"then as {expected} bytes.")

            try:
                _replace_file(tmp_filepath, dest)
            except PermissionError:
                # For example on Windows, while another process reads dest.  If
                # dest already holds the same complete file, the job is done.
                if (os.path.exists(dest) and length is not None
                        and os.stat(dest).st_size == os.stat(tmp_filepath).st_size == length):
                    log.info(f"{dest} is in use but already complete.")
                    os.remove(tmp_filepath)
                else:
                    raise
        except BaseException:
            # Keep data that can be resumed, unless an existing partial
            # download holds more; remove everything else.
            if os.path.exists(tmp_filepath):
                kept = os.stat(tmp_filepath).st_size
                previous = os.stat(part_filepath).st_size if os.path.exists(part_filepath) else 0
                if resumable and previous < kept <= length:
                    try:
                        _replace_file(tmp_filepath, part_filepath)
                    except OSError:
                        os.remove(tmp_filepath)
                else:
                    os.remove(tmp_filepath)
            raise
        finally:
            response.close()

        # The partial download, if any, is no longer needed.
        try:
            os.remove(part_filepath)
        except OSError:
            pass

        return local_filepath


@deprecated(since="v0.4.7", message=("The suspend_cache function is deprecated,"
                                     "Use the conf set_temp function instead."))
class suspend_cache:
    """
    A context manager that suspends caching.
    """

    def __init__(self, obj=None):
        self.original_cache_setting = cache_conf.cache_active

    def __enter__(self):
        cache_conf.cache_active = False

    def __exit__(self, exc_type, exc_value, traceback):
        cache_conf.cache_active = self.original_cache_setting
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
        super().__init__()
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
        with cache_conf.set_temp("cache_active", False):
            self._authenticated = self._login(*args, **kwargs)
        return self._authenticated

    def authenticated(self):
        return self._authenticated
