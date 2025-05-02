# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
IMCCE
-----

:author: Michael Mommert (mommermiscience@gmail.com)
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.imcce`.
    """

    # server settings
    ephemcc_server = _config.ConfigItem(
        'http://vo.imcce.fr/webservices/miriade/ephemcc_query.php',
        'IMCCE/Miriade.ephemcc base server')
    skybot_server = _config.ConfigItem(
        ['https://ssp.imcce.fr/webservices/skybot/api/conesearch.php'],
        'SkyBoT')

    timeout = _config.ConfigItem(
        300,
        'Time limit for connecting to IMCCE servers.')

    # SkyBoT configuration

    # dictionary for field name and unit conversions using 'output=all`
    field_names = {'num': 'Number',
                   'name': 'Name',
                   'ra': 'RA',
                   'de': 'DEC',
                   'class': 'Type',
                   'magV': 'V',
                   'errpos': 'posunc',
                   'angdist': 'centerdist',
                   'dracosdec': 'RA_rate',
                   'ddec': 'DEC_rate',
                   'dgeo': 'geodist',
                   'dhelio': 'heliodist',
                   'phase': 'alpha',
                   'solelong': 'elong',
                   'px': 'x',
                   'py': 'y',
                   'pz': 'z',
                   'vx': 'vx',
                   'vy': 'vy',
                   'vz': 'vz',
                   'jdref': 'epoch',
                   '_raj2000': '_raj2000',
                   '_decj2000': '_decj2000',
                   'externallink': 'externallink'}


conf = Conf()

from .core import Miriade, MiriadeClass, Skybot, SkybotClass

__all__ = ['Miriade', 'MiriadeClass',
           'Skybot', 'SkybotClass',
           'Conf', 'conf',
           ]
