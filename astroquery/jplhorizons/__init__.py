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
    # default: all quantities
    eph_quantities = ('1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,'
                      '21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,'
                      '38,39,40,41,42,43')

    # provide column names and units for each queried quantity for different
    # query modes
    eph_columns = {'targetname': ('targetname', '---'),
                   'Date__(UT)__HR:MN': ('datetime_str', '---'),
                   'Date__(UT)__HR:MN:SC.fff': ('datetime_str', '---'),
                   'Date_________JDUT': ('datetime_jd', 'd'),
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
                   'DEC_(ICRF/J2000.0)': ('DEC', 'deg'),
                   'R.A._(FK4/B1950.0)': ('RA', 'deg'),
                   'DEC_(FK4/B1950.0)': ('DEC', 'deg'),
                   'R.A._(a-app)': ('RA_app', 'deg'),
                   'DEC_(a-app)': ('DEC_app', 'deg'),
                   'R.A._(r-app)': ('RA_app', 'deg'),
                   'DEC_(r-app)': ('DEC_app', 'deg'),
                   'dRA*cosD': ('RA_rate', 'arcsec/hour'),
                   'd(DEC)/dt': ('DEC_rate', 'arcsec/hour'),
                   'Azi_(a-app)': ('AZ', 'deg'),
                   'Elev_(a-app)': ('EL', 'deg'),
                   'Azi_(r-appr)': ('AZ', 'deg'),
                   'Elev_(r-appr)': ('EL', 'deg'),
                   'dAZ*cosE': ('AZ_rate', 'arcsec/minute'),
                   'd(ELV)/dt': ('EL_rate', 'arcsec/minute'),
                   'X_(sat-prim)': ('sat_X', 'arcsec'),
                   'Y_(sat-prim)': ('sat_Y', 'arcsec'),
                   'SatPANG': ('sat_PANG', 'deg'),
                   'L_Ap_Sid_Time': ('siderealtime', '---'),
                   'a-mass': ('airmass', '---'),
                   'mag_ex': ('magextinct', 'mag'),
                   'APmag': ('V', 'mag'),
                   'T-mag': ('Tmag', 'mag'),
                   'N-mag': ('Nmag', 'mag'),
                   'S-brt': ('surfbright',
                             'mag/arcsec**2'),
                   'Illu%': ('illumination', 'percent'),
                   'Def_illu': ('illum_defect', 'arcsec'),
                   'ang-sep': ('sat_sep', 'arcsec'),
                   'v': ('sat_vis', '---'),
                   'Ang-diam': ('ang_width', 'arcsec'),
                   'Ob-lon': ('PDObsLon', 'deg'),
                   'Ob-lat': ('PDObsLat', 'deg'),
                   'Sl-lon': ('PDSunLon', 'deg'),
                   'Sl-lat': ('PDSunLat', 'deg'),
                   'Obsrv-lon': ('PDObsLon', 'deg'),
                   'Obsrv-lat': ('PDObsLat', 'deg'),
                   'Solar-lon': ('PDSunLon', 'deg'),
                   'Solar-lat': ('PDSunLat', 'deg'),
                   'SN.ang': ('SubSol_ang', 'deg'),
                   'SN.dist': ('SubSol_dist', 'arcsec'),
                   'NP.ang': ('NPole_ang', 'deg'),
                   'NP.dist': ('NPole_dist', 'arcsec'),
                   'hEcl-Lon': ('EclLon', 'deg'),
                   'hEcl-Lat': ('EclLat', 'deg'),
                   'r': ('r', 'au'),
                   'rdot': ('r_rate', 'km/second'),
                   'delta': ('delta', 'au'),
                   'deldot': ('delta_rate', 'km/second'),
                   '1-way_LT': ('lighttime', 'minute'),
                   'VmagSn': ('vel_sun', 'km/s'),
                   'VmagOb': ('vel_obs', 'km/s'),
                   'S-O-T': ('elong', 'deg'),
                   '/r': ('elongFlag', '---'),
                   'S-T-O': ('alpha', 'deg'),
                   'T-O-M': ('lunar_elong', 'deg'),
                   'T-O-I': ('IB_elong', 'deg'),
                   'MN_Illu%': ('lunar_illum', 'percent'),
                   'IB_Illu%': ('IB_illum', 'percent'),
                   'O-P-T': ('sat_alpha', 'deg'),
                   'PlAng': ('OrbPlaneAng', 'deg'),
                   'PsAng': ('sunTargetPA', 'deg'),
                   'PsAMV': ('velocityPA', 'deg'),
                   'Cnst': ('constellation', '---'),
                   'TDB-UT': ('TDB-UT', 'second'),
                   'ObsEcLon': ('ObsEclLon', 'deg'),
                   'ObsEcLat': ('ObsEclLat', 'deg'),
                   'r-ObsEcLon': ('ObsEclLon', 'deg'),
                   'r-ObsEcLat': ('ObsEclLat', 'deg'),
                   'N.Pole-RA': ('NPole_RA', 'deg'),
                   'N.Pole-DC': ('NPole_DEC', 'deg'),
                   'GlxLon': ('GlxLon', 'deg'),
                   'GlxLat': ('GlxLat', 'deg'),
                   'L_Ap_SOL_Time': ('solartime', '---'),
                   '399_ins_LT': ('earth_lighttime', 'minute'),
                   'RA_3sigma': ('RA_3sigma', 'arcsec'),
                   'DEC_3sigma': ('DEC_3sigma', 'arcsec'),
                   'SMAA_3sig': ('SMAA_3sigma', 'arcsec'),
                   'SMIA_3sig': ('SMIA_3sigma', 'arcsec'),
                   'Theta': ('Theta_3sigma', 'deg'),
                   'Area_3sig': ('Area_3sigma', 'arcsec^2'),
                   'POS_3sigma': ('RSS_3sigma', 'arcsec'),
                   'RNG_3sigma': ('r_3sigma', 'km'),
                   'RNGRT_3sig': ('r_rate_3sigma', 'km/s'),
                   'DOP_S_3sig': ('SBand_3sigma', 'Hz'),
                   'DOP_X_3sig': ('XBand_3sigma', 'Hz'),
                   'RT_delay_3sig': ('DoppDelay_3sigma', 'second'),
                   'Tru_Anom': ('true_anom', 'deg'),
                   'r-L_Ap_Hour_Ang': ('hour_angle', '---'),
                   'L_Ap_Hour_Ang': ('hour_angle', '---'),
                   'phi': ('alpha_true', 'deg'),
                   'PAB-LON': ('PABLon', 'deg'),
                   'PAB-LAT': ('PABLat', 'deg')
                   }

    elem_columns = {'targetname': ('targetname', '---'),
                    'JDTDB': ('datetime_jd', 'd'),
                    'Calendar Date (TDB)': ('datetime_str',
                                            '---'),
                    'H': ('H', 'mag'),
                    'G': ('G', '---'),
                    'M1': ('M1', 'mag'),
                    'M2': ('M2', 'mag'),
                    'k1': ('k1', '---'),
                    'k2': ('k2', '---'),
                    'phasecoeff': ('phasecoeff',
                                   'mag/deg'),
                    'EC': ('e', '---'),
                    'QR': ('q', 'AU'),
                    'IN': ('incl', 'deg'),
                    'OM': ('Omega', 'deg'),
                    'W': ('w', 'deg'),
                    'Tp': ('Tp_jd', 'd'),
                    'N': ('n', 'deg/day'),
                    'MA': ('M', 'deg'),
                    'TA': ('nu', 'deg'),
                    'A': ('a', 'AU'),
                    'AD': ('Q', 'AU'),
                    'PR': ('P', 'd')}

    vec_columns = {'targetname': ('targetname', '---'),
                   'JDTDB': ('datetime_jd', 'd'),
                   'Calendar Date (TDB)': ('datetime_str',
                                           '---'),
                   'H': ('H', 'mag'),
                   'G': ('G', '---'),
                   'M1': ('M1', 'mag'),
                   'M2': ('M2', 'mag'),
                   'k1': ('k1', '---'),
                   'k2': ('k2', '---'),
                   'phasecoeff': ('phasecoeff',
                                  'mag/deg'),
                   'X': ('x', 'AU'),
                   'Y': ('y', 'AU'),
                   'Z': ('z', 'AU'),
                   'VX': ('vx', 'AU/d'),
                   'VY': ('vy', 'AU/d'),
                   'VZ': ('vz', 'AU/d'),
                   'LT': ('lighttime', 'd'),
                   'RG': ('range', 'AU'),
                   'RR': ('range_rate',
                          'AU/d')}


conf = Conf()

from .core import Horizons, HorizonsClass

__all__ = ['Horizons', 'HorizonsClass',
           'Conf', 'conf',
           ]
