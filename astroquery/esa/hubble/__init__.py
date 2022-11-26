# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
==========
eHST Init
==========

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

from astropy import config as _config
from astropy.config import paths
import os


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esa.hubble`.
    """
    EHST_TAP_SERVER = _config.ConfigItem("https://hst.esac.esa.int/tap-server/tap", "eHST TAP Server")
    EHST_TARGET_ACTION = _config.ConfigItem("servlet/target-resolver?", "eHST Target Resolver")
    EHST_MESSAGES = _config.ConfigItem("notification?action=GetNotifications", "eHST Messages")
    TIMEOUT = 60

    cache_location = os.path.join(paths.get_cache_dir(), 'astroquery/ehst', )


conf = Conf()

from .core import ESAHubble, ESAHubbleClass

__all__ = ['ESAHubble', 'ESAHubbleClass', 'Conf', 'conf']
