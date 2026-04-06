# Licensed under a 3-clause BSD style license - see LICENSE.rst
import warnings

from astropy import config as _config
from astropy.config import paths
from astropy.utils.exceptions import AstropyDeprecationWarning

import os

ESASKY_COMMON_SERVER = "https://sky.esa.int/esasky-tap/"

ESASKY_TAP_COMMON = "tap"


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esasky`.
    """

    ESASKY_DOMAIN_SERVER = _config.ConfigItem(ESASKY_COMMON_SERVER, "ESASky TAP Common Server", alias='urlBase')
    ESASKY_TAP_SERVER = _config.ConfigItem(ESASKY_COMMON_SERVER + ESASKY_TAP_COMMON, "ESASky TAP Server")
    ESASKY_DATA_SERVER = _config.ConfigItem(ESASKY_COMMON_SERVER + 'data?', "ESASky Data Server")
    ESASKY_TABLES_SERVER = _config.ConfigItem(ESASKY_COMMON_SERVER + ESASKY_TAP_COMMON + "/tables",
                                              "ESASky TAP Tables Server")
    ESASKY_TARGET_ACTION = _config.ConfigItem("servlet/target-resolver?", "ESASky Target Resolver")
    ESASKY_MESSAGES = _config.ConfigItem("notification?action=GetNotifications", "ESASky Messages")
    ESASKY_LOGIN_SERVER = _config.ConfigItem(ESASKY_COMMON_SERVER + 'login', "ESASky Login Server")
    ESASKY_LOGOUT_SERVER = _config.ConfigItem(ESASKY_COMMON_SERVER + 'logout', "ESASky Logout Server")
    ESASKY_CONNECTION_TIMEOUT = _config.ConfigItem(1000, 'Time limit for connecting to a data product server.', alias='timeout')
    ESASKY_ROW_LIMIT = _config.ConfigItem(10000, 'Maximum number of rows returned (set to -1 for unlimited).', alias='row_limit')

    @property
    def urlBase(self):
        return self.ESASKY_DOMAIN_SERVER

    @urlBase.setter
    def urlBase(self, value):
        warnings.warn(
            "'urlBase' is deprecated and will be removed in a future version. "
            "Use 'ESASKY_DOMAIN_SERVER' instead.",
            AstropyDeprecationWarning,
            stacklevel=2,
        )
        self.ESASKY_DOMAIN_SERVER = value

    @property
    def timeout(self):
        return self.ESASKY_CONNECTION_TIMEOUT

    @timeout.setter
    def timeout(self, value):
        warnings.warn(
            "'timeout' is deprecated and will be removed in a future version. "
            "Use 'ESASKY_CONNECTION_TIMEOUT' instead.",
            AstropyDeprecationWarning,
            stacklevel=2,
        )
        self.ESASKY_CONNECTION_TIMEOUT = value

    @property
    def row_limit(self):
        return self.ESASKY_ROW_LIMIT

    @row_limit.setter
    def row_limit(self, value):
        warnings.warn(
            "'row_limit' is deprecated and will be removed in a future version. "
            "Use 'ESASKY_ROW_LIMIT' instead.",
            AstropyDeprecationWarning,
            stacklevel=2,
        )
        self.ESASKY_ROW_LIMIT = value

    cache_location = os.path.join(paths.get_cache_dir(), 'astroquery/esasky', )


conf = Conf()

from .core import ESASky, ESASkyClass

__all__ = ['ESASky', 'ESASkyClass',
           'Conf', 'conf',
           ]
