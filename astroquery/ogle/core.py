# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import warnings
import functools
import numpy as np
from astropy.table import Table

from ..query import BaseQuery
from ..utils.class_or_instance import class_or_instance
from ..utils import commons, async_to_sync
from ..utils.docstr_chompers import prepend_docstr_noreturns

from . import OGLE_SERVER, OGLE_TIMEOUT

__all__ = ['Ogle']



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
        super(ValueError, self).__init__(message, **kwargs)


@async_to_sync
class Ogle(BaseQuery):

    DATA_URL = OGLE_SERVER()
    TIMEOUT = OGLE_TIMEOUT()

    algorithms = ['NG', 'NN']
    quality_codes = ['GOOD', 'ALL']
    coord_systems = ['RD', 'LB']
    result_dtypes = ['f8', 'f8', 'f8', 'f8', 'f8', 'f8', 'f8', 'f8', 'i8', 'a2',
                     'f8']

    @class_or_instance
    @_validate_params
    def _args_to_payload(self, coord=None, algorithm='NG', quality='GOOD',
                         coord_sys='RD'):
        """
        Query the OGLE-III interstellar extinction calculator.

        Parameters
        ----------
        coord : list-like
            Pointings to evaluate interstellar extinction. Three forms of
            coordinates may be passed:
                * single astropy coordinate instance
                * list-like object (1 x N) of astropy coordinate instances
                * list-like object (2 x N) of RA/Decs or Glon/Glat as strings or
                  floats. (May not be supported in future versions.)
        algorithm : string
            Algorithm to interpolate data for desired coordinate. Valid options:
                * 'NG': nearest grid point
                * 'NN': natural neighbor interpolation
        quality : string
            Quality factor for data. Valid options:
                * 'All': all points
                * 'GOOD': QF=0 as described in Nataf et al. (2012).
        coord_sys : string
            Coordinate system if using lists of RA/Decs in `coord`. Valid options:
                * 'RD': equatorial coordinates
                * 'LB': Galactic coordinates.

        Returns
        -------
        astropy.table.Table

        Raises
        ------
        CoordParseError
            Exception raised for malformed coordinate input

        Examples
        --------
        Using astropy coordinates:
        >>> from astropy import coordinates as coord
        >>> from astropy import units as u
        >>> co = coord.Galactic(0.0, 3.0, unit=(u.degree, u.degree))
        >>> t = ogle.query(coord=co)
        >>> t.pprint()
          RA/LON   Dec/Lat    A_I  E(V-I) S_E(V-I) R_JKVI   mu    S_mu
        --------- ---------- ----- ------ -------- ------ ------ ----- ...
        17.568157 -27.342475 3.126  2.597    0.126 0.3337 14.581 0.212
        """
        # Determine the coord object type and generate list of coordinates
        lon, lat = self._parse_coords(coord, coord_sys)
        # Generate payload
        query_header = '# {0} {1} {2}\n'.format(coord_sys, algorithm, quality)
        sources = '\n'.join(['{0} {1}'.format(lon, lat) for lon, lat in
                            zip(lon, lat)])
        file_data = query_header + sources
        files = {'file1': file_data}
        return files

    @class_or_instance
    @prepend_docstr_noreturns(_args_to_payload.__doc__)
    def query_region_async(self, *args, **kwargs):
        """
        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """
        files = self._args_to_payload(*args, **kwargs)
        # Make request
        params = {'dnfile':'submit'}
        response = commons.send_request(url=self.DATA_URL,
                                        data=params,
                                        timeout=self.TIMEOUT,
                                        files=files,
                                        request_type='POST')
        response.raise_for_status()
        return response

    @class_or_instance
    def _parse_result(self, response, verbose=False):
        # Parse table, ignore last two (blank) lines
        raw_data = response.text.split('\n')[:-2]
        # Select first row and skip first character ('#') to find column headers
        header = raw_data[0][1:].encode('ascii').split()
        data = self._parse_raw(raw_data)
        t = Table(data, names=header, dtypes=self.result_dtypes)
        return t

    @class_or_instance
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
                lon = [coord.fk5.ra.hour]
                lat = [coord.fk5.dec.degree]
                return lon, lat
            except:
                raise CoordParseError()
        elif isinstance(coord, list):
            shape = np.shape(coord)
            # list of astropy coordinates
            if len(shape) == 1:
                try:
                    lon = [co.fk5.ra.hour for co in coord]
                    lat = [co.fk5.dec.degree for co in coord]
                    return lon, lat
                except:
                    raise CoordParseError()
            # list-like of values
            elif (len(shape) == 2) & (shape[0] == 2):
                warnings.warn('Non-Astropy coordinates may not be supported \
                              in a future version.', FutureWarning)
                return coord
            else:
                raise CoordParseError()
        else:
            raise CoordParseError()

    @class_or_instance
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
        data = [line.encode('ascii').split() for line in raw_data[1:]]
        # Transpose while keeping as list of lists
        data = map(list, zip(*data))
        return data
