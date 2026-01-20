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
    DEFAULT_SCHEMAS = _config.ConfigItem("",
                                         "Default TAP schema(s) used to filter available tables. "
                                         "If empty, no schema-based filtering is applied and all tables are returned. "
                                         "Use a comma-separated list if multiple schemas are required."
                                         "e.g. \"schema1, schema2, schema3\".")
    OBSCORE_TABLE = _config.ConfigItem("ivoa.ObsCore",
                                       "Fully qualified ObsCore table or view name (including schema)")

    TIMEOUT = 60


conf = Conf()

from .core import Emds, EmdsClass

__all__ = ['Emds', 'EmdsClass', 'Conf', 'conf']
