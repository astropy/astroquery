# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Support VO Simple Cone Search capabilities."""

# STDLIB
import warnings

# THIRD-PARTY
import numpy as np

# ASTROPY
from astropy.io.votable.exceptions import vo_warn, W25
from astropy.utils.console import color_print
from astropy.utils.exceptions import AstropyUserWarning

# LOCAL
from . import vos_catalog
from .vo_async import AsyncBase
from .core import ConeSearch, _validate_sr
from .exceptions import ConeSearchError
from ..exceptions import NoResultsWarning
from ..utils.timer import timefunc, RunTimePredictor

# Import configurable items declared in __init__.py
from . import conf

__all__ = ['AsyncConeSearch', 'conesearch', 'AsyncSearchAll', 'search_all',
           'list_catalogs', 'predict_search', 'conesearch_timer']

# Skip these doctests
__doctest_skip__ = ['AsyncConeSearch', 'AsyncSearchAll']


class AsyncConeSearch(AsyncBase):
    """
    Perform a Cone Search asynchronously and returns the result of the
    first successful query.

    .. note::

        See :class:`~astroquery.vo_conesearch.vo_async.AsyncBase`
        for more details.

    Parameters
    ----------
    args, kwargs
        See :func:`conesearch`.

    Examples
    --------
    >>> from astropy import coordinates as coord
    >>> from astropy import units as u
    >>> from astroquery.vo_conesearch import conesearch
    >>> c = coord.ICRS(6.0223 * u.degree, -72.0814 * u.degree)
    >>> async_search = conesearch.AsyncConeSearch(
    ...     c, 0.5 * u.degree,
    ...     catalog_db='Guide Star Catalog 2.3 Cone Search 1')

    Check search status:

    >>> async_search.running()
    True
    >>> async_search.done()
    False

    Get search results after a 30-second wait (not to be
    confused with ``astroquery.vo_conesearch.conf.timeout`` that
    governs individual Cone Search queries). If search is still not
    done after 30 seconds, `TimeoutError` is raised. Otherwise,
    Cone Search result is returned and can be manipulated as in
    :ref:`Simple Cone Search Examples <vo-sec-scs-examples>`.
    If no ``timeout`` keyword given, it waits until completion:

    >>> async_result = async_search.get(timeout=30)
    >>> len(async_result)
    74271

    """
    def __init__(self, *args, **kwargs):
        super().__init__(conesearch, *args, **kwargs)


