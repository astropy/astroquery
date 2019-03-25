# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

# 1. standard library imports
from numpy import nan as nan
from numpy import isnan
from numpy import ndarray
from collections import OrderedDict
import warnings

# 2. third party imports
from astropy.table import Table, Column
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

__all__ = ['Horizons', 'HorizonsClass']


@async_to_sync
class HorizonsClass(BaseQuery):
    """
    A class for querying the
    `JPL Horizons <https://ssd.jpl.nasa.gov/horizons.cgi>`_ service.
    """

    TIMEOUT = conf.timeout

    def __init__(self, id=None, location=None, epochs=None,
                 id_type='smallbody'):
        """Instantiate JPL query.

        Parameters
        ----------
        id : str, required
            Name, number, or designation of the object to be queried
        location : str or dict, optional
            Observer's location for ephemerides queries or center body
            name for orbital element or vector queries. Uses the same
            codes as JPL Horizons. If no location is provided, Earth's
            center is used for ephemerides queries and the Sun's
            center for elements and vectors queries. Arbitrary topocentic
            coordinates for ephemerides queries can be provided in the
            format of a dictionary. The
            dictionary has to be of the form {``'lon'``: longitude in
            deg (East positive, West negative), ``'lat'``: latitude in
            deg (North positive, South negative), ``'elevation'``:
            elevation in km above the reference ellipsoid, [``'body'``:
            Horizons body ID of the central body; optional; if this value
            is not provided it is assumed that this location is on Earth]}.
        epochs : scalar, list-like, or dictionary, optional
            Either a list of epochs in JD or MJD format or a dictionary
            defining a range of times and dates; the range dictionary has to
            be of the form {``'start'``:'YYYY-MM-DD [HH:MM:SS]',
            ``'stop'``:'YYYY-MM-DD [HH:MM:SS]', ``'step'``:'n[y|d|m|s]'}.
            If no epochs are provided, the current time is used.
        id_type : str, optional
            Identifier type, options:
            ``'smallbody'``, ``'majorbody'`` (planets but also
            anything that is not a small body), ``'designation'``,
            ``'name'``, ``'asteroid_name'``, ``'comet_name'``,
            ``'id'`` (Horizons id number), or ``'smallbody'`` (find the
            closest match under any id_type), default: ``'smallbody'``


        Examples
        --------
            >>> from astroquery.jplhorizons import Horizons
            >>> eros = Horizons(id='433', location='568',
            ...              epochs={'start':'2017-01-01',
            ...                      'stop':'2017-02-01',
            ...                      'step':'1d'})
            >>> print(eros) # doctest: +SKIP
            JPLHorizons instance "433"; location=568, epochs={'start': '2017-01-01', 'step': '1d', 'stop': '2017-02-01'}, id_type=smallbody
        """
        super(HorizonsClass, self).__init__()
        self.id = id
        self.location = location

        # check for epochs to be dict or list-like; else: make it a list
        if epochs is not None:
            if isinstance(epochs, (list, tuple, ndarray)):
                pass
            elif isinstance(epochs, dict):
                if not ('start' in epochs and
                        'stop' in epochs and
                        'step' in epochs):
                    raise ValueError('time range ({:s}) requires start, stop, '
                                     'and step'.format(str(epochs)))
            else:
                # turn scalars into list
                epochs = [epochs]
        self.epochs = epochs

        # check for id_type
        if id_type not in ['smallbody', 'majorbody',
                           'designation', 'name',
                           'asteroid_name', 'comet_name', 'id']:
            raise ValueError('id_type ({:s}) not allowed'.format(id_type))
        self.id_type = id_type

        # return raw response?
        self.return_raw = False

        self.query_type = None  # ['ephemerides', 'elements', 'vectors']

        self.uri = None  # will contain query URL

    def __str__(self):
        """
        String representation of HorizonsClass object instance'


        Examples
        --------
            >>> from astroquery.jplhorizons import Horizons
            >>> eros = Horizons(id='433', location='568',
            ...                 epochs={'start':'2017-01-01',
            ...                         'stop':'2017-02-01',
            ...                         'step':'1d'})
            >>> print(eros) # doctest: +SKIP
            JPLHorizons instance "433"; location=568, epochs={'start': '2017-01-01', 'step': '1d', 'stop': '2017-02-01'}, id_type=smallbody
        """
        return ('JPLHorizons instance \"{:s}\"; location={:s}, '
                'epochs={:s}, id_type={:s}').format(
                    str(self.id),
                    str(self.location),
                    str(self.epochs),
                    str(self.id_type))

    # ---------------------------------- query functions

    def ephemerides_async(self, airmass_lessthan=99,
                          solar_elongation=(0, 180), max_hour_angle=0,
                          rate_cutoff=None,
                          skip_daylight=False,
                          refraction=False,
                          refsystem='J2000',
                          closest_apparition=False, no_fragments=False,
                          quantities=conf.eph_quantities,
                          get_query_payload=False,
                          get_raw_response=False, cache=True):
        """
        Query JPL Horizons for ephemerides. The ``location`` parameter
        in ``HorizonsClass`` refers in this case to the location of
        the observer.

        The following tables list the values queried, their
        definitions, data types, units, and original Horizons
        designations (where available). For more information on the
        definitions of these quantities, please refer to the `Horizons
        User Manual <https://ssd.jpl.nasa.gov/?horizons_doc>`_.



        +------------------+-----------------------------------------------+
        | Column Name      | Definition                                    |
        +==================+===============================================+
        | targetname       | official number, name, designation (string)   |
        +------------------+-----------------------------------------------+
        | H                | absolute magnitude in V band (float, mag)     |
        +------------------+-----------------------------------------------+
        | G                | photometric slope parameter (float)           |
        +------------------+-----------------------------------------------+
        | M1               | comet total abs mag (float, mag, ``M1``)      |
        +------------------+-----------------------------------------------+
        | M2               | comet nuclear abs mag (float, mag, ``M2``)    |
        +------------------+-----------------------------------------------+
        | k1               | total mag scaling factor (float, ``k1``)      |
        +------------------+-----------------------------------------------+
        | k2               | nuclear mag scaling factor (float, ``k2``)    |
        +------------------+-----------------------------------------------+
        | phasecoeff       | comet phase coeff (float, mag/deg, ``PHCOFF``)|
        +------------------+-----------------------------------------------+
        | datetime         | epoch (str, ``Date__(UT)__HR:MN:SC.fff``)     |
        +------------------+-----------------------------------------------+
        | datetime_jd      | epoch Julian Date (float,                     |
        |                  | ``Date_________JDUT``)                        |
        +------------------+-----------------------------------------------+
        | solar_presence   | information on Sun's presence (str)           |
        +------------------+-----------------------------------------------+
        | flags            | information on Moon, target status (str)      |
        +------------------+-----------------------------------------------+
        | RA               | target RA (float, deg, ``DEC_(XXX)``)         |
        +------------------+-----------------------------------------------+
        | DEC              | target DEC (float, deg, ``DEC_(XXX)``)        |
        +------------------+-----------------------------------------------+
        | RA_app           | target apparent RA (float, deg,               |
        |                  | ``R.A._(a-app)``)                             |
        +------------------+-----------------------------------------------+
        | DEC_app          | target apparent DEC (float, deg,              |
        |                  | ``DEC_(a-app)``)                              |
        +------------------+-----------------------------------------------+
        | RA_rate          | target rate RA (float, arcsec/hr, ``RA*cosD``)|
        +------------------+-----------------------------------------------+
        | DEC_rate         | target RA (float, arcsec/hr, ``d(DEC)/dt``)   |
        +------------------+-----------------------------------------------+
        | AZ               | Azimuth (float, deg, EoN, ``Azi_(a-app)``)    |
        +------------------+-----------------------------------------------+
        | EL               | Elevation (float, deg, ``Elev_(a-app)``)      |
        +------------------+-----------------------------------------------+
        | AZ_rate          | Azimuth rate (float, arcsec/minute,           |
        |                  | ``dAZ*cosE``)                                 |
        +------------------+-----------------------------------------------+
        | EL_rate          | Elevation rate (float, arcsec/minute,         |
        |                  | ``d(ELV)/dt``)                                |
        +------------------+-----------------------------------------------+
        | sat_X            | satellite X position (arcsec,                 |
        |                  | ``X_(sat-prim)``)                             |
        +------------------+-----------------------------------------------+
        | sat_Y            | satellite Y position (arcsec,                 |
        |                  | ``Y_(sat-prim)``)                             |
        +------------------+-----------------------------------------------+
        | sat_PANG         | satellite position angle (deg,                |
        |                  | ``SatPANG``)                                  |
        +------------------+-----------------------------------------------+
        | siderealtime     | local apparent sidereal time (str,            |
        |                  | ``L_Ap_Sid_Time``)                            |
        +------------------+-----------------------------------------------+
        | airmass          | target optical airmass (float, ``a-mass``)    |
        +------------------+-----------------------------------------------+
        | magextinct       | V-mag extinction (float, mag, ``mag_ex``)     |
        +------------------+-----------------------------------------------+
        | V                | V magnitude (float, mag, ``APmag``)           |
        +------------------+-----------------------------------------------+
        | Tmag             | comet Total magnitude (float, mag, ``T-mag``) |
        +------------------+-----------------------------------------------+
        | Nmag             | comet Nucleaus magnitude (float, mag,         |
        |                  | ``N-mag``)                                    |
        +------------------+-----------------------------------------------+
        | surfbright       | surf brightness (float, mag/arcsec^2,         |
        |                  | ``S-brt``)                                    |
        +------------------+-----------------------------------------------+
        | illumination     | frac of illumination (float, percent,         |
        |                  | ``Illu%``)                                    |
        +------------------+-----------------------------------------------+
        | illum_defect     | Defect of illumination (float, arcsec,        |
        |                  | ``Dec_illu``)                                 |
        +------------------+-----------------------------------------------+
        | sat_sep          | Target-primary angular separation (float,     |
        |                  | arcsec, ``ang-sep``)                          |
        +------------------+-----------------------------------------------+
        | sat_vis          | Target-primary visibility (str, ``v``)        |
        +------------------+-----------------------------------------------+
        | ang_width        | Angular width of target (float, arcsec,       |
        |                  | ``Ang-diam``)                                 |
        +------------------+-----------------------------------------------+
        | PDObsLon         | Apparent planetodetic longitude (float, deg,  |
        |                  | ``Ob-lon``)                                   |
        +------------------+-----------------------------------------------+
        | PDObsLat         | Apparent planetodetic latitude  (float, deg,  |
        |                  | ``Ob-lat``)                                   |
        +------------------+-----------------------------------------------+
        | PDSunLon         | Apparent planetodetic longitude of the Sun    |
        |                  | (float, deg, ``Sl-lon``)                      |
        +------------------+-----------------------------------------------+
        | PDSunLat         | Apparent planetodetic latitude of the Sun     |
        |                  | (float, deg, ``Sl-lat``)                      |
        +------------------+-----------------------------------------------+
        | SubSol_ang       | Target sub-solar point position angle         |
        |                  | (float, deg, ``SN.ang``)                      |
        +------------------+-----------------------------------------------+
        | SubSol_dist      | Target sub-solar point position angle distance|
        |                  | (float, arcsec, ``SN.dist``)                  |
        +------------------+-----------------------------------------------+
        | NPole_ang        | Target's North Pole position angle            |
        |                  | (float, deg, ``NP.ang``)                      |
        +------------------+-----------------------------------------------+
        | NPole_dist       | Target's North Pole position angle distance   |
        |                  | (float, arcsec, ``NP.dist``)                  |
        +------------------+-----------------------------------------------+
        | EclLon           | heliocentr ecl long (float, deg, ``hEcl-Lon``)|
        +------------------+-----------------------------------------------+
        | EclLat           | heliocentr ecl lat (float, deg, ``hEcl-Lat``) |
        +------------------+-----------------------------------------------+
        | ObsEclLon        | obscentr ecl long (float, deg, ``ObsEcLon``)  |
        +------------------+-----------------------------------------------+
        | ObsEclLat        | obscentr ecl lat (float, deg, ``ObsEcLat``)   |
        +------------------+-----------------------------------------------+
        | r                | heliocentric distance (float, au, ``r``)      |
        +------------------+-----------------------------------------------+
        | r_rate           | heliocentric radial rate (float, km/s,        |
        |                  | ``rdot``)                                     |
        +------------------+-----------------------------------------------+
        | delta            | distance from observer (float, au, ``delta``) |
        +------------------+-----------------------------------------------+
        | delta_rate       | obs-centric rad rate (float, km/s, ``deldot``)|
        +------------------+-----------------------------------------------+
        | lighttime        | one-way light time (float, min, ``1-way_LT``) |
        +------------------+-----------------------------------------------+
        | vel_sun          | Target center velocity wrt Sun                |
        |                  | (float, km/s, ``VmagSn``)                     |
        +------------------+-----------------------------------------------+
        | vel_obs          | Target center velocity wrt Observer           |
        |                  | (float, km/s, ``VmagOb``)                     |
        +------------------+-----------------------------------------------+
        | elong            | solar elongation (float, deg, ``S-O-T``)      |
        +------------------+-----------------------------------------------+
        | elongFlag        | app. position relative to Sun (str, ``/r``)   |
        +------------------+-----------------------------------------------+
        | alpha            | solar phase angle (float, deg, ``S-T-O``)     |
        +------------------+-----------------------------------------------+
        | lunar_elong      | Apparent lunar elongation angle wrt target    |
        |                  | (float, deg, ``T-O-M``)                       |
        +------------------+-----------------------------------------------+
        | lunar_illum      | Lunar illumination percentage                 |
        |                  | (float, percent, ``MN_Illu%``)                |
        +------------------+-----------------------------------------------+
        | IB_elong         | Apparent interfering body elongation angle    |
        |                  | wrt target (float, deg, ``T-O-I``)            |
        +------------------+-----------------------------------------------+
        | IB_illum         | Interfering body illumination percentage      |
        |                  | (float, percent, ``IB_Illu%``)                |
        +------------------+-----------------------------------------------+
        | sat_alpha        | Observer-Primary-Target angle                 |
        |                  | (float, deg, ``O-P-T``)                       |
        +------------------+-----------------------------------------------+
        | OrbPlaneAng      | orbital plane angle (float, deg, ``PlAng``)   |
        +------------------+-----------------------------------------------+
        | sunTargetPA      | -Sun vector PA (float, deg, EoN, ``PsAng``)   |
        +------------------+-----------------------------------------------+
        | velocityPA       | -velocity vector PA (float, deg, EoN,         |
        |                  | ``PsAMV``)                                    |
        +------------------+-----------------------------------------------+
        | constellation    | constellation ID containing target (str,      |
        |                  | ``Cnst``)                                     |
        +------------------+-----------------------------------------------+
        | TDB-UT           | difference between TDB and UT (float,         |
        |                  | seconds, ``TDB-UT``)                          |
        +------------------+-----------------------------------------------+
        | NPole_RA         | Target's North Pole RA (float, deg,           |
        |                  | ``N.Pole-RA``)                                |
        +------------------+-----------------------------------------------+
        | NPole_DEC        | Target's North Pole DEC (float, deg,          |
        |                  | ``N.Pole-DC``)                                |
        +------------------+-----------------------------------------------+
        | GlxLon           | galactic longitude (float, deg, ``GlxLon``)   |
        +------------------+-----------------------------------------------+
        | GlxLat           | galactic latitude  (float, deg, ``GlxLat``)   |
        +------------------+-----------------------------------------------+
        | solartime        | local apparent solar time (string,            |
        |                  | ``L_Ap_SOL_Time``)                            |
        +------------------+-----------------------------------------------+
        | earth_lighttime  | observer lighttime from center of Earth       |
        |                  | (float, minutes, ``399_ins_LT``               |
        +------------------+-----------------------------------------------+
        | RA_3sigma        | 3 sigma positional uncertainty in RA (float,  |
        |                  | arcsec, ``RA_3sigma``)                        |
        +------------------+-----------------------------------------------+
        | DEC_3sigma       | 3 sigma positional uncertainty in  DEC (float,|
        |                  | arcsec, ``DEC_3sigma``)                       |
        +------------------+-----------------------------------------------+
        | SMAA_3sigma      | 3sig pos unc error ellipse semi-major axis    |
        |                  | (float, arcsec, ``SMAA_3sig``)                |
        +------------------+-----------------------------------------------+
        | SMIA_3sigma      | 3sig pos unc error ellipse semi-minor axis    |
        |                  | (float, arcsec, ``SMIA_3sig``)                |
        +------------------+-----------------------------------------------+
        | Theta_3sigma     | pos unc error ellipse position angle          |
        |                  | (float, deg, ``Theta``)                       |
        +------------------+-----------------------------------------------+
        | Area_3sigma      | 3sig pos unc error ellipse are                |
        |                  | (float, arcsec^2, ``Area_3sig``)              |
        +------------------+-----------------------------------------------+
        | RSS_3sigma       | 3sig pos unc error ellipse root-sum-square    |
        |                  | (float, arcsec, ``POS_3sigma``)               |
        +------------------+-----------------------------------------------+
        | r_3sigma         | 3sig range uncertainty                        |
        |                  | (float, km, ``RNG_3sigma``)                   |
        +------------------+-----------------------------------------------+
        | r_rate_3sigma    | 3sig range rate uncertainty                   |
        |                  | (float, km/second, ``RNGRT_3sigma``)          |
        +------------------+-----------------------------------------------+
        | SBand_3sigma     | 3sig Doppler radar uncertainties at S-band    |
        |                  | (float, Hertz, ``DOP_S_3sig``)                |
        +------------------+-----------------------------------------------+
        | XBand_3sigma     | 3sig Doppler radar uncertainties at X-band    |
        |                  | (float, Hertz, ``DOP_X_3sig``)                |
        +------------------+-----------------------------------------------+
        | DoppDelay_3sigma | 3sig Doppler radar round-trip delay           |
        |                  | unc (float, second, ``RT_delay_3sig``)        |
        +------------------+-----------------------------------------------+
        | true_anom        | True Anomaly (float, deg, ``Tru_Anom``)       |
        +------------------+-----------------------------------------------+
        | hour_angle       | local apparent hour angle (string,            |
        |                  | sexagesimal angular hours, ``L_Ap_Hour_Ang``) |
        +------------------+-----------------------------------------------+
        | alpha_true       | true phase angle (float, deg, ``phi``)        |
        +------------------+-----------------------------------------------+
        | PABLon           | phase angle bisector longitude                |
        |                  | (float, deg, ``PAB-LON``)                     |
        +------------------+-----------------------------------------------+
        | PABLat           | phase angle bisector latitude                 |
        |                  | (float, deg, ``PAB-LAT``)                     |
        +------------------+-----------------------------------------------+


        Parameters
        ----------
        airmass_lessthan : float, optional
            Defines a maximum airmass for the query, default: 99
        solar_elongation : tuple, optional
            Permissible solar elongation range: (minimum, maximum); default:
            (0,180)
        max_hour_angle : float, optional
            Defines a maximum hour angle for the query, default: 0
        rate_cutoff : float, optional
            Angular range rate upper limit cutoff in arcsec/h; default:
            disabled
        skip_daylight : boolean, optional
            Crop daylight epochs in query, default: False
        refraction : boolean
            If `True`, coordinates account for a standard atmosphere
            refraction model; if `False`, coordinates do not account for
            refraction (airless model); default: `False`
        refsystem : string
            Coordinate reference system: ``'J2000'`` or ``'B1950'``;
            default: ``'J2000'``
        closest_apparition : boolean, optional
            Only applies to comets. This option will choose the
            closest apparition available in time to the selected
            epoch; default: False. Do not use this option for
            non-cometary objects.
        no_fragments : boolean, optional
            Only applies to comets. Reject all comet fragments from
            selection; default: False. Do not use this option for
            non-cometary objects.
        quantities : integer or string, optional
            single integer or comma-separated list in the form of a string
            corresponding to all the
            quantities to be queried from JPL Horizons using the coding
            according to the `JPL Horizons User Manual Definition of
            Observer Table Quantities
            <https://ssd.jpl.nasa.gov/?horizons_doc#table_quantities>`_;
            default: all quantities
        get_query_payload : boolean, optional
            When set to `True` the method returns the HTTP request
            parameters as a dict, default: False
        get_raw_response : boolean, optional
            Return raw data as obtained by JPL Horizons without parsing the
            data into a table, default: False


        Returns
        -------
        response : `requests.Response`
            The response of the HTTP request.


        Examples
        --------
            >>> from astroquery.jplhorizons import Horizons
            >>> obj = Horizons(id='Ceres', location='568',
            ...             epochs={'start':'2010-01-01',
            ...                     'stop':'2010-03-01',
            ...                     'step':'10d'})
            >>> eph = obj.ephemerides() # doctest: +SKIP
            >>> print(eph) # doctest: +SKIP
            targetname    datetime_str   datetime_jd ...   GlxLat  RA_3sigma
            DEC_3sigma
               ---            ---             d      ...    deg      arcsec
            arcsec
            ---------- ----------------- ----------- ... --------- ---------
            ----------
               1 Ceres 2010-Jan-01 00:00   2455197.5 ... 24.120057       0.0
            0.0
               1 Ceres 2010-Jan-11 00:00   2455207.5 ... 20.621496       0.0
            0.0
               1 Ceres 2010-Jan-21 00:00   2455217.5 ... 17.229529       0.0
            0.0
               1 Ceres 2010-Jan-31 00:00   2455227.5 ...  13.97264       0.0
            0.0
               1 Ceres 2010-Feb-10 00:00   2455237.5 ... 10.877201       0.0
            0.0
               1 Ceres 2010-Feb-20 00:00   2455247.5 ...  7.976737       0.0
            0.0

        """

        URL = conf.horizons_server

        # check for required information
        if self.id is None:
            raise ValueError("'id' parameter not set. Query aborted.")
        if self.location is None:
            self.location = '500@399'
        if self.epochs is None:
            self.epochs = Time.now().jd

        # assemble commandline based on self.id_type
        commandline = str(self.id)
        if self.id_type in ['designation', 'name',
                            'asteroid_name', 'comet_name']:
            commandline = ({'designation': 'DES=',
                            'name': 'NAME=',
                            'asteroid_name': 'ASTNAM=',
                            'comet_name': 'COMNAM='}[self.id_type] +
                           commandline)
        if self.id_type in ['smallbody', 'asteroid_name',
                            'comet_name', 'designation']:
            commandline += ';'
            if isinstance(closest_apparition, bool):
                if closest_apparition:
                    commandline += ' CAP;'
            else:
                commandline += ' CAP{:s};'.format(closest_apparition)
            if no_fragments:
                commandline += ' NOFRAG;'

        request_payload = OrderedDict([
            ('batch', 1),
            ('TABLE_TYPE', 'OBSERVER'),
            ('QUANTITIES', "'"+str(quantities)+"'"),
            ('COMMAND', '"' + commandline + '"'),
            ('SOLAR_ELONG', ('"' + str(solar_elongation[0]) + "," +
                             str(solar_elongation[1]) + '"')),
            ('LHA_CUTOFF', (str(max_hour_angle))),
            ('CSV_FORMAT', ('YES')),
            ('CAL_FORMAT', ('BOTH')),
            ('ANG_FORMAT', ('DEG')),
            ('APPARENT', ({False: 'AIRLESS',
                           True: 'REFRACTED'}[refraction])),
            ('REF_SYSTEM', (refsystem))])

        if isinstance(self.location, dict):
            if ('lon' not in self.location or 'lat' not in self.location or
                    'elevation' not in self.location):
                raise ValueError(("'location' must contain lon, lat, "
                                  "elevation"))

            if 'body' not in self.location:
                self.location['body'] = '399'
            request_payload['CENTER'] = 'coord@{:s}'.format(
                str(self.location['body']))
            request_payload['COORD_TYPE'] = 'GEODETIC'
            request_payload['SITE_COORD'] = "'{:f},{:f},{:f}'".format(
                self.location['lon'], self.location['lat'],
                self.location['elevation'])
        else:
            request_payload['CENTER'] = "'" + str(self.location) + "'"

        if rate_cutoff is not None:
            request_payload['ANG_RATE_CUTOFF'] = (str(rate_cutoff))

        # parse self.epochs
        if isinstance(self.epochs, (list, tuple, ndarray)):
            request_payload['TLIST'] = "\n".join([str(epoch) for epoch in
                                                  self.epochs])
        elif isinstance(self.epochs, dict):
            if ('start' not in self.epochs or 'stop' not in self.epochs or
                    'step' not in self.epochs):
                raise ValueError("'epochs' must contain start, " +
                                 "stop, step")
            request_payload['START_TIME'] = '"'+self.epochs['start']+'"'
            request_payload['STOP_TIME'] = '"'+self.epochs['stop']+'"'
            request_payload['STEP_SIZE'] = '"'+self.epochs['step']+'"'
        else:
            # treat epochs as scalar
            request_payload['TLIST'] = str(self.epochs)

        if airmass_lessthan < 99:
            request_payload['AIRMASS'] = str(airmass_lessthan)

        if skip_daylight:
            request_payload['SKIP_DAYLT'] = 'YES'
        else:
            request_payload['SKIP_DAYLT'] = 'NO'

        self.query_type = 'ephemerides'

        # return request_payload if desired
        if get_query_payload:
            return request_payload

        # set return_raw flag, if raw response desired
        if get_raw_response:
            self.return_raw = True

        # query and parse
        response = self._request('GET', URL, params=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        self.uri = response.url

        # check length of uri
        if len(self.uri) >= 2000:
            warnings.warn(('The URI used in this query is very long '
                           'and might have been truncated. The results of '
                           'the query might be compromised. If you queried '
                           'a list of epochs, consider querying a range.'))

        return response

    def elements_async(self, get_query_payload=False,
                       refsystem='J2000',
                       refplane='ecliptic',
                       tp_type='absolute',
                       closest_apparition=False, no_fragments=False,
                       get_raw_response=False, cache=True):
        """
        Query JPL Horizons for osculating orbital elements. The ``location``
        parameter in ``HorizonsClass`` refers in this case to the  center
        body relative to which the elements are provided.

        The following table lists the values queried, their
        definitions, data types, units, and original Horizons
        designations (where available). For more information on the
        definitions of these quantities, please refer to the `Horizons
        User Manual <https://ssd.jpl.nasa.gov/?horizons_doc>`_.

        +------------------+-----------------------------------------------+
        | Column Name      | Definition                                    |
        +==================+===============================================+
        | targetname       | official number, name, designation (string)   |
        +------------------+-----------------------------------------------+
        | H                | absolute magnitude in V band (float, mag)     |
        +------------------+-----------------------------------------------+
        | G                | photometric slope parameter (float)           |
        +------------------+-----------------------------------------------+
        | M1               | comet total abs mag (float, mag, ``M1``)      |
        +------------------+-----------------------------------------------+
        | M2               | comet nuclear abs mag (float, mag, ``M2``)    |
        +------------------+-----------------------------------------------+
        | k1               | total mag scaling factor (float, ``k1``)      |
        +------------------+-----------------------------------------------+
        | k2               | nuclear mag scaling factor (float, ``k2``)    |
        +------------------+-----------------------------------------------+
        | phasecoeff       | comet phase coeff (float, mag/deg, ``PHCOFF``)|
        +------------------+-----------------------------------------------+
        | datetime_str     | epoch Date (str, ``Calendar Date (TDB)``)     |
        +------------------+-----------------------------------------------+
        | datetime_jd      | epoch Julian Date (float, ``JDTDB``)          |
        +------------------+-----------------------------------------------+
        | e                | eccentricity (float, ``EC``)                  |
        +------------------+-----------------------------------------------+
        | q                | periapsis distance (float, au, ``QR``)        |
        +------------------+-----------------------------------------------+
        | a                | semi-major axis (float, au, ``A``)            |
        +------------------+-----------------------------------------------+
        | incl             | inclination (float, deg, ``IN``)              |
        +------------------+-----------------------------------------------+
        | Omega            | longitude of Asc. Node (float, deg, ``OM``)   |
        +------------------+-----------------------------------------------+
        | w                | argument of the perifocus (float, deg, ``W``) |
        +------------------+-----------------------------------------------+
        | Tp_jd            | time of periapsis (float, Julian Date, ``Tp``)|
        +------------------+-----------------------------------------------+
        | n                | mean motion (float, deg/d, ``N``)             |
        +------------------+-----------------------------------------------+
        | M                | mean anomaly (float, deg, ``MA``)             |
        +------------------+-----------------------------------------------+
        | nu               | true anomaly (float, deg, ``TA``)             |
        +------------------+-----------------------------------------------+
        | period           | orbital period (float, (Earth) d, ``PR``)     |
        +------------------+-----------------------------------------------+
        | Q                | apoapsis distance (float, au, ``AD``)         |
        +------------------+-----------------------------------------------+


        Parameters
        ----------
        refsystem : string
            Element reference system for geometric and astrometric
            quantities: ``'J2000'`` or ``'B1950'``; default: ``'J2000'``
        refplane : string
            Reference plane for all output quantities: ``'ecliptic'``
            (ecliptic and mean equinox of reference epoch), ``'earth'``
            (Earth mean equator and equinox of reference epoch), or
            ``'body'`` (body mean equator and node of date); default:
            ``'ecliptic'``
        tp_type : string
            Representation for time-of-perihelion passage: ``'absolute'`` or
            ``'relative'`` (to epoch); default: ``'absolute'``
        closest_apparition : boolean, optional
            Only applies to comets. This option will choose the
            closest apparition available in time to the selected
            epoch; default: False. Do not use this option for
            non-cometary objects.
        no_fragments : boolean, optional
            Only applies to comets. Reject all comet fragments from
            selection; default: False. Do not use this option for
            non-cometary objects.
        get_query_payload : boolean, optional
            When set to ``True`` the method returns the HTTP request
            parameters as a dict, default: False
        get_raw_response: boolean, optional
            Return raw data as obtained by JPL Horizons without parsing the
            data into a table, default: False


        Returns
        -------
        response : `requests.Response`
            The response of the HTTP request.


        Examples
        --------
            >>> from astroquery.jplhorizons import Horizons
            >>> obj = Horizons(id='433', location='500@10',
            ...                epochs=2458133.33546)
            >>> el = obj.elements() # doctest: +SKIP
            >>> print(el) # doctest: +SKIP
                targetname      datetime_jd  ...       Q            P
                   ---               d       ...       AU           d
            ------------------ ------------- ... ------------- ------------
            433 Eros (1898 DQ) 2458133.33546 ... 1.78244263804 642.93873484
        """

        URL = conf.horizons_server

        # check for required information
        if self.id is None:
            raise ValueError("'id' parameter not set. Query aborted.")
        if self.location is None:
            self.location = '500@10'
        if self.epochs is None:
            self.epochs = Time.now().jd

        # assemble commandline based on self.id_type
        commandline = str(self.id)
        if self.id_type in ['designation', 'name',
                            'asteroid_name', 'comet_name']:
            commandline = ({'designation': 'DES=',
                            'name': 'NAME=',
                            'asteroid_name': 'ASTNAM=',
                            'comet_name': 'COMNAM='}[self.id_type] +
                           commandline)
        if self.id_type in ['smallbody', 'asteroid_name',
                            'comet_name', 'designation']:
            commandline += ';'
            if isinstance(closest_apparition, bool):
                if closest_apparition:
                    commandline += ' CAP;'
            else:
                commandline += ' CAP{:s};'.format(closest_apparition)
            if no_fragments:
                commandline += ' NOFRAG;'

        if isinstance(self.location, dict):
            raise ValueError(('cannot use topographic position in orbital'
                              'elements query'))

        # configure request_payload for ephemerides query
        request_payload = OrderedDict([
            ('batch', 1),
            ('TABLE_TYPE', 'ELEMENTS'),
            ('MAKE_EPHEM', 'YES'),
            ('OUT_UNITS', 'AU-D'),
            ('COMMAND', '"' + commandline + '"'),
            ('CENTER', ("'" + str(self.location) + "'")),
            ('CSV_FORMAT', 'YES'),
            ('ELEM_LABELS', 'YES'),
            ('OBJ_DATA', 'YES'),
            ('REF_SYSTEM', refsystem),
            ('REF_PLANE', {'ecliptic': 'ECLIPTIC', 'earth': 'FRAME',
                           'body': "'BODY EQUATOR'"}[refplane]),
            ('TP_TYPE', {'absolute': 'ABSOLUTE',
                         'relative': 'RELATIVE'}[tp_type])]
        )

        # parse self.epochs
        if isinstance(self.epochs, (list, tuple, ndarray)):
            request_payload['TLIST'] = "\n".join([str(epoch) for
                                                  epoch in
                                                  self.epochs])
        elif type(self.epochs) is dict:
            if ('start' not in self.epochs or 'stop' not in self.epochs or
                    'step' not in self.epochs):
                raise ValueError("'epochs' must contain start, "
                                 "stop, step")
            request_payload['START_TIME'] = '"'+self.epochs['start']+'"'
            request_payload['STOP_TIME'] = '"'+self.epochs['stop']+'"'
            request_payload['STEP_SIZE'] = '"'+self.epochs['step']+'"'

        else:
            request_payload['TLIST'] = str(self.epochs)

        self.query_type = 'elements'

        # return request_payload if desired
        if get_query_payload:
            return request_payload

        # set return_raw flag, if raw response desired
        if get_raw_response:
            self.return_raw = True

        # query and parse
        response = self._request('GET', URL, params=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        self.uri = response.url

        # check length of uri
        if len(self.uri) >= 2000:
            warnings.warn(('The URI used in this query is very long '
                           'and might have been truncated. The results of '
                           'the query might be compromised. If you queried '
                           'a list of epochs, consider querying a range.'))

        return response

    def vectors_async(self, get_query_payload=False,
                      closest_apparition=False, no_fragments=False,
                      get_raw_response=False, cache=True, refplane='ecliptic'):
        """
        Query JPL Horizons for state vectors. The ``location``
        parameter in ``HorizonsClass`` refers in this case to the center
        body relative to which the vectors are provided.

        The following table lists the values queried, their
        definitions, data types, units, and original Horizons
        designations (where available). For more information on the
        definitions of these quantities, please refer to the `Horizons
        User Manual <https://ssd.jpl.nasa.gov/?horizons_doc>`_.

        +------------------+-----------------------------------------------+
        | Column Name      | Definition                                    |
        +==================+===============================================+
        | targetname       | official number, name, designation (string)   |
        +------------------+-----------------------------------------------+
        | H                | absolute magnitude in V band (float, mag)     |
        +------------------+-----------------------------------------------+
        | G                | photometric slope parameter (float)           |
        +------------------+-----------------------------------------------+
        | M1               | comet total abs mag (float, mag, ``M1``)      |
        +------------------+-----------------------------------------------+
        | M2               | comet nuclear abs mag (float, mag, ``M2``)    |
        +------------------+-----------------------------------------------+
        | k1               | total mag scaling factor (float, ``k1``)      |
        +------------------+-----------------------------------------------+
        | k2               | nuclear mag scaling factor (float, ``k2``)    |
        +------------------+-----------------------------------------------+
        | phasecoeff       | comet phase coeff (float, mag/deg, ``PHCOFF``)|
        +------------------+-----------------------------------------------+
        | datetime_str     | epoch Date (str, ``Calendar Date (TDB)``)     |
        +------------------+-----------------------------------------------+
        | datetime_jd      | epoch Julian Date (float, ``JDTDB``)          |
        +------------------+-----------------------------------------------+
        | x                | x-component of position vector                |
        |                  | (float, au, ``X``)                            |
        +------------------+-----------------------------------------------+
        | y                | y-component of position vector                |
        |                  | (float, au, ``Y``)                            |
        +------------------+-----------------------------------------------+
        | z                | z-component of position vector                |
        |                  | (float, au, ``Z``)                            |
        +------------------+-----------------------------------------------+
        | vx               | x-component of velocity vector (float, au/d,  |
        |                  | ``VX``)                                       |
        +------------------+-----------------------------------------------+
        | vy               | y-component of velocity vector (float, au/d,  |
        |                  | ``VY``)                                       |
        +------------------+-----------------------------------------------+
        | vz               | z-component of velocity vector (float, au/d,  |
        |                  | ``VZ``)                                       |
        +------------------+-----------------------------------------------+
        | lighttime        | one-way lighttime (float, d, ``LT``)          |
        +------------------+-----------------------------------------------+
        | range            | range from coordinate center (float, au,      |
        |                  | ``RG``)                                       |
        +------------------+-----------------------------------------------+
        | range_rate       | range rate (float, au/d, ``RR``)              |
        +------------------+-----------------------------------------------+


        Parameters
        ----------
        closest_apparition : boolean, optional
            Only applies to comets. This option will choose the
            closest apparition available in time to the selected
            epoch; default: False. Do not use this option for
            non-cometary objects.
        no_fragments : boolean, optional
            Only applies to comets. Reject all comet fragments from
            selection; default: False. Do not use this option for
            non-cometary objects.
        get_query_payload : boolean, optional
            When set to `True` the method returns the HTTP request
            parameters as a dict, default: False
        get_raw_response: boolean, optional
            Return raw data as obtained by JPL Horizons without parsing the
            data into a table, default: False
        refplane : string
            Reference plane for all output quantities: ``'ecliptic'``
            (ecliptic and mean equinox of reference epoch), ``'earth'``
            (Earth mean equator and equinox of reference epoch), or
            ``'body'`` (body mean equator and node of date); default:
            ``'ecliptic'``


        Returns
        -------
        response : `requests.Response`
            The response of the HTTP request.


        Examples
        --------
            >>> from astroquery.jplhorizons import Horizons
            >>> obj = Horizons(id='2012 TC4', location='257',
            ...             epochs={'start':'2017-10-01',
            ...                     'stop':'2017-10-02',
            ...                     'step':'10m'})
            >>> vec = obj.vectors() # doctest: +SKIP
            >>> print(vec) # doctest: +SKIP
            targetname  datetime_jd  ...      range          range_rate
               ---           d       ...        AU             AU / d
            ---------- ------------- ... --------------- -----------------
            (2012 TC4)     2458027.5 ... 0.0429332099306 -0.00408018711862
            (2012 TC4) 2458027.50694 ... 0.0429048742906 -0.00408040726527
            (2012 TC4) 2458027.51389 ... 0.0428765385796 -0.00408020747595
            (2012 TC4) 2458027.52083 ... 0.0428482057142  -0.0040795878561
            (2012 TC4) 2458027.52778 ...  0.042819878607 -0.00407854931543
            (2012 TC4) 2458027.53472 ... 0.0427915601617  -0.0040770935665
                   ...           ... ...             ...               ...
            (2012 TC4) 2458028.45833 ... 0.0392489462501 -0.00405496595173
            (2012 TC4) 2458028.46528 ...   0.03922077771 -0.00405750632914
            (2012 TC4) 2458028.47222 ...  0.039192592935 -0.00405964084539
            (2012 TC4) 2458028.47917 ...  0.039164394759 -0.00406136516755
            (2012 TC4) 2458028.48611 ... 0.0391361860433 -0.00406267574646
            (2012 TC4) 2458028.49306 ... 0.0391079696711  -0.0040635698239
            (2012 TC4)     2458028.5 ... 0.0390797485422 -0.00406404543822
            Length = 145 rows
        """

        URL = conf.horizons_server

        # check for required information
        if self.id is None:
            raise ValueError("'id' parameter not set. Query aborted.")
        if self.location is None:
            self.location = '500@10'
        if self.epochs is None:
            self.epochs = Time.now().jd

        # assemble commandline based on self.id_type
        commandline = str(self.id)

        if self.id_type in ['designation', 'name',
                            'asteroid_name', 'comet_name']:
            commandline = ({'designation': 'DES=',
                            'name': 'NAME=',
                            'asteroid_name': 'ASTNAM=',
                            'comet_name': 'COMNAM='}[self.id_type] +
                           commandline)
        if self.id_type in ['smallbody', 'asteroid_name',
                            'comet_name', 'designation']:
            commandline += ';'
            if isinstance(closest_apparition, bool):
                if closest_apparition:
                    commandline += ' CAP;'
            else:
                commandline += ' CAP{:s};'.format(closest_apparition)
            if no_fragments:
                commandline += ' NOFRAG;'

        if isinstance(self.location, dict):
            raise ValueError(('cannot use topographic position in state'
                              'vectors query'))

        # configure request_payload for ephemerides query
        request_payload = OrderedDict([
            ('batch', 1),
            ('TABLE_TYPE', 'VECTORS'),
            ('OUT_UNITS', 'AU-D'),
            ('COMMAND', '"' + commandline + '"'),
            ('CENTER', ("'" + str(self.location) + "'")),
            ('CSV_FORMAT', ('"YES"')),
            ('REF_PLANE', {'ecliptic': 'ECLIPTIC', 'earth': 'FRAME',
                           'body': "'BODY EQUATOR'"}[refplane]),
            ('REF_SYSTEM', 'J2000'),
            ('TP_TYPE', 'ABSOLUTE'),
            ('LABELS', 'YES'),
            ('OBJ_DATA', 'YES')]
        )

        # parse self.epochs
        if isinstance(self.epochs, (list, tuple, ndarray)):
            request_payload['TLIST'] = "\n".join([str(epoch) for epoch in
                                                  self.epochs])
        elif type(self.epochs) is dict:
            if ('start' not in self.epochs or 'stop' not in self.epochs or
                    'step' not in self.epochs):
                raise ValueError("'epochs' must contain start, " +
                                 "stop, step")
            request_payload['START_TIME'] = '"'+self.epochs['start']+'"'
            request_payload['STOP_TIME'] = '"'+self.epochs['stop']+'"'
            request_payload['STEP_SIZE'] = '"'+self.epochs['step']+'"'

        else:
            # treat epochs as a list
            request_payload['TLIST'] = str(self.epochs)

        self.query_type = 'vectors'

        # return request_payload if desired
        if get_query_payload:
            return request_payload

        # set return_raw flag, if raw response desired
        if get_raw_response:
            self.return_raw = True

        # query and parse
        response = self._request('GET', URL, params=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        self.uri = response.url

        # check length of uri
        if len(self.uri) >= 2000:
            warnings.warn(('The URI used in this query is very long '
                           'and might have been truncated. The results of '
                           'the query might be compromised. If you queried '
                           'a list of epochs, consider querying a range.'))

        return response

    # ---------------------------------- parser functions

    def _parse_horizons(self, src):
        """
        Routine for parsing data from JPL Horizons


        Parameters
        ----------
        self : HorizonsClass instance
        src : list
            raw response from server


        Returns
        -------
        data : `astropy.Table`
        """

        # return raw response, if desired
        if self.return_raw:
            # reset return_raw flag
            self.return_raw = False
            return src

        # split response by line break
        src = src.split('\n')

        data_start_idx = 0
        data_end_idx = 0
        H, G = nan, nan
        M1, M2, k1, k2, phcof = nan, nan, nan, nan, nan
        headerline = []
        for idx, line in enumerate(src):
            # read in ephemerides header line; replace some field names
            if (self.query_type is 'ephemerides' and
                    "Date__(UT)__HR:MN" in line):
                headerline = str(line).split(',')
                headerline[2] = 'solar_presence'
                headerline[3] = 'flags'
                headerline[-1] = '_dump'
            # read in elements header line
            elif (self.query_type is 'elements' and
                  "JDTDB," in line):
                headerline = str(line).split(',')
                headerline[-1] = '_dump'
            # read in vectors header line
            elif (self.query_type is 'vectors' and
                  "JDTDB," in line):
                headerline = str(line).split(',')
                headerline[-1] = '_dump'
            # identify end of data block
            if "$$EOE" in line:
                data_end_idx = idx
            # identify start of data block
            if "$$SOE" in line:
                data_start_idx = idx + 1
            # read in targetname
            if "Target body name" in line:
                targetname = line[18:50].strip()
            # read in H and G (if available)
            if "rotational period in hours)" in line:
                HGline = src[idx + 2].split('=')
                if 'B-V' in HGline[2] and 'G' in HGline[1]:
                    try:
                        H = float(HGline[1].rstrip('G'))
                        G = float(HGline[2].rstrip('B-V'))
                    except ValueError:
                        H = nan
                        G = nan
            # read in M1, M2, k1, k2, and phcof (if available)
            if "Comet physical" in line:
                HGline = src[idx + 2].split('=')
                try:
                    M1 = float(HGline[1].rstrip('M2'))
                    k1 = float(HGline[3].rstrip('k2'))
                except ValueError:
                    M1 = nan
                    k1 = nan
                try:
                    M2 = float(HGline[2].rstrip('k1'))
                    k2 = float(HGline[4].rstrip('PHCOF'))
                except ValueError:
                    M2 = nan
                    k2 = nan
                try:
                    phcof = float(HGline[5])
                except ValueError:
                    phcof = nan
            # catch unambiguous names
            if (("Multiple major-bodies match string" in line or
                 "Matching small-bodies:" in line) and
                    ("No matches found" not in src[idx + 1])):
                for i in range(idx + 2, len(src), 1):
                    if (('To SELECT, enter record' in src[i]) or
                            ('make unique selection.' in src[i])):
                        end_idx = i
                        break
                raise ValueError(('Ambiguous target name; provide '
                                  'unique id:\n%s' %
                                  '\n'.join(src[idx + 2:end_idx])))
            # catch unknown target
            if ("Matching small-bodies" in line and
                    "No matches found" in src[idx + 1]):
                raise ValueError(('Unknown target ({:s}). Maybe try '
                                  'different id_type?').format(self.id))
            # catch any unavailability of ephemeris data
            if "No ephemeris for target" in line:
                errormsg = line[line.find('No ephemeris for target'):]
                errormsg = errormsg[:errormsg.find('\n')]
                raise ValueError('Horizons Error: {:s}'.format(errormsg))
            # catch elements errors
            if "Cannot output elements" in line:
                errormsg = line[line.find('Cannot output elements'):]
                errormsg = errormsg[:errormsg.find('\n')]
                raise ValueError('Horizons Error: {:s}'.format(errormsg))
            if 'INPUT ERROR' in line:
                headerline = []
                break

        if headerline == []:
            err_msg = "".join(src[data_start_idx:data_end_idx])
            if len(err_msg) > 0:
                raise ValueError('Query failed with error message:\n' +
                                 err_msg)
            else:
                raise ValueError(('Query failed without error message; '
                                  'check URI for more information'))
        # strip whitespaces from column labels
        headerline = [h.strip() for h in headerline]

        # remove all 'Cut-off' messages
        raw_data = [line for line in src[data_start_idx:data_end_idx]
                    if 'Cut-off' not in line]

        # read in data
        data = ascii.read(raw_data,
                          names=headerline,
                          fill_values=[('.n.a.', '0'),
                                       ('n.a.', '0')])
        # force to a masked table
        data = Table(data, masked=True)

        # convert data to QTable
        # from astropy.table import QTable
        # data = QTable(data)
        # does currently not work, unit assignment in columns creates error
        # results in:
        # TypeError: The value must be a valid Python or Numpy numeric type.

        # remove last column as it is empty
        data.remove_column('_dump')

        # add targetname and physical properties as columns
        data.add_column(Column([targetname] * len(data),
                               name='targetname'), index=0)
        if not isnan(H):
            data.add_column(Column([H] * len(data),
                                   name='H'), index=3)
        if not isnan(G):
            data.add_column(Column([G] * len(data),
                                   name='G'), index=4)
        if not isnan(M1):
            data.add_column(Column([M1] * len(data),
                                   name='M1'), index=3)
        if not isnan(M2):
            data.add_column(Column([M2] * len(data),
                                   name='M2'), index=4)
        if not isnan(k1):
            data.add_column(Column([k1] * len(data),
                                   name='k1'), index=5)
        if not isnan(k2):
            data.add_column(Column([k2] * len(data),
                                   name='k2'), index=6)
        if not isnan(phcof):
            data.add_column(Column([phcof] * len(data),
                                   name='phasecoeff'), index=7)

        # replace missing airmass values with 999 (not observable)
        if self.query_type is 'ephemerides' and 'a-mass' in data.colnames:
            data['a-mass'] = data['a-mass'].filled(999)

        # set column definition dictionary
        if self.query_type is 'ephemerides':
            column_defs = conf.eph_columns
        elif self.query_type is 'elements':
            column_defs = conf.elem_columns
        elif self.query_type is 'vectors':
            column_defs = conf.vec_columns
        else:
            raise TypeError('Query type unknown.')

        # set column units
        rename = []
        for col in data.columns:
            data[col].unit = column_defs[col][1]
            if data[col].name != column_defs[col][0]:
                rename.append(data[col].name)

        # rename columns
        for col in rename:
            try:
                data.rename_column(data[col].name, column_defs[col][0])
            except KeyError:
                pass

        return data

    def _parse_result(self, response, verbose=None):
        """
        Routine for managing parser calls;


        This routine decides based on `self.query_type` which parser
        has to be used.


        Parameters
        ----------
        self : Horizonsclass instance
        response : string
            raw response from server


        Returns
        -------
        data : `astropy.Table`

        """
        if self.query_type not in ['ephemerides', 'elements', 'vectors']:
            return None
        else:
            data = self._parse_horizons(response.text)

        return data


# the default tool for users to interact with is an instance of the Class
Horizons = HorizonsClass()
