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
    catalog = _config.ConfigItem(
        'wise_merge',
        ('Default catalog to query. See the drop-down menu at '
         'https://irsa.ipac.caltech.edu/applications/MOST/ for options.'))
    input_type = _config.ConfigItem(
        'name_input',
        'Default type of query to run. One of `name_input`, `naifid_input`, '
        '`mpc_input` or `manual_input` corresponding to Solar System Object '
        'Name, NAIF ID, MPC one-line element input type or manual input of '
        'orbital elements.'
    )
    output_mode = _config.ConfigItem(
        'Full',
        ('Set the verbosity of returned results. See the drop-down menu at '
         'https://irsa.ipac.caltech.edu/applications/MOST/ for options.'))
    ephem_step = _config.ConfigItem(
        0.25,
        'Ephemeris step size (day).'
    )
    timeout = _config.ConfigItem(
        120,
        'Time limit for connecting to the IRSA server.')


conf = Conf()


from .core import MOST, MOSTClass

__all__ = ['MOST', 'MOSTClass',
           'Conf', 'conf',
           ]
