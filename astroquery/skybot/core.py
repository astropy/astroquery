# Licensed under a 3-clause BSD style license - see LICENSE.rst

import warnings

import astropy.units as u
from astropy.time import Time
from astropy.table import QTable
from astropy.coordinates import SkyCoord, Angle
from astropy.io import ascii

from ..query import BaseQuery
from ..utils import commons
from ..utils import async_to_sync
from . import conf

__all__ = ['Skybot', 'SkybotClass']


@async_to_sync
class SkybotClass(BaseQuery):
    """A class for querying the `IMCCE SkyBoT
    <http://vo.imcce.fr/webservices/skybot>`_ service.
    """
    _uri = None  # query uri

    @property
    def uri(self):
        """
        URI used in query to service.

        Examples
        --------

        >>> from astroquery.skybot import Skybot
        >>> skybot = Skybot()
        >>> obj = skybot.cone_search((1, 1), 0.1, 2451200) # doctest: +SKIP
        >>> obj.uri # doctest: +SKIP
        'http://vo.imcce.fr/webservices/skybot/skybotconesearch_query.php?-ra=1.0&-dec=1.0&-rd=0.1&-ep=2451200.0&-loc=500&-filter=120.0&-objFilter=111&-refsys=EQJ2000&-output=all&-mime=text'
        """
        return self._uri

    def cone_search_async(self,
                          coo,
                          rad,
                          epoch,
                          location='500',
                          position_error=120,
                          find_planets=True,
                          find_asteroids=True,
                          find_comets=True,
                          get_query_payload=False,
                          get_raw_response=False,
                          cache=True):
        """
        This method queries the IMCCE
        `SkyBoT <http://vo.imcce.fr/webservices/skybot/?conesearch>`_
        cone search service and produces a `~astropy.table.QTable` object
        containing all Solar System bodies that might be in the cone
        defined by the cone center coordinates and epoch provided.

        Parameters
        ----------
        coo : `~astropy.coordinates.SkyCoord` object or tuple
            Center coordinates of the search cone in ICRS coordinates. If
            provided as tuple, the input is excepted as (right ascension
            in degrees, declination in degrees).
        rad : `~astropy.coordinates.Angle` object or float
            Radius of the search cone. `~astropy.units` are taken into
            account.; if no units are provided (input as float), degrees
            are assumed. The maximum search radius is 10 degrees; if this
            maximum radius is exceeded, it will be clipped and a warning
            will be provided to the user.
        epoch : `~astropy.time.Time` object, float, or string
            Epoch of search process. If provided as float, it is interpreted
            as Julian Date, if provided as string, it is interpreted as
            date in the form ``'YYYY-MM-DD HH-MM-SS'``.
        location : int or str, optional
            Location of the observer on Earth as defined in the official
            `list of IAU codes
            <https://www.minorplanetcenter.net/iau/lists/ObsCodes.html>`_.
            Default: geocentric location (``'500'``)
        position_error : `~astropy.coordinates.Angle` or float, optional
            Maximum positional error for targets to be queried. If no
            unit is provided, arcseconds are assumed. Maximum positional
            error is 120 arcseconds, larger values are clipped and warning
            will be provided to the user. Default: 120 arcseconds
        find_planets : boolean, optional
            If ``True``, planets will be included in the search. Default:
            ``True``
        find_asteroids : boolean, optional
            If ``True``, asteroids will be included in the search. Default:
            ``True``
        find_comets : boolean, optional
            If ``True``, comets will be included in the search. Default:
            ``True``
        get_query_payload : boolean, optional
            Returns the query payload only and performs no query.
            Default: ``False``
        get_raw_response : boolean, optional
            Returns the raw response as provided by the IMCCE server instead
            of the parsed output. Default: ``False``
        cache : boolean, optional
            Cache this specfific query so it might be retrieved faster in
            the future. Default: ``True``

        Notes
        -----
        The following parameters are queried from the SkyBoT service:

        +------------------+-----------------------------------------------+
        | Column Name      | Definition                                    |
        +==================+===============================================+
        | ``'Number'``     | Target Number (``-1`` if none provided, int)  |
        +------------------+-----------------------------------------------+
        | ``'Name'``       | Target Name (str)                             |
        +------------------+-----------------------------------------------+
        | ``'RA'``         | Target RA (J2000, deg, float)                 |
        +------------------+-----------------------------------------------+
        | ``'DEC'``        | Target declination (J2000, deg, float)        |
        +------------------+-----------------------------------------------+
        | ``'Type'``       | Target dynamical/physical type (str)          |
        +------------------+-----------------------------------------------+
        | ``'V'``          | Target apparent brightness (V-band, mag,      |
        |                  | float)                                        |
        +------------------+-----------------------------------------------+
        | ``'posunc'``     | Positional uncertainty (arcsec, float)        |
        +------------------+-----------------------------------------------+
        | ``'centerdist'`` | Angular distance of target from cone center   |
        |                  | (arcsec, float)                               |
        +------------------+-----------------------------------------------+
        | ``'RA_rate'``    | RA rate of motion (arcsec/hr, float)          |
        +------------------+-----------------------------------------------+
        | ``'DEC_rate'``   | Declination rate of motion (arcsec/hr, float) |
        +------------------+-----------------------------------------------+
        | ``'geodist'``    | Geocentric distance of target (au, float)     |
        +------------------+-----------------------------------------------+
        | ``'heliodist'``  | Heliocentric distance of target (au, float)   |
        +------------------+-----------------------------------------------+
        | ``'alpha'``      | Solar phase angle (deg, float)                |
        +------------------+-----------------------------------------------+
        | ``'elong'``      | Solar elongation angle (deg, float)           |
        +------------------+-----------------------------------------------+
        | ``'x'``          | Target equatorial vector x (au, float)        |
        +------------------+-----------------------------------------------+
        | ``'y'``          | Target equatorial vector y (au, float)        |
        +------------------+-----------------------------------------------+
        | ``'z'``          | Target equatorial vector z (au, float)        |
        +------------------+-----------------------------------------------+
        | ``'vx'``         | Target velocity vector x (au/d, float)        |
        +------------------+-----------------------------------------------+
        | ``'vy'``         | Target velocity vector y (au/d, float)        |
        +------------------+-----------------------------------------------+
        | ``'vz'``         | Target velocity vector z (au/d, float)        |
        +------------------+-----------------------------------------------+
        | ``'epoch'``      | Ephemerides epoch (JD, float)                 |
        +------------------+-----------------------------------------------+

        Examples
        --------
        >>> from astroquery.skybot import Skybot
        >>> obj = Skybot.cone_search((1, 1), 0.1, 2451200) # doctest: +SKIP
           Name           RA                DEC          V      Type
                         deg                deg         mag
        --------- ------------------ ------------------ ---- ---------
        2001 HL61 1.0318587499999998 1.0419800000000001 20.8 MB>Middle
        2005 OT10 0.9520820833333332 0.9630413888888888 21.0  MB>Inner
        2007 FD47 0.9953599999999999 0.9018569444444444 22.0  MB>Outer
        """

        URL = conf.server
        TIMEOUT = conf.timeout

        # check for types and units
        if not isinstance(coo, SkyCoord):
            coo = SkyCoord(ra=coo[0]*u.degree,
                           dec=coo[1]*u.degree, frame='icrs')
        if not isinstance(rad, Angle):
            rad = Angle(rad, unit=u.degree)
        if rad > Angle(10, unit=u.degree):
            rad = Angle(10, unit=u.degree)
            warnings.warn('search cone radius set to maximum: 10 deg',
                          UserWarning)
        if isinstance(epoch, (int, float)):
            epoch = Time(epoch, format='jd')
        elif isinstance(epoch, str):
            epoch = Time(epoch, format='iso')
        if not isinstance(position_error, Angle):
            position_error = Angle(position_error, unit=u.arcsec)
        if position_error > Angle(120, unit=u.arcsec):
            position_error = Angle(120, unit=u.arcsec)
            warnings.warn('positional error set to maximum: 120 arcsec',
                          UserWarning)

        # assemble payload
        request_payload = {'-ra': coo.ra.deg,
                           '-dec': coo.dec.deg,
                           '-rd': rad.deg,
                           '-ep': str(epoch.jd),
                           '-loc': str(location),
                           '-filter': position_error.arcsec,
                           '-objFilter':
                           str(int(find_asteroids)) +
                           str(int(find_planets)) +
                           str(int(find_comets)),
                           '-refsys': 'EQJ2000',
                           '-output': 'all',
                           '-mime': 'text'}

        # check for diagnostic flags
        if get_query_payload:
            return request_payload
        if get_raw_response:
            self._raw_response = True

        response = self._request(method='GET', url=URL,
                                 params=request_payload,
                                 timeout=TIMEOUT, cache=cache)

        if get_raw_response:
            self._return_raw = True

        self._uri = response.url

        return response

    def _parse_result(self, response, verbose=False):
        """
        internal wrapper to parse queries
        """

        if hasattr(self, '_raw_response') and self._raw_response is True:
            return response.text

        # intercept error messages
        response_txt = response.text.split('\n')[2:-1]
        if len(response_txt) < 3 and len(response_txt[-1].split('|')) < 21:
            raise RuntimeError(response_txt[-1])

        results = ascii.read(response_txt[1:], delimiter='|',
                             names=response_txt[0].replace('# ',
                                                           '').split(' | '))
        results = QTable(results)

        # convert coordinates to degrees
        coo = SkyCoord(ra=results['RA(h)'], dec=results['DE(deg)'],
                       unit=(u.hourangle, u.deg), frame='icrs')
        results['RA(h)'] = coo.ra.deg
        results['DE(deg)'] = coo.dec.deg

        colnames = results.columns[:]
        for fieldname in colnames:
            # apply field name change
            results.rename_column(fieldname, conf.field_names[fieldname])
            # apply unit, if available
            if conf.field_names[fieldname] in conf.field_units:
                results[conf.field_names[fieldname]].unit = conf.field_units[
                    conf.field_names[fieldname]]

        # convert object numbers to int
        results['Number'] = [int(float(n)) for n in results['Number']]

        return results


Skybot = SkybotClass()
