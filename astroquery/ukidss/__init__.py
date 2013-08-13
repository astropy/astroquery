# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
UKIDSS Image and Catalog Query Tool
-----------------------------------
.. topic:: Revision History

    Refactored using common API as a part of Google Summer of Code 2013.

    :Originally contributed by:

        Thomas Robitalle (thomas.robitaille@gmail.com)

        Adam Ginsburg (adam.g.ginsburg@gmail.com)
"""
from astropy.config import ConfigurationItem

UKIDSS_SERVER = ConfigurationItem('ukidss_server', ["http://surveys.roe.ac.uk:8080/wsa/"],
                                  'Name of the UKIDSS mirror to use.')
UKIDSS_TIMEOUT = ConfigurationItem('timeout', 60, 'time limit for connecting to UKIDSS server')

from .core import Ukidss,clean_catalog

__all__ = ['Ukidss','clean_catalog']