def conesearch(center, radius, *, verb=1, catalog_db=None,
               verbose=True, cache=True, query_all=False,
               return_astropy_table=True, use_names_over_ids=False):
    """
    Perform Cone Search and returns the result of the
    first successful query.

    .. note::

        Use ``astroquery.vo_conesearch.conf.pedantic`` to control
        pedantry. When `True`, will raise an error when the result
        violates the spec, otherwise issue a warning. Warnings may
        be controlled using :py:mod:`warnings` module.

    .. note::

        Use ``astroquery.vo_conesearch.conf.timeout`` to control
        timeout limit in seconds for each service being queried.

    Parameters
    ----------
    center : str, `astropy.coordinates` object, list, or tuple
        Position of the center of the cone to search.
        It may be specified as an object from the
        :ref:`astropy:astropy-coordinates` package,
        string as accepted by
        :func:`~astroquery.utils.parse_coordinates`, or tuple/list.
        If given as tuple or list, it is assumed to be ``(RA, DEC)``
        in the ICRS coordinate frame, given in decimal degrees.

    radius : float or `~astropy.units.quantity.Quantity`
        Radius of the cone to search:

            - If float is given, it is assumed to be in decimal degrees.
            - If astropy quantity is given, it is internally converted
              to degrees.

    verb : {1, 2, 3}
        Verbosity indicating how many columns are to be returned
        in the resulting table. Support for this parameter by
        a Cone Search service implementation is optional. If the
        service supports the parameter:

            1. Return the bare minimum number of columns that
               the provider considers useful in describing the
               returned objects.
            2. Return a medium number of columns between the
               minimum and maximum (inclusive) that are
               considered by the provider to most typically
               useful to the user.
            3. Return all of the columns that are available for
               describing the objects.

        If not supported, the service should ignore the parameter
        and always return the same columns for every request.

    catalog_db
        May be one of the following, in order from easiest to
        use to most control:

            - `None`: A database of
              ``astroquery.vo_conesearch.conf.conesearch_dbname`` catalogs is
              downloaded from ``astroquery.vo_conesearch.conf.vos_baseurl``.
              The first catalog in the database to successfully return a
              result is used.

            - *catalog name*: A name in the database of
              ``astroquery.vo_conesearch.conf.conesearch_dbname`` catalogs at
              ``astroquery.vo_conesearch.conf.vos_baseurl`` is used.
              For a list of acceptable names, use
              :func:`astroquery.vo_conesearch.vos_catalog.list_catalogs`.

            - *url*: The prefix of a URL to a IVOA Service for
              ``astroquery.vo_conesearch.conf.conesearch_dbname``.
              Must end in either '?' or '&'.

            - `~astroquery.vo_conesearch.vos_catalog.VOSCatalog` object: A
              specific catalog manually downloaded and selected from the
              database (see :ref:`vo-sec-client-vos`).

            - Any of the above 3 options combined in a list, in which case
              they are tried in order.

    verbose : bool
        Verbose output.

    cache : bool
        Use caching for VO Service database. Access to actual VO
        websites referenced by the database still needs internet
        connection.

    query_all : bool
        This is used by :func:`search_all`.

    return_astropy_table : bool
        Returned ``obj`` will be `astropy.table.Table` rather
        than `astropy.io.votable.tree.TableElement`.

    use_names_over_ids : bool
        When `True` use the ``name`` attributes of columns as the names
        of columns in the `~astropy.table.Table` instance.  Since names
        are not guaranteed to be unique, this may cause some columns
        to be renamed by appending numbers to the end.  Otherwise
        (default), use the ID attributes as the column names.

    Returns
    -------
    obj : `astropy.table.Table` or `astropy.io.votable.tree.TableElement`
        First table from first successful VO service request.
        See ``return_astropy_table`` parameter for the kind of table returned.

    Raises
    ------
    ConeSearchError
        When invalid inputs are passed into Cone Search.

    """
    n_timed_out = 0
    service_type = conf.conesearch_dbname
    catalogs = vos_catalog._get_catalogs(
        service_type, catalog_db, cache=cache, verbose=verbose)
    if query_all:
        result = {}
    else:
        result = None

    for name, catalog in catalogs:
        if isinstance(catalog, str):
            if catalog.startswith('http'):
                url = catalog
            else:
                remote_db = vos_catalog.get_remote_catalog_db(
                    service_type, cache=cache, verbose=verbose)
                catalog = remote_db.get_catalog(catalog)
                url = catalog['url']
        else:
            url = catalog['url']

        if verbose:  # pragma: no cover
            color_print('Trying {0}'.format(url), 'green')

        try:
            r = ConeSearch.query_region(
                center, radius, verb=verb, cache=cache, verbose=verbose,
                service_url=url, return_astropy_table=return_astropy_table,
                use_names_over_ids=use_names_over_ids)
        except Exception as e:
            err_msg = str(e)
            vo_warn(W25, (url, err_msg))
            if not query_all and 'ConnectTimeoutError' in err_msg:
                n_timed_out += 1
        else:
            if r is not None:
                if query_all:
                    result[r.url] = r
                else:
                    result = r
                    break

    if result is None and n_timed_out > 0:
        err_msg = ('None of the available catalogs returned valid results.'
                   ' ({0} URL(s) timed out.)'.format(n_timed_out))
        warnings.warn(err_msg, NoResultsWarning)

    return result


