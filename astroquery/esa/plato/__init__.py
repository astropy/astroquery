"""
==========
PLATO Init
==========

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

from astropy import config as _config

PLATO_DOMAIN = 'https://pax.esac.esa.int/tap/'
PLATO_TAP_URL = PLATO_DOMAIN + 'tap'


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esa.plato`.
    """
    PLATO_TAP_SERVER = _config.ConfigItem(PLATO_TAP_URL, "PLATO TAP Server")
    PLATO_DATA_SERVER = _config.ConfigItem(PLATO_DOMAIN + 'data?', "PLATO Data Server")
    PLATO_LOGIN_SERVER = _config.ConfigItem(PLATO_DOMAIN + 'login', "PLATO Login Server")
    PLATO_LOGOUT_SERVER = _config.ConfigItem(PLATO_DOMAIN + 'logout', "PLATO Logout Server")
    PLATO_SERVLET = _config.ConfigItem(PLATO_TAP_URL + "/sync/?PHASE=RUN",
                                       "plato Sync Request")
    PLATO_TARGET_RESOLVER = _config.ConfigItem(PLATO_DOMAIN + "servlet/target-resolver?TARGET_NAME={}"
                                                              "&RESOLVER_TYPE={}&FORMAT=json",
                                               "PLATO Target Resolver Request")
    PLATO_LOGO = _config.ConfigItem('https://pax.esac.esa.int/plato/assets/images/plato_logo.png', "PLATO logo")

    TIMEOUT = 60


conf = Conf()

from .core import Plato, PlatoClass

__all__ = ['Plato', 'PlatoClass', 'Conf', 'conf']
