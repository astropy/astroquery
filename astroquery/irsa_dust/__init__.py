# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
IRSA Galactic Dust Reddening and Extinction Query Tool
------------------------------------------------------
.. topic:: Revision History

    Refactored using common API as a part of Google Summer of Code 2013.

    :Originally contributed by: David Shiga (dshiga.dev@gmail.com)
"""
from astropy.config import ConfigurationItem
# maintain a list of URLs in case the user wants to append a mirror
IRSA_DUST_SERVER = ConfigurationItem('irsa_dust_server',[
                                    'http://irsa.ipac.caltech.edu/cgi-bin/DUST/nph-dust'],
    'Name of the irsa_dust server to use')

IRSA_DUST_TIMEOUT = ConfigurationItem('timeout', 30, 'default timeout for connecting to server')

from .core import IrsaDust

__all__ = ['IrsaDust']
