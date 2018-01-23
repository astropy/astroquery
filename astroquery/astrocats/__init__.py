# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
OPEN ASTRONOMY CATALOG (OAC) API TOOL
-------------------------
This module allows access to the OAC API and
all available functionality. For more information
see: api.astrocats.space.
:authors: Philip S. Cowperthwaite (pcowpert@cfa.harvard.edu)
and James Guillochon (jguillochon@cfa.harvard.edu)
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.oacapi`.
    """
    server = _config.ConfigItem(
        ['https://api.astrocats.space/'],
        'URL of the primary API Server')

    timeout = _config.ConfigItem(
        60,
        'Timeout limit for API Server')

conf = Conf()

# Now import your public class
# Should probably have the same name as your module
from .core import OACAPI, OACAPIClass

__all__ = ['OACAPI', 'OACAPIClass',
           'Conf', 'conf',
           ]
