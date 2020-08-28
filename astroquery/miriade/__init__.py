# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
IMCCE Miriade
-------------

:author: Miguel de Val-Borro (miguel.deval@gmail.com)
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.miriade`.
    """

    # server settings
    miriade_server = _config.ConfigItem(
        'http://vo.imcce.fr/webservices/miriade/ephemcc_query.php',
        'IMCCE Miriade')

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to Miriade servers.')

    # provide column names and units for each queried quantity
    eph_columns = {'Date UTC (Y-M-D h:m:s)': ('datetime_str', '---'),
                   'RA (h m s)': ('RA', 'hourangle'),
                   'DE (deg arcmin arcs': ('DE', 'deg'),
                   'Distance (au)': ('r', 'au'),
                   'V Mag': ('V mag', 'mag'),
                   'Phase (o)': ('phase', 'deg'),
                   'Sun elong (o)': ('elong', 'deg'),
                   'muRAcosDE (arcsec/min)': ('RA_rate', 'arcsec/minute'),
                   'muDE (arcsec/min)': ('DE_rate', 'arcsec/minute'),
                   'Dist_dot (km/s)': ('r_dot', 'km/second')
                   }


conf = Conf()

from .core import Miriade, MiriadeClass

__all__ = ['Miriade', 'MiriadeClass',
           'Conf', 'conf',
           ]