class AsyncSearchAll(AsyncBase):
    """
    Perform a Cone Search asynchronously, storing all results
    instead of just the result from first successful query.

    .. note::

        See :class:`~astroquery.vo_conesearch.vo_async.AsyncBase`
        for more details.

    Parameters
    ----------
    args, kwargs
        See :func:`search_all`.

    Examples
    --------
    >>> from astropy import coordinates as coord
    >>> from astropy import units as u
    >>> from astroquery.vo_conesearch import conesearch
    >>> c = coord.ICRS(6.0223 * u.degree, -72.0814 * u.degree)
    >>> async_search = conesearch.AsyncSearchAll(c, 0.5 * u.degree)

    Check search status:

    >>> async_search.running()
    True
    >>> async_search.done()
    False

    Get a dictionary of all search results after a 30-second wait (not
    to be confused with ``astroquery.vo_conesearch.conf.timeout`` that
    governs individual Cone Search queries). If search is still not
    done after 30 seconds, `TimeoutError` is raised. Otherwise, a
    dictionary is returned and can be manipulated as in
    :ref:`Simple Cone Search Examples <vo-sec-scs-examples>`.
    If no ``timeout`` keyword given, it waits until completion:

    >>> async_allresults = async_search.get(timeout=60)
    >>> all_catalogs = list(async_allresults)
    >>> first_cone_arr = async_allresults[all_catalogs[0]]
    >>> len(first_cone_arr)
    74271

    """
    def __init__(self, *args, **kwargs):
        AsyncBase.__init__(self, search_all, *args, **kwargs)


def search_all(*args, **kwargs):
    """
    Perform Cone Search and returns the results of
    all successful queries.

    .. warning::

        Could potentially take up significant run time and
        computing resources.

    Parameters
    ----------
    args, kwargs
        Arguments and keywords accepted by :func:`conesearch`.

    Returns
    -------
    result : dict of `astropy.io.votable.tree.TableElement` objects
        A dictionary of tables from successful VO service requests,
        with keys being the access URLs. If none is successful,
        an empty dictionary is returned.

    Raises
    ------
    ConeSearchError
        When invalid inputs are passed into Cone Search.

    """
    kwargs['query_all'] = True
    return conesearch(*args, **kwargs)


def list_catalogs(**kwargs):
    """
    Return the available Cone Search catalogs as a list of strings.
    These can be used for the ``catalog_db`` argument to
    :func:`conesearch`.

    Parameters
    ----------
    cache : bool
        Use caching for VO Service database. Access to actual VO
        websites referenced by the database still needs internet
        connection.

    verbose : bool
        Show download progress bars.

    pattern : str or `None`
        If given string is anywhere in a catalog name, it is
        considered a matching catalog. It accepts patterns as
        in :py:mod:`fnmatch` and is case-insensitive.
        By default, all catalogs are returned.

    sort : bool
        Sort output in alphabetical order. If not sorted, the
        order depends on dictionary hashing. Default is `True`.

    Returns
    -------
    arr : list of str
        List of catalog names.

    """
    return vos_catalog.list_catalogs(conf.conesearch_dbname, **kwargs)


