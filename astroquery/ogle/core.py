# Licensed under a 3-clause BSD style license - see LICENSE.rst


import warnings
import functools
import numpy as np
from astropy.table import Table
from astropy.utils.exceptions import AstropyDeprecationWarning

from ..query import BaseQuery
from ..utils import commons, async_to_sync, prepend_docstr_nosections

from . import conf

__all__ = ['Ogle', 'OgleClass']

__doctest_skip__ = ['OgleClass.*']


def _validate_params(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        algorithm = kwargs.get('algorithm')
        quality = kwargs.get('quality')
        coord_sys = kwargs.get('coord_sys')
        # if unspecified, the defaults (which are OK) will be used
        if algorithm is not None and algorithm not in Ogle.algorithms:
            raise ValueError("'algorithm` must be one of \
                             {!s}".format(Ogle.algorithms))
        if quality is not None and quality not in Ogle.quality_codes:
            raise ValueError("'quality' must be one of \
                             {!s}".format(Ogle.quality_codes))
        if coord_sys is not None and coord_sys not in Ogle.coord_systems:
            raise ValueError("'coord_sys' must be one of \
                    {!s}".format(Ogle.coord_systems))
        return func(*args, **kwargs)
    return wrapper


class CoordParseError(ValueError):

    def __init__(self, message='Could not parse `coord` argument.', **kwargs):
        super().__init__(message, **kwargs)


@async_to_sync
class OgleClass(BaseQuery):

    DATA_URL = conf.server
    TIMEOUT = conf.timeout

    algorithms = ['NG', 'NN']
    quality_codes = ['GOOD', 'ALL']
    coord_systems = ['RD', 'LB']

    @_validate_params
    def _args_to_payload(self, *, coord=None, algorithm='NG', quality='GOOD',
                         coord_sys='RD'):
        """
        Query the OGLE-III interstellar extinction calculator.

        Parameters
        ----------
        coord : list-like
            Pointings to evaluate interstellar extinction. Three forms of
            coordinates may be passed::

                * single astropy coordinate instance
                * list-like object (1 x N) of astropy coordinate instances
                * list-like object (2 x N) of RA/Decs or Glon/Glat as strings
                or  floats. (May not be supported in future versions.)

        algorithm : string
            Algorithm to interpolate data for desired coordinate.
            Valid options::

                * 'NG': nearest grid point
                * 'NN': natural neighbor interpolation

        quality : string
            Quality factor for data. Valid options::

                * 'All': all points
                * 'GOOD': QF=0 as described in Nataf et al. (2012).

        coord_sys : string
            Coordinate system if using lists of RA/Decs in ``coord``.
            Valid options::

                * 'RD': equatorial coordinates
                * 'LB': Galactic coordinates.

        Returns
        -------
        table : `~astropy.table.Table`

        Raises
        ------
        CoordParseError
            Exception raised for malformed coordinate input

        Examples
        --------
        Using astropy coordinates:

        >>> from astropy.coordinates import SkyCoord
        >>> from astropy import units as u
        >>> co = SkyCoord(0.0, 3.0, unit=(u.degree, u.degree),
        ...               frame='galactic')
        >>> from astroquery.ogle import Ogle
        >>> t = Ogle.query_region(coord=co)
        >>> t.pprint()
        RA/LON   Dec/Lat    A_I  E(V-I) S_E(V-I) R_JKVI   mu    S_mu
        --------- ---------- ----- ------ -------- ------ ------ ----- ...
        17.568157 -27.342475 3.126  2.597    0.126 0.3337 14.581 0.212
        """
        # Determine the coord object type and generate list of coordinates
        lon, lat = self._parse_coords(coord, coord_sys)
        # Generate payload
        query_header = '# {0} {1} {2}\n'.format(coord_sys, algorithm, quality)
        sources = '\n'.join(['{0} {1}'.format(lo, la) for lo, la in
                             zip(lon, lat)])
        file_data = query_header + sources
        files = {'file1': file_data}
        return files

    @prepend_docstr_nosections(_args_to_payload.__doc__)
    def query_region_async(self, *args, **kwargs):
        """
        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """
        files = self._args_to_payload(*args, **kwargs)
        # Make request
        params = {'dnfile': 'submit'}
        response = self._request("POST", url=self.DATA_URL, data=params,
                                 timeout=self.TIMEOUT, files=files)

        response.raise_for_status()
        return response

    def _parse_result(self, response, *, verbose=False):
        # Header is in first row starting with #, this works with the default
        t = Table.read(response.text.split('\n'), format='ascii')
        return t

    def _parse_coords(self, coord, coord_sys):
        """
        Parse single astropy.coordinates instance, list of astropy.coordinate
        instances, or 2xN list of coordinate values.

        Parameters
        ----------
        coord : list-like
        coord_sys : string

        Returns
        -------
        lon : list
            Longitude coordinate values
        lat : list
            Latitude coordinate values
        """
        if not isinstance(coord, list):
            # single astropy coordinate
            try:
                ra, dec = commons.coord_to_radec(coord)
                lon = [ra]
                lat = [dec]
                return lon, lat
            except ValueError:
                raise CoordParseError()
        elif isinstance(coord, list):
            shape = np.shape(coord)
            # list of astropy coordinates
            if len(shape) == 1:
                try:
                    radec = [commons.coord_to_radec(co) for co in coord]
                    lon, lat = list(zip(*radec))
                    return lon, lat
                except ValueError:
                    raise CoordParseError()
            # list-like of values
            elif (len(shape) == 2) & (shape[0] == 2):
                warnings.warn('Non-Astropy coordinates may not be supported '
                              'in a future version.', AstropyDeprecationWarning)
                return coord
            else:
                raise CoordParseError()
        else:
            raise CoordParseError()

    def _parse_raw(self, raw_data):
        """
        Parse the raw strings returned from the query request and return a list
        of lists for each column in string format.

        Parameters
        ----------
        raw_data : list
            Raw data from the request formatted to as list of strings for each
            line

        Returns
        -------
        data : list
            List of lists for each column as strings
        """
        # Requests returns unicode encoding, return to ascii
        data = [line.split() for line in raw_data[1:]]
        # Transpose while keeping as list of lists
        data = list(map(list, zip(*data)))
        return data


Ogle = OgleClass()
