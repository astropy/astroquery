# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
OPEN ASTRONOMY CATALOG (OAC) API TOOL
-------------------------------------
This module allows access to the OAC API and
all available functionality. For more information
see: https://api.astrocats.space.
:authors: Philip S. Cowperthwaite (pcowpert@cfa.harvard.edu)
and James Guillochon (jguillochon@cfa.harvard.edu)
"""

from astropy import config as _config

# Now import your public class
# Should probably have the same name as your module


class Conf(_config.ConfigNamespace):
    """Configuration parameters for `astroquery.oac`."""

    server = _config.ConfigItem(
        ['https://api.astrocats.space/'],
        'URL of the primary API Server')

    timeout = _config.ConfigItem(
        60,
        'Timeout limit for API Server')


conf = Conf()

from .core import OAC, OACClass


__all__ = ['OAC', 'OACClass',
           'Conf', 'conf',
           ]
