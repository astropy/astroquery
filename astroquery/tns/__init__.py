# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Transient Name Server query tool
----------------------------------

:Author: Noah M. Glimcher (brainsonfire42@gmail.com)

"""
from astropy import config as _config

class Conf(_config.ConfigNamespace):
    """ Configuration parameters for `astroquery.tns` """

    timeout = _config.ConfigItem(120, "Timeout in seconds.")
    api_url = _config.ConfigItem("sandbox.wis-tns.org", "The endpoint URL") # Sandbox TODO: switch to production url "www.wis-tns.org"

    bot_name = _config.ConfigItem("", "Your TNS bot name")
    bot_id = _config.ConfigItem("", "Your TNS bot ID")
    api_key = _config.ConfigItem("", "Your TNS API key")

conf = Conf()

from .core import TnsClass

__all__ = ['TnsClass', 'conf']