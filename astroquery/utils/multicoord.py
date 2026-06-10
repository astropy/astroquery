# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Support for looping single-position query methods over multiple coordinates.

Most archive query methods accept a single sky position per request. The
`support_multiple_coordinates` decorator lets such a method transparently
accept a vector `~astropy.coordinates.SkyCoord` or a list of coordinates
(or coordinate strings): the method is called once per position, a few
requests at a time in parallel, and the per-position results are combined.

The parallelism is deliberately conservative so that scripted use does not
overload archive servers; it can be tuned through
``astroquery.utils.multicoord.conf``.
"""
import functools
import inspect
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from astropy import config as _config
from astropy.coordinates import SkyCoord, BaseCoordinateFrame
from astropy.table import Table, vstack

from .commons import TableList

__all__ = ['support_multiple_coordinates', 'conf', 'Conf']


class Conf(_config.ConfigNamespace):
    """Configuration for queries looped over multiple coordinates."""

    max_parallel_queries = _config.ConfigItem(
        3,
        'Maximum number of requests sent in parallel when a query method is '
        'called with multiple coordinates. Keep this small: archive servers '
        'are a shared resource, and aggressive parallelism can degrade the '
        'service or get a client blocked. Do not raise this above what the '
        'archive documentation explicitly allows.',
        cfgtype='integer')

    min_request_interval = _config.ConfigItem(
        0.3,
        'Minimum delay (seconds) between submitting consecutive requests of '
        'a multi-coordinate query, across all parallel workers. This bounds '
        'the aggregate request rate at 1/min_request_interval regardless of '
        'how many workers run in parallel. Set to 0 to disable.',
        cfgtype='float')


conf = Conf()


class _Throttle:
    """Enforce a minimum interval between request submissions (thread-safe)."""

    def __init__(self, interval):
        self._interval = interval
        self._lock = threading.Lock()
        self._next_time = None

    def wait(self):
        if self._interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            if self._next_time is None or now >= self._next_time:
                delay = 0.
                self._next_time = now + self._interval
            else:
                delay = self._next_time - now
                self._next_time += self._interval
        if delay > 0:
            time.sleep(delay)


def _coordinate_list(value):
    """Return a list of single positions if ``value`` holds several, else None.

    Lists and tuples are interpreted as one entry per position; a
    non-scalar (vector) `~astropy.coordinates.SkyCoord` or coordinate frame
    is split into its scalar elements. Anything else (a string, a scalar
    coordinate, None) is treated as a single position.
    """
    if isinstance(value, (list, tuple)):
        if len(value) == 0:
            raise ValueError("An empty list of coordinates was provided.")
        return list(value)
    if (isinstance(value, (SkyCoord, BaseCoordinateFrame))
            and not value.isscalar):
        return list(value)
    return None


def _stack_tables(tables):
    if all('query_index' not in tbl.colnames for tbl in tables):
        for index, tbl in enumerate(tables):
            if len(tbl.colnames) > 0:
                tbl['query_index'] = index
    return vstack(tables, metadata_conflicts='silent')


def _combine_results(results):
    """Combine per-coordinate results into a single object where possible.

    Tables are stacked (gaining a ``query_index`` column identifying which
    input position each row came from, unless a column of that name already
    exists). `~astroquery.utils.TableList` results are merged key by key.
    Any other result type is returned as a plain list, in input order.
    """
    if all(isinstance(result, Table) for result in results):
        return _stack_tables(results)
    if all(isinstance(result, TableList) for result in results):
        keys = []
        for result in results:
            keys.extend(key for key in result.keys() if key not in keys)
        merged = {}
        for key in keys:
            for index, result in enumerate(results):
                if (key in result.keys()
                        and 'query_index' not in result[key].colnames
                        and len(result[key].colnames) > 0):
                    result[key]['query_index'] = index
            merged[key] = vstack([result[key] for result in results
                                  if key in result.keys()],
                                 metadata_conflicts='silent')
        return TableList(merged)
    return list(results)


def support_multiple_coordinates(coord_arg='coordinates', max_workers=None):
    """Allow a single-position query method to accept multiple coordinates.

    When the decorated method receives a vector
    `~astropy.coordinates.SkyCoord` or a list of coordinates (or coordinate
    strings) in its ``coord_arg`` argument, it is called once per position
    and the results are combined: tables are stacked into one table with an
    added ``query_index`` column mapping rows back to the input positions;
    other return types come back as a list in input order.

    A bounded worker pool (``conf.max_parallel_queries``, default 3) issues
    the requests, and consecutive request submissions are spaced by at least
    ``conf.min_request_interval`` seconds in aggregate, to stay well below
    archive rate limits. An exception in any single request propagates and
    aborts the combined result.

    Parameters
    ----------
    coord_arg : str
        Name of the coordinate parameter of the wrapped method.
    max_workers : int, optional
        Per-method cap on parallel requests, overriding
        ``conf.max_parallel_queries`` (use for services with stricter
        documented limits).
    """
    def decorator(func):
        signature = inspect.signature(func)
        if coord_arg not in signature.parameters:
            raise TypeError(f"'{func.__name__}' has no '{coord_arg}' parameter")

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound = signature.bind(*args, **kwargs)
            coords = _coordinate_list(bound.arguments.get(coord_arg))
            if coords is None:
                return func(*args, **kwargs)

            nworkers = max_workers if max_workers is not None else conf.max_parallel_queries
            nworkers = max(1, min(int(nworkers), len(coords)))
            throttle = _Throttle(conf.min_request_interval)

            def run_one(coord):
                rebound = signature.bind(*args, **kwargs)
                rebound.arguments[coord_arg] = coord
                throttle.wait()
                return func(*rebound.args, **rebound.kwargs)

            if nworkers == 1:
                results = [run_one(coord) for coord in coords]
            else:
                with ThreadPoolExecutor(max_workers=nworkers) as executor:
                    results = list(executor.map(run_one, coords))
            return _combine_results(results)

        return wrapper
    return decorator
