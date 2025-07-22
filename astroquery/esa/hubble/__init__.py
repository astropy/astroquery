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

EHST_COMMON_SERVER = "https://hst.esac.esa.int/tap-server/"
EHST_TAP_COMMON = "tap"


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esa.hubble`.
    """
    EHST_DOMAIN_SERVER = _config.ConfigItem(EHST_COMMON_SERVER, "eHST TAP Common Server")
    EHST_TAP_SERVER = _config.ConfigItem(EHST_COMMON_SERVER + EHST_TAP_COMMON, "eHST TAP Server")
    EHST_DATA_SERVER = _config.ConfigItem(EHST_COMMON_SERVER + 'data?', "eHST Data Server")
    EHST_TABLES_SERVER = _config.ConfigItem(EHST_COMMON_SERVER + EHST_TAP_COMMON + "/tables", "eHST TAP Common Server")
    EHST_TARGET_ACTION = _config.ConfigItem("servlet/target-resolver?", "eHST Target Resolver")
    EHST_MESSAGES = _config.ConfigItem("notification?action=GetNotifications", "eHST Messages")
    TIMEOUT = 60

    cache_location = os.path.join(paths.get_cache_dir(), 'astroquery/ehst', )


conf = Conf()

from .core import ESAHubble, ESAHubbleClass

__all__ = ['ESAHubble', 'ESAHubbleClass', 'Conf', 'conf']
