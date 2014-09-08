"""
Millennium Database Query Tool
-----------------------------
.. topic:: Revision History

    Access to all cosmological simulations stored in the Millennium database, via the ??? service.

    http://www.

    :Author: Austen M. Groener <Austen.M.Groener@drexel.edu>
"""

from astropy.config import ConfigurationItem

MILLENNIUM_SERVER = ConfigurationItem('millennium_server',["http://www."],'Name of the Millennium mirror to use.')

MILLENNIUM_TIMEOUT = ConfigurationItem('timeout', 60, 'time limit for connecting to Millennium server')

from .core import Millennium

__all__ = ['Millennium']