def predict_search(url, *args, **kwargs):
    """
    Predict the run time needed and the number of objects
    for a Cone Search for the given access URL, position, and
    radius.

    Run time prediction uses `astroquery.utils.timer.RunTimePredictor`.
    Baseline searches are done with starting and ending radii at
    0.05 and 0.5 of the given radius, respectively.

    Extrapolation on good data uses least-square straight line fitting,
    assuming linear increase of search time and number of objects
    with radius, which might not be accurate for some cases. If
    there are less than 3 data points in the fit, it fails.

    Warnings (controlled by :py:mod:`warnings`) are given when:

        #. Fitted slope is negative.
        #. Any of the estimated results is negative.
        #. Estimated run time exceeds
           ``astroquery.vo_conesearch.conf.timeout``.

    .. note::

        If ``verbose=True``, extra log info will be provided.
        But unlike :func:`conesearch_timer`, timer info is suppressed.

        The predicted results are just *rough* estimates.

        Prediction is done using
        :class:`astroquery.vo_conesearch.core.ConeSearchClass`.
        Prediction for :class:`AsyncConeSearch` is not supported.

    Parameters
    ----------
    url : str
        Cone Search access URL to use.

    plot : bool
        If `True`, plot will be displayed.
        Plotting uses matplotlib.

    args, kwargs
        See :meth:`astroquery.vo_conesearch.core.ConeSearchClass.query_region`.

    Returns
    -------
    t_est : float
        Estimated time in seconds needed for the search.

    n_est : int
        Estimated number of objects the search will yield.

    Raises
    ------
    AssertionError
        If prediction fails.

    ConeSearchError
        If input parameters are invalid.

    VOSError
        If VO service request fails.

    """
    if len(args) != 2:  # pragma: no cover
        raise ConeSearchError('conesearch must have exactly 2 arguments')

    kwargs['service_url'] = url
    kwargs['return_astropy_table'] = False
    plot = kwargs.pop('plot', False)
    center, radius = args
    sr = _validate_sr(radius)
    if sr <= 0:
        raise ConeSearchError('Search radius must be > 0 degrees')

    # Not using default ConeSearch instance because the attributes are
    # tweaked to match user inputs to this function.
    cs_pred = RunTimePredictor(ConeSearch.query_region, center, **kwargs)

    # Search properties for timer extrapolation
    num_datapoints = 10  # Number of desired data points for extrapolation
    sr_min = 0.05 * sr  # Min radius to start the timer
    sr_max = 0.5 * sr   # Max radius to stop the timer
    sr_step = (1.0 / num_datapoints) * (sr_max - sr_min)  # Radius step

    # Slowly increase radius to get data points for extrapolation
    sr_arr = np.arange(sr_min, sr_max + sr_step, sr_step)
    cs_pred.time_func(sr_arr)

    # Predict run time
    t_coeffs = cs_pred.do_fit()
    t_est = cs_pred.predict_time(sr)

    if t_est < 0 or t_coeffs[1] < 0:  # pragma: no cover
        warnings.warn(
            'Estimated runtime ({0} s) is non-physical with slope of '
            '{1}'.format(t_est, t_coeffs[1]), AstropyUserWarning)
    elif t_est > conf.timeout:  # pragma: no cover
        warnings.warn(
            'Estimated runtime is longer than timeout of '
            '{0} s'.format(conf.timeout), AstropyUserWarning)

    # Predict number of objects
    sr_arr = sorted(cs_pred.results)  # Orig with floating point error
    n_arr = [cs_pred.results[key].array.size for key in sr_arr]
    n_coeffs = np.polyfit(sr_arr, n_arr, 1)
    n_fitfunc = np.poly1d(n_coeffs)
    n_est = int(round(n_fitfunc(sr)))

    if n_est < 0 or n_coeffs[0] < 0:  # pragma: no cover
        warnings.warn('Estimated #objects ({0}) is non-physical with slope of '
                      '{1}'.format(n_est, n_coeffs[0]), AstropyUserWarning)

    if plot:  # pragma: no cover
        import matplotlib.pyplot as plt

        xlabeltext = 'radius (deg)'
        sr_fit = np.append(sr_arr, sr)
        n_fit = n_fitfunc(sr_fit)

        cs_pred.plot(xlabeltext=xlabeltext)

        fig, ax = plt.subplots()
        ax.plot(sr_arr, n_arr, 'kx-', label='Actual')
        ax.plot(sr_fit, n_fit, 'b--', label='Fit')
        ax.scatter([sr], [n_est], marker='o', c='r', label='Predicted')
        ax.set_xlabel(xlabeltext)
        ax.set_ylabel('#objects')
        ax.legend(loc='best', numpoints=1)
        plt.draw()

    return t_est, n_est


@timefunc(num_tries=1)
def conesearch_timer(*args, **kwargs):
    """
    Time a single Cone Search using `astroquery.utils.timer.timefunc`
    with a single try and a verbose timer.

    Parameters
    ----------
    args, kwargs
        See :func:`conesearch`.

    Returns
    -------
    t : float
        Run time in seconds.

    obj : `astropy.io.votable.tree.TableElement`
        First table from first successful VO service request.

    """
    return conesearch(*args, **kwargs)
