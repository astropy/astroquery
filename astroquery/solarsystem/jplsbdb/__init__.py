# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
JPLSBDB
-------------------------

:author: Michael Mommert (mommermiscience@gmail.com)
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.jplsbdb`.
    """
    server = _config.ConfigItem(
        ['https://ssd-api.jpl.nasa.gov/sbdb.api'],
        'JPL SBDB')

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to JPL server.')

    # dictionary to replace JPL SBDB units with astropy units in data objects
    data_unit_replace = {'JED': 'd', 'TDB': 'd'}

    # dictionary for units of individual and unique fields
    field_unit = {'epoch': 'd',
                  'cov_epoch': 'd',
                  'moid': 'au',
                  'moid_jup': 'au',
                  'jd': 'd',
                  'sigma_t': 'min',
                  'dist_min': 'au',
                  'dist_max': 'au',
                  'v_rel': 'km / s',
                  'v_inf': 'km / s',
                  'unc_major': 'km',
                  'unc_minor': 'km',
                  'un_angle': 'deg',
                  'dt': 'yr',

                  'v_imp': 'km / s',
                  'h': 'mag',
                  'diam': 'km',
                  'mass': 'kg',
                  }
    # `dist` not listed here, as it is defined twice with different units
    # 'energy' not listed here: 'Mt' not available in astropy.units


conf = Conf()

from .core import SBDB, SBDBClass

__all__ = ['SBDB', 'SBDBClass',
           'Conf', 'conf',
           ]
