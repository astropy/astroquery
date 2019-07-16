"""
CSIRO ASKAP Science Data Archive (CASDA)
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.casda`.
    """

    server = _config.ConfigItem(
        ['https://casda.csiro.au/casda_vo_tools/sia2/query'],
        'Name of the CASDA SIA server to use.'
    )
    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to CASDA server.'
    )


conf = Conf()

from .core import Casda, CasdaClass

__all__ = ['Casda', 'CasdaClass', 'conf']
