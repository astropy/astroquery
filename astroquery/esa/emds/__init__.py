"""
=========
EMDS Init
=========

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

from astropy import config as _config

EMDS_DOMAIN = 'https://emds.esac.esa.int/service/'
EMDS_TAP_URL = EMDS_DOMAIN + 'tap'


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esa.emds`.
    """
    EMDS_TAP_SERVER = _config.ConfigItem(EMDS_TAP_URL, "EMDS TAP Server")
    EMDS_DATA_SERVER = _config.ConfigItem(EMDS_DOMAIN + 'data?', "EMDS Data Server")
    EMDS_LOGIN_SERVER = _config.ConfigItem(EMDS_DOMAIN + 'login', "EMDS Login Server")
    EMDS_LOGOUT_SERVER = _config.ConfigItem(EMDS_DOMAIN + 'logout', "EMDS Logout Server")
    EMDS_SERVLET = _config.ConfigItem(EMDS_TAP_URL + "/sync/?PHASE=RUN",
                                      "EMDS Sync Request")
    EMDS_TARGET_RESOLVER = _config.ConfigItem(EMDS_DOMAIN + "servlet/target-resolver?TARGET_NAME={}"
                                                            "&RESOLVER_TYPE={}&FORMAT=json",
                                              "EMDS Target Resolver Request")
    DEFAULT_SCHEMA = _config.ConfigItem("ivoa",
                                "Default TAP schema for EMDS")
    OBSCORE_TABLE = _config.ConfigItem("ivoa.ObsCore",
                                       "Fully-qualified ObsCore view/table")

    TIMEOUT = 60


conf = Conf()

from .core import Emds, EmdsClass

__all__ = ['Emds', 'EmdsClass', 'Conf', 'conf']
