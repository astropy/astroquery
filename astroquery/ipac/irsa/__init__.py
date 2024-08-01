# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
IRSA Query Tool
===============

This module contains various methods for querying the
IRSA Services.

"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.ipac.irsa`.
    """
    most_server = _config.ConfigItem(
        'https://irsa.ipac.caltech.edu/cgi-bin/MOST/nph-most',
        'URL address of the MOST service.')
    most_interface_url = _config.ConfigItem(
        'https://irsa.ipac.caltech.edu/applications/MOST/',
        'URL address of the MOST application interface.'
    )
    row_limit = _config.ConfigItem(
        500,
        'Maximum number of rows to retrieve in result')
    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to the IRSA server.')
    sia_url = _config.ConfigItem('https://irsa.ipac.caltech.edu/SIA', 'IRSA SIA URL')
    ssa_url = _config.ConfigItem('https://irsa.ipac.caltech.edu/SSA', 'IRSA SSA URL')
    tap_url = _config.ConfigItem('https://irsa.ipac.caltech.edu/TAP', 'IRSA TAP URL')


conf = Conf()


from .core import Irsa, IrsaClass
from .most import Most, MostClass

__all__ = ['Irsa', 'IrsaClass', 'Most', 'MostClass', 'Conf', 'conf', ]
