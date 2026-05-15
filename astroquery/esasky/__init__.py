# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy import config as _config
from astropy.config import paths
from astropy.utils.decorators import deprecated_attribute

import os

ESASKY_COMMON_SERVER = "https://sky.esa.int/esasky-tap/"

ESASKY_TAP_COMMON = "tap"


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esasky`.
    """

    ESASKY_DOMAIN_SERVER = _config.ConfigItem(ESASKY_COMMON_SERVER, "ESASky TAP Common Server",
                                              aliases=['astroquery.esasky.urlBase'])
    ESASKY_TAP_SERVER = _config.ConfigItem(ESASKY_COMMON_SERVER + ESASKY_TAP_COMMON, "ESASky TAP Server")
    ESASKY_DATA_SERVER = _config.ConfigItem(ESASKY_COMMON_SERVER + 'data?', "ESASky Data Server")
    ESASKY_TABLES_SERVER = _config.ConfigItem(ESASKY_COMMON_SERVER + ESASKY_TAP_COMMON + "/tables",
                                              "ESASky TAP Tables Server")
    ESASKY_TARGET_ACTION = _config.ConfigItem("servlet/target-resolver?", "ESASky Target Resolver")
    ESASKY_MESSAGES = _config.ConfigItem("notification?action=GetNotifications", "ESASky Messages")
    ESASKY_LOGIN_SERVER = _config.ConfigItem(ESASKY_COMMON_SERVER + 'login', "ESASky Login Server")
    ESASKY_LOGOUT_SERVER = _config.ConfigItem(ESASKY_COMMON_SERVER + 'logout', "ESASky Logout Server")
    ESASKY_CONNECTION_TIMEOUT = _config.ConfigItem(1000, 'Time limit for connecting to a data product server.',
                                                   aliases=['astroquery.esasky.timeout'])
    ESASKY_ROW_LIMIT = _config.ConfigItem(10000, 'Maximum number of rows returned (set to -1 for unlimited).',
                                          aliases=['astroquery.esasky.row_limit'])

    urlBase = deprecated_attribute(name='urlBase', alternative='ESASKY_DOMAIN_SERVER', since='8.0')
    timeout = deprecated_attribute(name='timeout', alternative='ESASKY_CONNECTION_TIMEOUT', since='8.0')
    row_limit = deprecated_attribute(name='row_limit', alternative='ESASKY_ROW_LIMIT', since='8.0')

    cache_location = os.path.join(paths.get_cache_dir(), 'astroquery/esasky', )


conf = Conf()

from .core import ESASky, ESASkyClass

__all__ = ['ESASky', 'ESASkyClass',
           'Conf', 'conf',
           ]
