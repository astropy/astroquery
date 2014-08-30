"""
CosmoSim Database Query Tool
-----------------------------
.. topic:: Revision History

    Access to all cosmological simulations stored in the CosmoSim database, via the uws service.

    http://www.cosmosim.org/uws/query

    :Author: Austen M. Groener <Austen.M.Groener@drexel.edu>
"""

from astropy import config as _config

class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.cosmosim`.
    """

    query_url = _config.ConfigItem(
        ['http://www.cosmosim.org/uws/query'],
        'CosmoSim UWS query URL'
        )
    schema_url = _config.ConfigItem(
        ['http://www.cosmosim.org/query/account/databases/json'],
        'CosmoSim json query URL for generating database schema'
        )
    timeout = _config.ConfigItem(
        60.0,
        'Timeout for CosmoSim query'
        )
    
conf = Conf()

from .core import CosmoSim

__all__ = ['CosmoSim', 'Conf', 'conf']
