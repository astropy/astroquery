# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import six
from six import BytesIO
from six.moves import urllib

from numbers import Number

from astropy import units as u
from astropy.coordinates import (BaseCoordinateFrame, ICRS, SkyCoord,
                                 Longitude, Latitude)
from astropy.io.votable import table

from .exceptions import ConeSearchError, InvalidAccessURL
from .vos_catalog import vo_tab_parse
from ..query import BaseQuery
from ..utils import commons

# Import configurable items declared in __init__.py
from . import conf

__all__ = ['ConeSearch', 'ConeSearchClass']

__doctest_skip__ = ['ConeSearchClass']


class ConeSearchClass(BaseQuery):
    """
    The class for querying the Virtual Observatory (VO)
    Cone Search web service.

    Examples
    --------
    >>> from astropy import units as u
    >>> from astropy.coordinates import SkyCoord
    >>> from astroquery.vo_conesearch import ConeSearch
    >>> ConeSearch.query_region(SkyCoord.from_name('M31'), 5 * u.arcsecond)
    <Table masked=True length=6>
        objID           gscID2      ... compassGSC2id   Mag
                                    ...                 mag
        int64           object      ...     object    float32
    -------------- ---------------- ... ------------- -------
    23323175812944 00424433+4116085 ... 6453800072293      --
    23323175812933 00424455+4116103 ... 6453800072282      --
    23323175812939 00424464+4116092 ... 6453800072288      --
    23323175812931 00424464+4116106 ... 6453800072280      --
    23323175812948 00424403+4116069 ... 6453800072297      --
    23323175812930 00424403+4116108 ... 6453800072279      --
    """
    TIMEOUT = conf.timeout
    URL = conf.fallback_url
    PEDANTIC = conf.pedantic

    def __init__(self):
        if not self.URL.endswith(('?', '&')):
            raise InvalidAccessURL("URL should end with '?' or '&'")

        super(ConeSearchClass, self).__init__()

    def query_region_async(self, *args, **kwargs):
        """
        This is not implemented. Use
        :class:`~astroquery.vo_conesearch.conesearch.AsyncConeSearch` instead.
        """
        raise NotImplementedError(
            'Use astroquery.vo_conesearch.conesearch.AsyncConeSearch class.')

    def query_region(self, coordinates, radius, verb=1,
                     get_query_payload=False, cache=True, verbose=False):
        """
        Perform Cone Search and returns the result of the
        first successful query.

        Parameters
        ----------
        coordinates : str, `astropy.coordinates` object, list, or tuple
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
                - If `~astropy.units.quantity.Quantity` is given,
                  it is internally converted to degrees.

        verb : {1, 2, 3}, optional
            Verbosity indicating how many columns are to be returned
            in the resulting table. Support for this parameter by
            a Cone Search service implementation is optional.
            If the service supports the parameter:

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

        get_query_payload : bool, optional
            Just return the dict of HTTP request parameters.

        cache : bool, optional
            Use caching for VO Service database. Access to actual VO
            websites referenced by the database still needs internet
            connection.

        verbose : bool, optional
            Verbose output, including VO table warnings.

        Returns
        -------
        result : `astropy.io.votable.tree.Table`
            Table from successful VO service request.

        """
        request_payload = self._args_to_payload(coordinates, radius, verb)

        if get_query_payload:
            return request_payload

        # && in URL can break some queries, so remove trailing & if needed
        if self.URL.endswith('&'):
            url = self.URL[:-1]
        else:
            url = self.URL

        response = self._request('GET', url, params=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        result = self._parse_result(response, pars=request_payload,
                                    verbose=verbose)
        return result

    def _args_to_payload(self, coordinates, radius, verb):
        """
        Takes the arguments from any of the query functions and returns a
        dictionary that can be used as the data for an HTTP POST request.
        """
        ra, dec = _validate_coord(coordinates)
        sr = _validate_sr(radius)
        v = _validate_verb(verb)
        return {'RA': ra, 'DEC': dec, 'SR': sr, 'VERB': v}

    def _parse_result(self, response, pars={}, verbose=False):
        """
        Parse the raw HTTP response and return it as a table.
        """
        # Suppress any VOTable related warnings.
        if not verbose:
            commons.suppress_vo_warnings()

        query = []
        for key, value in six.iteritems(pars):
            query.append('{0}={1}'.format(urllib.parse.quote(key),
                                          urllib.parse.quote_plus(str(value))))
        parsed_url = self.URL + '&'.join(query)

        # Parse the result
        tab = table.parse(BytesIO(response.content), filename=parsed_url,
                          pedantic=self.PEDANTIC)
        return vo_tab_parse(tab, self.URL, pars)


def _validate_coord(coordinates):
    """Validate coordinates and return them as ICRS RA and DEC in deg."""
    if isinstance(coordinates, (list, tuple)) and len(coordinates) == 2:
        icrscoord = ICRS(Longitude(coordinates[0], unit=u.degree),
                         Latitude(coordinates[1], unit=u.degree))
    else:
        c = commons.parse_coordinates(coordinates)
        if isinstance(c, SkyCoord):
            icrscoord = c.transform_to(ICRS).frame
        elif isinstance(c, BaseCoordinateFrame):
            icrscoord = c.transform_to(ICRS)
        else:  # Assume already ICRS
            icrscoord = c

    return icrscoord.ra.degree, icrscoord.dec.degree


def _validate_sr(radius):
    """Validate search radius and return value in deg."""
    if isinstance(radius, Number):
        sr = radius
    else:
        sr = commons.radius_to_unit(radius)

    return sr


def _validate_verb(verb):
    """Validate verbosity."""
    try:
        v = int(verb)
    except ValueError:
        v = 999
    if v not in (1, 2, 3):
        raise ConeSearchError('Verbosity must be 1, 2, or 3')

    return v


ConeSearch = ConeSearchClass()
