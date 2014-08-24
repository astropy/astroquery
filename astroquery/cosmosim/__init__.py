"""
CosmoSim Database Query Tool
-----------------------------
.. topic:: Revision History

    Access to all cosmological simulations stored in the CosmoSim database, via the uws service.

    http://www.cosmosim.org/uws/query

    :Author: Austen M. Groener <Austen.M.Groener@drexel.edu>
"""

from astropy.config import ConfigItem

COSMOSIM_SERVER = ConfigItem('cosmosim_server',["http://www.cosmosim.org/uws/query"],'Name of the CosmoSim mirror to use.')

COSMOSIM_TIMEOUT = ConfigItem('timeout', 60, 'time limit for connecting to CosmoSim server')

from .core import CosmoSim

__all__ = ['CosmoSim']
