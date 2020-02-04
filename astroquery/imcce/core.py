# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

from collections import OrderedDict
import warnings
from io import BytesIO

from astropy.table import QTable, MaskedColumn
from astropy.io import ascii
from astropy.time import Time
from astropy.io.votable import parse
import astropy.units as u
from astropy.coordinates import SkyCoord, Angle

from ..query import BaseQuery
from ..utils import async_to_sync, commons
from . import conf

__all__ = ['Miriade', 'MiriadeClass', 'Skybot', 'SkybotClass']


@async_to_sync
class MiriadeClass(BaseQuery):
    """
    A class for querying the
    `IMCCE/Miriade <http://vo.imcce.fr/webservices/miriade/>`_ service.
    """

    _query_uri = None  # uri used in query
    _get_raw_response = False

    @property
    def uri(self):
        """
        URI used in query to service.
        """
        return self._query_uri

    def get_ephemerides_async(self, targetname, objtype='asteroid',
                              epoch=None, epoch_step='1d', epoch_nsteps=1,
                              location=500, coordtype=1,
                              timescale='UTC',
                              planetary_theory='INPOP',
                              ephtype=1,
                              refplane='equator',
                              elements='ASTORB',
                              radial_velocity=False,
                              get_query_payload=False,
                              get_raw_response=False, cache=True):
        """
        Query the
        `IMCCE Miriade <http://vo.imcce.fr/webservices/miriade/>`_
        `ephemcc <http://vo.imcce.fr/webservices/miriade/?ephemcc>`_
        service.


        Parameters
        ----------

        targetname : str
            Name of the target to be queried.

        objtype : str, optional
            Type of the object to be queried. Available are: ``'asteroid'``,
            ``'comet'``, ``'dwarf planet'``, ``'planet'``, ``'satellite'``.
            Default: ``'asteroid'``

        epoch : `~astropy.time.Time` object, float, str,``None``, optional
            Start epoch of the query. If a float is provided, it is
            expected to be a Julian Date; if a str is provided, it is
            expected to be an iso date of the form
            ``'YYYY-MM-DD HH-MM-SS'``. If ``None`` is provided, the
            current date and time are used as epoch. Default: ``None``

        epoch_step : str, optional
            Step size for ephemerides calculation. Must consist of a decimal
            number followed by a single character: (d)ays, (h)ours,
            (m)inutes or (s)econds. Default: ``'1d'``

        epoch_nsteps : int, optional
            Number of increments of ``epoch_step`` starting from ``epoch``
            for which ephemerides are calculated. Maximum number of steps
            is 5000. Default: 1

        location : str, optional
            Location of the observer on Earth as a code or a set of
            coordinates. See the
            `Miriade manual <http://vo.imcce.fr/webservices/miriade/?documentation#field_7>`_
            for details. Default: geocentric location (``'500'``)

        coordtype : int, optional
            Type of coordinates to be calculated: ``1``: spherical, ``2``:
            rectangular, ``3``: local coordinates (azimuth and elevation),
            ``4``: hour angle coordinates, ``5``: dedicated to observation,
            ``6``: dedicated to AO observation. Default: ``1``

        timescale : str, optional
            The time scale used in the computation of the ephemerides:
            ``'UTC'`` or ``'TT'``. Default: ``'UTC'``

        planetary_theory : str, optional
            Planetary ephemerides set to be utilized in the calculations:
            ``'INPOP'``, ``'DE405'``, ``'DE406'``. Default: ``'INPOP'``

        ephtype : int, optional
            Type of ephemerides to be calculated: ``1``: astrometric J2000,
            ``2``: apparent of the date, ``3``: mean of the date,
            ``4``: mean J2000, Default: ``1``

        refplane : str, optional
            Reference plane: ``'equator'`` or ``'ecliptic'``. Default:
            ``'equator'``

        elements : str, optional
            Set of osculating elements to be used in the calculations:
            ``'ASTORB'`` or ``'MPCORB'``. Default: ``'ASTORB'``

        radial_velocity : bool, optional
            Calculate additional information on the target's radial velocity.
            Default: ``False``

        get_query_payload : bool, optional
            When set to ``True`` the method returns the HTTP request
            parameters as a dict, default: ``False``

        get_raw_response : bool, optional
            Return raw data as obtained by Miriade without parsing the
            data into a table, default: ``False``

        cache : bool, optional
            If ``True`` the query will be cached. Default: ``True``


        Notes
        -----

        The following parameters can be queried using this function. Note
        that different ``coordtype`` setting provide different sets of
        parameters; number in parentheses denote which ``coordtype``
        settings include the parameters.

        +------------------+-----------------------------------------------+
        | Column Name      | Definition                                    |
        +==================+===============================================+
        | ``target``       | Target name (str, 1, 2, 3, 4, 5, 6 )          |
        +------------------+-----------------------------------------------+
        | ``epoch``        | Ephemerides epoch (JD, float, 1, 2, 3, 4, 5,  |
        |                  | 6)                                            |
        +------------------+-----------------------------------------------+
        | ``RA``           | Target RA at ``ephtype`` (deg, float, 1)      |
        +------------------+-----------------------------------------------+
        | ``DEC``          | Target declination at ``ephtype`` (deg,       |
        |                  | float, 1, 4, 5)                               |
        +------------------+-----------------------------------------------+
        | ``RAJ2000``      | Target RA at J2000 (deg, float, 5, 6)         |
        +------------------+-----------------------------------------------+
        | ``DECJ2000``     | Target declination at J2000 (deg, float, 5, 6)|
        +------------------+-----------------------------------------------+
        | ``AZ``           | Target azimuth (deg, float, 3, 5)             |
        +------------------+-----------------------------------------------+
        | ``EL``           | Target elevation (deg, float, 3, 5)           |
        +------------------+-----------------------------------------------+
        | ``delta``        | Distance from observer (au, float, 1, 2, 3,   |
        |                  | 4, 5, 6)                                      |
        +------------------+-----------------------------------------------+
        | ``delta_rate``   | Rate in observer distance (km/s, float,       |
        |                  | 1, 5, 6)                                      |
        +------------------+-----------------------------------------------+
        | ``V``            | Apparent visual magnitude (mag, float, 1, 2,  |
        |                  | 3, 4, 5, 6)                                   |
        +------------------+-----------------------------------------------+
        | ``alpha``        | Solar phase angle (deg, 1, 2, 3, 4, 5, 6)     |
        +------------------+-----------------------------------------------+
        | ``elong``        | Solar elongation angle (deg, 1, 2, 3, 4, 5, 6)|
        +------------------+-----------------------------------------------+
        | ``RAcosD_rate``  | Rate of motion in RA * cos(DEC) (arcsec/min,  |
        |                  | float, 1, 5, 6)                               |
        +------------------+-----------------------------------------------+
        | ``DEC_rate``     | Rate of motion in DEC (arcsec/min, float, 1,  |
        |                  | 5, 6)                                         |
        +------------------+-----------------------------------------------+
        | ``x``            | X position state vector (au, float, 2)        |
        +------------------+-----------------------------------------------+
        | ``y``            | Y position state vector (au, float, 2)        |
        +------------------+-----------------------------------------------+
        | ``z``            | Z position state vector (au, float, 2)        |
        +------------------+-----------------------------------------------+
        | ``vx``           | X velocity state vector (au/d, float, 2)      |
        +------------------+-----------------------------------------------+
        | ``vy``           | Y velocity state vector (au/d, float, 2)      |
        +------------------+-----------------------------------------------+
        | ``vz``           | Z velocity state vector (au/d, float, 2)      |
        +------------------+-----------------------------------------------+
        | ``rv``           | Radial velocity (km/s, float, 2)              |
        +------------------+-----------------------------------------------+
        | ``heldist``      | Target heliocentric distance (au, float, 2,   |
        |                  | 5, 6)                                         |
        +------------------+-----------------------------------------------+
        | ``x_h``          | X heliocentric position vector (au, float, 2) |
        +------------------+-----------------------------------------------+
        | ``y_h``          | Y heliocentric position vector (au, float, 2) |
        +------------------+-----------------------------------------------+
        | ``z_h``          | Z heliocentric position vector (au, float, 2) |
        +------------------+-----------------------------------------------+
        | ``vx_h``         | X heliocentric vel. vector (au/d, float, 2)   |
        +------------------+-----------------------------------------------+
        | ``vy_h``         | Y heliocentric vel. vector (au/d, float, 2)   |
        +------------------+-----------------------------------------------+
        | ``vz_h``         | Z heliocentric vel. vector (au/d, float, 2)   |
        +------------------+-----------------------------------------------+
        | ``hourangle``    | Target hour angle (deg, float, 4, 5)          |
        +------------------+-----------------------------------------------+
        | ``siderealtime`` | Local sidereal time (hr, float, 5, 6)         |
        +------------------+-----------------------------------------------+
        | ``refraction``   | Atmospheric refraction (arcsec, float, 5, 6)  |
        +------------------+-----------------------------------------------+
        | ``airmass``      | Target airmass (float, 5, 6)                  |
        +------------------+-----------------------------------------------+
        | ``posunc``       | Positional uncertainty (arcsec, float, 5, 6)  |
        +------------------+-----------------------------------------------+


        Examples
        --------

        >>> from astroquery.imcce import Miriade
        >>> from astropy.time import Time
        >>> epoch = Time('2019-01-01', format='iso')
        >>> Miriade.get_ephemerides('3552', epoch=epoch)  # doctest: +SKIP
        <Table masked=True length=1>
           target          epoch                 RA         ...  DEC_rate   delta_rate
                             d                  deg         ... arcs / min    km / s
          bytes20         float64             float64       ...  float64     float64
        ----------- -------------------- ------------------ ... ---------- ------------
        Don Quixote            2458484.5 16.105294999999998 ...   -0.25244   31.4752734
        """

        URL = conf.ephemcc_server
        TIMEOUT = conf.timeout

        if isinstance(epoch, (int, float)):
            epoch = Time(epoch, format='jd')
        elif isinstance(epoch, str):
            epoch = Time(epoch, format='iso')
        elif epoch is None:
            epoch = Time.now()

        request_payload = OrderedDict([
            ('-name', targetname),
            ('-type', objtype[0].upper()+objtype[1:]),
            ('-ep', str(epoch.jd)),
            ('-step', epoch_step),
            ('-nbd', epoch_nsteps),
            ('-observer', location),
            ('-output', '--jul'),
            ('-tscale', timescale),
            ('-theory', planetary_theory),
            ('-teph', ephtype),
            ('-tcoor', coordtype),
            ('-rplane', {'equator': 1, 'ecliptic': 2}[refplane]),
            ('-oscelem', elements),
            ('-mime', 'votable')])

        if radial_velocity:
            request_payload['-output'] += ',--rv'

        if get_query_payload:
            return request_payload

        # query and parse
        response = self._request('GET', URL, params=request_payload,
                                 timeout=TIMEOUT, cache=cache)
        self._query_uri = response.url

        self._get_raw_response = get_raw_response

        return response

    def _parse_result(self, response, verbose=None):
        """
        Parser for Miriade request results
        """

        response_txt = response.text

        if self._get_raw_response:
            return response_txt

        # intercept error messages
        for line in response_txt.split('\n'):
            if 'name="QUERY_STATUS" value="ERROR"' in line:
                errmsg = line[line.find('ERROR:>')+9:
                              line.find('</vot:INFO>')]
                raise RuntimeError(errmsg)

        # convert votable to table
        commons.suppress_vo_warnings()
        voraw = BytesIO(response.content)
        votable = parse(voraw)
        data = votable.get_first_table().to_table()

        # modify table columns
        data['epoch'].unit = u.d

        if 'ra' in data.columns:
            data['ra'] = Angle(data['ra'], unit=u.hourangle).deg*u.deg
            data.rename_column('ra', 'RA')

        if 'dec' in data.columns:
            data['dec'] = Angle(data['dec'], unit=u.deg).deg*u.deg
            data.rename_column('dec', 'DEC')

        if 'raJ2000' in data.columns and 'decJ2000' in data.columns:
            data['raJ2000'] = Angle(
                data['raJ2000'], unit=u.hourangle).deg*u.deg
            data['decJ2000'] = Angle(data['decJ2000'], unit=u.deg).deg*u.deg
            data.rename_column('raJ2000', 'RAJ2000')
            data.rename_column('decJ2000', 'DECJ2000')

        if all([p in data.columns for p in ['xp', 'yp', 'zp']]):
            data.rename_column('xp', 'vx')
            data.rename_column('yp', 'vy')
            data.rename_column('zp', 'vz')
            if all([str(data[p].unit) == 'au/day'
                    for p in ['vx', 'vy', 'vz']]):
                data['vx'].unit = u.au/u.day
                data['vy'].unit = u.au/u.day
                data['vz'].unit = u.au/u.day

        if all([p in data.columns for p in ['xh', 'yh', 'zh']]):
            data.rename_column('xh', 'x_h')
            data.rename_column('yh', 'y_h')
            data.rename_column('zh', 'z_h')

        if all([p in data.columns for p in ['xhp', 'yhp', 'zhp']]):
            data.rename_column('xhp', 'vx_h')
            data.rename_column('yhp', 'vy_h')
            data.rename_column('zhp', 'vz_h')
            if all([str(data[p].unit) == 'au/day'
                    for p in ['vx_h', 'vy_h', 'vz_h']]):
                data['vx_h'].unit = u.au/u.day
                data['vy_h'].unit = u.au/u.day
                data['vz_h'].unit = u.au/u.day

        if 'distance' in data.columns:
            data.rename_column('distance', 'delta')

        if 'obsdistance' in data.columns:
            data.rename_column('obsdistance', 'delta')

        if 'heliodistance' in data.columns:
            data.rename_column('heliodistance', 'heldist')

        if 'azimut' in data.columns and 'elevation' in data.columns:
            data['azimut'] = Angle(data['azimut'], unit=u.deg).deg * u.deg
            data['elevation'] = Angle(
                data['elevation'], unit=u.deg).deg * u.deg
            data.rename_column('azimut', 'AZ')
            data.rename_column('elevation', 'EL')

        if 'mv' in data.columns:
            data.rename_column('mv', 'V')
            data['V'].unit = u.mag

        if 'phase' in data.columns:
            data.rename_column('phase', 'alpha')

        if 'elongation' in data.columns:
            data.rename_column('elongation', 'elong')

        if 'dracosdec' in data.columns:
            data.rename_column('dracosdec', 'RAcosD_rate')

        if 'ddec' in data.columns:
            data.rename_column('ddec', 'DEC_rate')

        if 'dist_dot' in data.columns:
            data.rename_column('dist_dot', 'delta_rate')

        if 'lst' in data.columns:
            data.rename_column('lst', 'siderealtime')

        if 'hourangle' in data.columns:
            data['hourangle'] = Angle(data['hourangle'],
                                      unit=u.hourangle).deg * u.deg

        if 'aeu' in data.columns:
            data.rename_column('aeu', 'posunc')

        return data


