# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.vo_conesearch`.
    """
    # Config related to remote database of "reliable" services.
    vos_baseurl = _config.ConfigItem(
        'https://astropy.stsci.edu/aux/vo_databases/',
        'URL where the VO Service database file is stored.')
    conesearch_dbname = _config.ConfigItem(
        'conesearch_good',
        'Conesearch database name to use.')

    # Config related to individual Cone Search query
    timeout = _config.ConfigItem(
        30.0, 'Time limit for connecting to Cone Search service.')
    fallback_url = _config.ConfigItem(
        'http://gsss.stsci.edu/webservices/vo/ConeSearch.aspx?CAT=GSC23&',
        'Just ignore database above and use STScI HST Guide Star Catalog.')
    pedantic = _config.ConfigItem(
        False,
        'If True, raise an error when the result violates the spec, '
        'otherwise issue warning(s).')


conf = Conf()

from .core import ConeSearch  # noqa

__all__ = ['ConeSearch']
