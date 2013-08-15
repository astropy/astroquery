# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Module to query the NRAO Data Archive for observation summaries.
"""
from astropy.config import ConfigurationItem

NRAO_SERVER = ConfigurationItem('nrao_server', ['https://archive.nrao.edu/archive/ArchiveQuery'],
                               'Name of the NRAO mirror to use.')
NRAO_TIMEOUT = ConfigurationItem('timeout', 60, 'time limit for connecting to NRAO server')


from .core import Nrao

__all__ = ['Nrao']
