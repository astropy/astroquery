# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
<Put Your Tool Name Here>
-------------------------

:author: <your name> (<your email>)
"""

# Make the URL of the server, timeout and other items configurable
# See <http://docs.astropy.org/en/latest/config/index.html#developer-usage>
# for docs and examples on how to do this
# Below is a common use case
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.template_module`.
    """
    server = _config.ConfigItem(
        ['http://dummy_server_mirror_1',
         'http://dummy_server_mirror_2',
         'http://dummy_server_mirror_n'],
        'Name of the template_module server to use.')

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to template_module server.')

conf = Conf()

# Now import your public class
# Should probably have the same name as your module
from .core import Template, TemplateClass

__all__ = ['Template', 'TemplateClass',
           'Conf', 'conf',
           ]
