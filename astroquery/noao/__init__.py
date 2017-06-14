# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
NOAO Archive Service
-------------------------

:author: Ayush Yadav (ayushyadav@outlook.com)
"""

# Make the URL of the server, timeout and other items configurable
# See <http://docs.astropy.org/en/latest/config/index.html#developer-usage>
# for docs and examples on how to do this
# Below is a common use case
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.noao`.
    """
    server = _config.ConfigItem(
        ['http://archive.noao.edu/search/query'
         ],
        'The NOAO search server to use.')

    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to noao server.')


conf = Conf()

# Now import your public class
# Should probably have the same name as your module
from .core import Template, TemplateClass

__all__ = ['NOAO', 'NOAOClass',
           'Conf', 'conf',
           ]