Miriade = MiriadeClass()


@async_to_sync
class SkybotClass(BaseQuery):
    """A class for querying the `IMCCE SkyBoT
    <http://vo.imcce.fr/webservices/skybot>`_ service.
    """
    _uri = None  # query uri
    _get_raw_response = False

    @property
    def uri(self):
        """
        URI used in query to service.

        Examples
        --------

        >>> from astroquery.imcce import Skybot
        >>> from astropy.coordinates import SkyCoord
        >>> import astropy.units as u
        >>> from astropy.time import Time
        >>> field = SkyCoord(1*u.deg, 1*u.deg)
        >>> epoch = Time('2019-05-29 21:42', format='iso')
        >>> skybot = Skybot()
        >>> obj = skybot.cone_search(field, 0.1*u.deg, epoch) # doctest: +SKIP
        >>> skybot.uri # doctest: +SKIP
        'http://vo.imcce.fr/webservices/skybot/skybotconesearch_query.php?-ra=1.0&-dec=1.0&-rd=0.1&-ep=2458633.404166667&-loc=500&-filter=120.0&-objFilter=111&-refsys=EQJ2000&-output=all&-mime=text'
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
        rad : `~astropy.units.Quantity` object or float
            Radius of the search cone. If no units are provided (input as
            float), degrees are assumed. The maximum search radius is 10
            degrees; if this
            maximum radius is exceeded, it will be clipped and a warning
            will be provided to the user.
        epoch : `~astropy.time.Time` object, float, or string
            Epoch of search process in UT. If provided as float, it is
            interpreted as Julian Date, if provided as string, it is
            interpreted as date in the form ``'YYYY-MM-DD HH-MM-SS'``.
        location : int or str, optional
            Location of the observer on Earth as defined in the official
            `list of IAU codes
            <https://www.minorplanetcenter.net/iau/lists/ObsCodes.html>`_.
            Default: geocentric location (``'500'``)
        position_error : `~astropy.units.Quantity` or float, optional
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
        >>> from astroquery.imcce import Skybot
        >>> from astropy.coordinates import SkyCoord
        >>> from astropy.time import Time
        >>> import astropy.units as u
        >>> field = SkyCoord(1*u.deg, 1*u.deg)
        >>> epoch = Time('2019-05-29 21:42', format='iso')
        >>> Skybot.cone_search(field, 0.1*u.deg, epoch)  # doctest: +SKIP
        <QTable length=2>
        Number    Name           RA         ...      vy          vz       epoch
                                deg         ...    AU / d      AU / d       d
        int64     str9        float64       ...   float64     float64    float64
        ------ --------- ------------------ ... ----------- ----------- ---------
        180969 2005 MM39 1.0019566666666666 ...  0.00977568 0.003022634 2458630.0
        107804 2001 FV58 1.0765258333333332 ... 0.006551369 0.003846177 2458630.0
        """

        URL = conf.skybot_server
        TIMEOUT = conf.timeout

        # check for types and units
        if not isinstance(coo, SkyCoord):
            coo = SkyCoord(ra=coo[0]*u.degree,
                           dec=coo[1]*u.degree, frame='icrs')
        if isinstance(rad, u.Quantity):
            rad = Angle(rad.value, unit=rad.unit)
        if not isinstance(rad, u.Quantity):
            rad = Angle(rad, unit=u.degree)
        if rad > Angle(10, unit=u.degree):
            rad = Angle(10, unit=u.degree)
            warnings.warn('search cone radius set to maximum: 10 deg',
                          UserWarning)
        if isinstance(epoch, (int, float)):
            epoch = Time(epoch, format='jd')
        elif isinstance(epoch, str):
            epoch = Time(epoch, format='iso')
        if isinstance(position_error, u.Quantity):
            position_error = Angle(position_error.value,
                                   unit=position_error.unit)
        if not isinstance(position_error, u.Quantity):
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

        self._get_raw_response = get_raw_response

        response = self._request(method='GET', url=URL,
                                 params=request_payload,
                                 timeout=TIMEOUT, cache=cache)

        self._uri = response.url

        return response

    def _parse_result(self, response, verbose=False):
        """
        internal wrapper to parse queries
        """

        if self._get_raw_response:
            return response.text

        # intercept error messages
        response_txt = response.text.split('\n')[2:-1]
        if len(response_txt) < 3 and len(response_txt[-1].split('|')) < 21:
            raise RuntimeError(response_txt[-1])

        names = response_txt[0].replace('# ', '').strip().split(' | ')
        results = ascii.read(response_txt[1:], delimiter='|',
                             names=names, fast_reader=False)
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
        # unnumbered asteroids return as non numeric values ('-')
        # this is treated as defaulting to 0, and masking the entry
        unnumbered_mask = [not str(x).isdigit() for x in results['Number']]
        numbers = [int(x) if str(x).isdigit()
                   else 0
                   for x in results['Number']]
        asteroid_number_col = MaskedColumn(numbers, name='Number',
                                           mask=unnumbered_mask)

        results.replace_column('Number', asteroid_number_col)

        return results


Skybot = SkybotClass()
