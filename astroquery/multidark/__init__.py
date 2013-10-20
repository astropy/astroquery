"""
MultiDark Database Query Tool
-----------------------------
.. topic:: Revision History

    Access to the MultiDark cosmological simulations database, via the MyDB SQL query form.

    http://www.multidark.org/MultiDark/MyDB

    :Author: Austen M. Groener <Austen.M.Groener@drexel.edu>
"""
from astropy.config import ConfigurationItem

MULTIDARK_SERVER = ConfigurationItem('multidark_server',["http://www.multidark.org/MultiDark/"],'Name of the MultiDark mirror to use.')

MULTIDARK_TIMEOUT = ConfigurationItem('timeout', 60, 'time limit for connecting to MultiDark server')

from .core import MultiDark

__all__ = ['MultiDark']
