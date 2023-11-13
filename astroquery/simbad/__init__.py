# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SIMBAD Query Tool
=================

The SIMBAD query tool creates a `script query
<https://simbad.cds.unistra.fr/simbad/sim-fscript>`__ that returns VOtable XML
data that is then parsed into a SimbadResult object.  This object then
parses the data and returns a table parsed with `astropy.io.votable.parse`.
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.simbad`.
    """
    # the first item is the default configuration
    servers_list = ['simbad.cds.unistra.fr', 'simbad.harvard.edu']

    server = _config.ConfigItem(
        servers_list,
        'Name of the SIMBAD mirror to use.')

    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to Simbad server.')

    row_limit = _config.ConfigItem(
        # O defaults to the maximum limit
        0,
        'Maximum number of rows that will be fetched from the result.')


conf = Conf()

from .core import Simbad, SimbadClass, SimbadBaseQuery

__all__ = ['Simbad', 'SimbadClass',
           'SimbadBaseQuery',
           'Conf', 'conf',
           ]
