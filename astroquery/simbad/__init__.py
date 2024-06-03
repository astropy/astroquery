# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SIMBAD Query Tool
=================

The SIMBAD query tool creates `TAP ADQL queries
<https://cds.unistra.fr/help/documentation/simbad-more/adql-simbad/>`__ that return VOtable XML
data. This is then parsed into a `~astropy.table.Table` object.
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
        # defaults to the maximum limit
        -1,
        'Maximum number of rows that will be fetched from the result.')

    # should be columns of 'basic'
    default_columns = ["main_id", "ra", "dec", "coo_err_maj", "coo_err_min",
                       "coo_err_angle", "coo_wavelength", "coo_bibcode"]


conf = Conf()

from .core import Simbad, SimbadClass

__all__ = ['Simbad', 'SimbadClass', 'Conf', 'conf']
