# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
JPLHorizons
-----------

:author: Michael Mommert (mommermiscience@gmail.com)
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.jplhorizons`.
    """

    # server settings
    horizons_server = _config.ConfigItem(
        'https://ssd.jpl.nasa.gov/horizons_batch.cgi',
        'JPL Horizons')

    # implement later: sbdb_server = 'http://ssd-api.jpl.nasa.gov/sbdb.api'

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to JPL servers.')

    # JPL Horizons settings

    # quantities queried in ephemerides query (see
    # http://ssd.jpl.nasa.gov/?horizons_doc#table_quantities)
    eph_quantities = '"1,3,4,8,9,10,18,19,20,21,23,24,27,31,33,36"'

    # provide column names and units for each queried quantity for different
    # query modes
    eph_columns = {'targetname': ('targetname', '---'),
                   ' Date__(UT)__HR:MN': ('datetime_str', '---'),
                   ' Date__(UT)__HR:MN:SC.fff': ('datetime_str', '---'),
                   ' Date_________JDUT': ('datetime_jd', 'd'),
                   'H': ('H', 'mag'),
                   'G': ('G', '---'),
                   'M1': ('M1', 'mag'),
                   'M2': ('M2', 'mag'),
                   'k1': ('k1', '---'),
                   'k2': ('k2', '---'),
                   'phasecoeff': ('phasecoeff', 'mag/deg'),
                   'solar_presence': ('solar_presence', '---'),
                   'flags': ('flags', '---'),
                   'R.A._(ICRF/J2000.0)': ('RA', 'deg'),
                   ' DEC_(ICRF/J2000.0)': ('DEC', 'deg'),
                   ' dRA*cosD': ('RA_rate', 'arcsec/hour'),
                   'd(DEC)/dt': ('DEC_rate', 'arcsec/hour'),
                   ' Azi_(a-app)': ('AZ', 'deg'),
                   ' Elev_(a-app)': ('EL', 'deg'),
                   ' a-mass': ('airmass', '---'),
                   'mag_ex': ('magextinct', 'mag'),
                   '  APmag': ('V', 'mag'),
                   '  T-mag': ('Tmag', 'mag'),
                   ' N-mag': ('Nmag', 'mag'),
                   ' S-brt': ('surfbright',
                              'mag/arcsec**2'),
                   '   Illu%': ('illumination', 'percent'),
                   ' hEcl-Lon': ('EclLon', 'deg'),
                   'hEcl-Lat': ('EclLat', 'deg'),
                   '               r': ('r', 'au'),
                   '       rdot': ('r_rate', 'km/second'),
                   '            delta': ('delta', 'au'),
                   '     deldot': ('delta_rate', 'km/second'),
                   '   1-way_LT': ('lighttime', 'minute'),
                   '    S-O-T': ('elong', 'deg'),
                   '/r': ('elongFlag', '---'),
                   '    S-T-O': ('alpha', 'deg'),
                   '   PsAng': ('sunTargetPA', 'deg'),
                   '  PsAMV': ('velocityPA', 'deg'),
                   '    ObsEcLon': ('ObsEclLon', 'deg'),
                   '   ObsEcLat': ('ObsEclLat', 'deg'),
                   '     GlxLon': ('GlxLon', 'deg'),
                   '    GlxLat': ('GlxLat', 'deg'),
                   ' RA_3sigma': ('RA_3sigma', 'arcsec'),
                   'DEC_3sigma': ('DEC_3sigma', 'arcsec')}

    elem_columns = {'targetname': ('targetname', '---'),
                    '            JDTDB': ('datetime_jd', 'd'),
                    '            Calendar Date (TDB)': ('datetime_str',
                                                        '---'),
                    'H': ('H', 'mag'),
                    'G': ('G', '---'),
                    'M1': ('M1', 'mag'),
                    'M2': ('M2', 'mag'),
                    'k1': ('k1', '---'),
                    'k2': ('k2', '---'),
                    'phasecoeff': ('phasecoeff',
                                   'mag/deg'),
                    '                     EC': ('e', '---'),
                    '                     QR': ('q', 'AU'),
                    '                     IN': ('incl', 'deg'),
                    '                     OM': ('Omega', 'deg'),
                    '                      W': ('w', 'deg'),
                    '                     Tp': ('Tp_jd', 'd'),
                    '                      N': ('n', 'deg/day'),
                    '                     MA': ('M', 'deg'),
                    '                     TA': ('nu', 'deg'),
                    '                      A': ('a', 'AU'),
                    '                     AD': ('Q', 'AU'),
                    '                     PR': ('P', 'd')}

    vec_columns = {'targetname': ('targetname', '---'),
                   '            JDTDB': ('datetime_jd', 'd'),
                   '            Calendar Date (TDB)': ('datetime_str',
                                                       '---'),
                   'H': ('H', 'mag'),
                   'G': ('G', '---'),
                   'M1': ('M1', 'mag'),
                   'M2': ('M2', 'mag'),
                   'k1': ('k1', '---'),
                   'k2': ('k2', '---'),
                   'phasecoeff': ('phasecoeff',
                                  'mag/deg'),
                   '                      X': ('x', 'AU'),
                   '                      Y': ('y', 'AU'),
                   '                      Z': ('z', 'AU'),
                   '                     VX': ('vx', 'AU/d'),
                   '                     VY': ('vy', 'AU/d'),
                   '                     VZ': ('vz', 'AU/d'),
                   '                     LT': ('lighttime', 'd'),
                   '                     RG': ('range', 'AU'),
                   '                     RR': ('range_rate',
                                               'AU/d')}


conf = Conf()

from .core import Horizons, HorizonsClass

__all__ = ['Horizons', 'HorizonsClass',
           'Conf', 'conf',
           ]
