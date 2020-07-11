# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
Module to query the IMCCE Miriade service

:author: Miguel de Val-Borro <miguel.deval@gmail.com>
"""
from __future__ import print_function

# 2. third party imports
from astropy.io import ascii
from astropy.time import Time

# 3. local imports - use relative imports
# commonly required local imports shown below as example
# all Query classes should inherit from BaseQuery.
from ..query import BaseQuery
# async_to_sync generates the relevant query tools from _async methods
from ..utils import async_to_sync
# import configurable items declared in __init__.py
from . import conf

__all__ = ['Miriade', 'MiriadeClass']


@async_to_sync
class MiriadeClass(BaseQuery):
    """
    A class for querying the `IMCCE Miriade
    <http://vo.imcce.fr/webservices/miriade/miriade.php>`_ service.
    """

    TIMEOUT = conf.timeout

    TYPES = ('Asteroid', 'Comet', 'Dwarf Planet', 'Planet', 'Satellite')
    TSCALE = ('UTC', 'TT')
    THEORY = ('INPOP', 'DE405', 'DE406')
    OSCELEM = ('astorb', 'mpcorb', 'mpcorb/nea')

    def ephemerides_async(self, name=None, type=None, ep=None, nbd=1,
                          step='1d', tscale='UTC', observer='500',
                          theory='INPOP', teph=1, tcoor=1, rplane=1,
                          oscelem='astorb', cache=True,
                          get_query_payload=False):
        """
        Parameters
        ----------
        name : str, required
            Name, or designation of the target to be queried.
        type : str, optional
            Type of the target. Possible options are 'Asteroid',
            'Comet', 'Dwarf Planet', 'Planet' or 'Satellite'.
        ep : str, optional
            Requested epoch, expressed in Julian day, ISO format,
            or formatted as any English textual datetime If no epoch
            is provided, the current time is used.
        nbd : int, optional
            Number of dates of ephemeris to compute. Default: 1.
        step : str, optional
            Step of increment (float) followed by one of
            (d)ays or (h)ours or (m)inutes or (s)econds.
            Default: '1d'.
        tscale : str, optional
            Ephemeris time scale. Possible options are 'UTC' or 'TT'.
            Default: 'UTC'.
        observer : str, optional
            `Observatory's code
            <https://www.minorplanetcenter.net/iau/lists/ObsCodesF.html>`_.
            or geographic coordinates of the observer's location
            for ephemerides queries.  If no location is provided,
            Earth's center is used for ephemerides queries (500).
        theory : str, optional
            Planetary theory to use for the calculation.
            Possible options are 'INPOP', 'DE405' or 'DE406'.
            Default: 'INPOP'.
        teph : int, optional
            Type of ephemeris: 1: astrometric J2000, 2: apparent of
            the date, 3: mean of the date, 4: mean J2000. Default: 1.
        tcoor: int, optional
            Type of coordinates: 1:spherical, 2:rectangular, 3: Local
            coordinates, 4: Hour angle coordinates, 5: dedicated to
            observation, 6: dedicated to AO observation.
            Default: 1.
        rplane : int, optional
            Reference plane: 1: equator, 2: ecliptic
            Default: 1.
        oscelem : str, optional
            Source of osculating elements for asteroids:
            'ASTORB' or 'MPCORB'. Default: 'ASTORB'.

        Returns
        -------
        response : `requests.Response`
            The response of the HTTP request.

        Examples
        --------
            >>> from astroquery.miriade import Miriade
            >>> ceres = Miriade.ephemerides(name='a:Ceres', observer='568',
            ...                            ep='2017-01-01', nbd=31)
            >>> print(ceres)  # doctest: +SKIP
            Date UTC (Y-M-D h:m:s)   RA (h m s)  ... muDE (arcsec/min) Dist_dot (km/s)
            ---------------------- ------------- ... ----------------- ---------------
            2017-01-01T00:00:00.00 1 34  0.84372 ...            0.2961         22.2838
            2017-01-02T00:00:00.00 1 34 23.89404 ...            0.2995        22.35694
            2017-01-03T00:00:00.00 1 34 48.18172 ...            0.3029        22.42349
            2017-01-04T00:00:00.00 1 35 13.69205 ...            0.3061        22.48361
            2017-01-05T00:00:00.00 1 35 40.40984 ...            0.3093        22.53746
            2017-01-06T00:00:00.00 1 36  8.31953 ...            0.3124        22.58526
            2017-01-07T00:00:00.00 1 36 37.40523 ...            0.3154        22.62724
            2017-01-08T00:00:00.00 1 37  7.65088 ...            0.3183        22.66367
            2017-01-09T00:00:00.00 1 37 39.04042 ...            0.3211        22.69483
            2017-01-10T00:00:00.00 1 38 11.55792 ...            0.3238        22.72099
            2017-01-11T00:00:00.00 1 38 45.18784 ...            0.3264        22.74241
            2017-01-12T00:00:00.00 1 39 19.91517 ...             0.329        22.75927
            2017-01-13T00:00:00.00 1 39 55.72556 ...            0.3315        22.77171
            2017-01-14T00:00:00.00 1 40 32.60534 ...            0.3339        22.77977
            2017-01-15T00:00:00.00 1 41 10.54144 ...            0.3362        22.78343
            2017-01-16T00:00:00.00 1 41 49.52132 ...            0.3385        22.78265
            2017-01-17T00:00:00.00 1 42 29.53274 ...            0.3407        22.77737
            2017-01-18T00:00:00.00 1 43 10.56372 ...            0.3429        22.76753
            2017-01-19T00:00:00.00 1 43 52.60238 ...            0.3449        22.75309
            2017-01-20T00:00:00.00 1 44 35.63693 ...            0.3469        22.73402
            2017-01-21T00:00:00.00 1 45 19.65558 ...            0.3489        22.71029
            2017-01-22T00:00:00.00 1 46  4.64658 ...            0.3507        22.68191
            2017-01-23T00:00:00.00 1 46 50.59818 ...            0.3525        22.64887
            2017-01-24T00:00:00.00 1 47 37.49863 ...            0.3543        22.61117
            2017-01-25T00:00:00.00 1 48 25.33617 ...            0.3559        22.56881
            2017-01-26T00:00:00.00 1 49 14.09897 ...            0.3576        22.52179
            2017-01-27T00:00:00.00 1 50  3.77515 ...            0.3591        22.47012
            2017-01-28T00:00:00.00 1 50 54.35269 ...            0.3606        22.41383
            2017-01-29T00:00:00.00 1 51 45.81939 ...             0.362        22.35296
            2017-01-30T00:00:00.00 1 52 38.16287 ...            0.3633        22.28758
            2017-01-31T00:00:00.00 1 53 31.37053 ...            0.3646        22.21781
        """
        URL = conf.miriade_server

        payload = dict()

        # check for required information
        if type in self.TYPES:
            payload['-type'] = type
        elif type is not None:
            raise ValueError("Invalid type specified.  Allowed types "
                             "are {0}".format(str(self.TYPES)))

        if nbd >= 1 and nbd <= 5000:
            payload['-nbd'] = nbd
        else:
            raise ValueError("Invalid nbd specified. 1 <= nbd <= 5000")

        if (step[-1] in ('d', 'h', 'm', 's') and
            step[:-1].replace('.', '', 1).isdigit()):
            payload['-step'] = step
        else:
            raise ValueError("Invalid step specified. Step (float) "
                             "followed by one of (d)ays or (h)ours or "
                             "(m)inutes or (s)econds")

        if tscale in self.TSCALE:
            payload['-tscale'] = tscale
        else:
            raise ValueError("Invalid tscale specified.  Allowed types "
                             "are {0}".format(str(self.TSCALE)))

        if theory in self.THEORY:
            payload['-theory'] = theory
        else:
            raise ValueError("Invalid theory specified.  Allowed types "
                             "are {0}".format(str(self.THEORY)))

        if teph in range(1, 5):
            payload['-teph'] = teph
        else:
            raise ValueError("Invalid teph specified. 1 <= teph <= 4")

        if tcoor in range(1, 7):
            payload['-tcoor'] = tcoor
        else:
            raise ValueError("Invalid tcoor specified. 1 <= tcoor <= 6")

        if rplane in (1, 2):
            payload['-rplane'] = rplane
        else:
            raise ValueError("Invalid rplane specified. 1 <= rplane <= 2")

        if name is None:
            raise ValueError("'name ' parameter not set. Query aborted.")

        if ep is None:
            ep = Time.now().jd

        payload['-name'] = name
        payload['-ep'] = ep
        payload['-mime'] = "text/csv"

        # return payload if desired
        if get_query_payload:
            return payload

        # query and parse
        response = self._request('GET', URL, params=payload,
                                 timeout=self.TIMEOUT, cache=cache)

        return response

    def _parse_result(self, response, verbose=None):
        """
        Routine for parsing data from IMCCE Miriade

        Parameters
        ----------
        self : MiriadeClass instance
        response : string
            raw response from server


        Returns
        -------
        data : `astropy.Table`

        """

        data = ascii.read(response.text.replace('# Date', 'Date'),
                          header_start=0)

        # set column units
        for col in list(data.columns):
            data[col].unit = conf.eph_columns[col][1]
            try:
                data.rename_column(col, conf.eph_columns[col][0])
            except KeyError:
                pass

        return data


# the default tool for users to interact with is an instance of the Class
Miriade = MiriadeClass()
