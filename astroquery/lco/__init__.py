# Licensed under a 3-clause BSD style license - see LICENSE.rst
# Generative AI was used in the making of this module

"""
Las Cumbres Observatory (LCO)
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.lco`.
    """
    archive_url = _config.ConfigItem(
        ['https://archive-api.lco.global', ],
        'The LCO Archive mirror to use.')

    token_url = _config.ConfigItem(
        'https://observe.lco.global/api/api-token-auth/',
        'URL used to exchange a username and password for an API token.')

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to LCO Archive server.')

    row_limit = _config.ConfigItem(
        100,
        'Maximum number of frames returned by a query. Set to -1 to retrieve '
        'every matching frame.')


conf = Conf()

from astroquery.lco.core import LcoArchive, LcoArchiveClass

__all__ = ['LcoArchive', 'LcoArchiveClass',
           'Conf', 'conf',
           ]
