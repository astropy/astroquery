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
        ['http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca'],
        'CADC server.')

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to template_module server.')


conf = Conf()

from core import *
