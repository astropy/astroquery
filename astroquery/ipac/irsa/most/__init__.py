# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
IRSA Moving Object Search Tool (MOST) Query Tool
================================================

This module contains functionality required for
querying of MOST service.
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    '''
    Configuration parameters for `astroquery.ipac.irsa.most`.
    '''

    server = _config.ConfigItem(
        'https://irsa.ipac.caltech.edu/cgi-bin/MOST/nph-most',
        'URL address of the MOST service.')
    interface_url = _config.ConfigItem(
        'https://irsa.ipac.caltech.edu/applications/MOST/',
        'URL address of the MOST application interface.'
    )
    timeout = _config.ConfigItem(
        120,
        'Time limit for connecting to the IRSA server.')


conf = Conf()


from .core import Most, MOSTClass

__all__ = [
    'Most', 'MOSTClass',
    'Conf', 'conf',
]
