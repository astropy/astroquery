# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
==========
eJWST Init
==========

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""


from astropy import config as _config
from astropy.config import paths
import os

JWST_COMMON_SERVER = "https://jwst.esac.esa.int/server/"
JWST_TAP_COMMON = "tap"

class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esa.jwst`.
    """

    JWST_DOMAIN_SERVER = _config.ConfigItem(JWST_COMMON_SERVER, "eJWST TAP Common Server")

    JWST_TAP_SERVER = _config.ConfigItem(JWST_COMMON_SERVER + JWST_TAP_COMMON, "eJWST TAP Server")

    JWST_DATA_SERVER = _config.ConfigItem(JWST_COMMON_SERVER + 'data?', "eJWST Data Server")

    JWST_TABLES_SERVER = _config.ConfigItem(JWST_COMMON_SERVER + JWST_TAP_COMMON + "/tables", "eJWST TAP Common Server")

    JWST_TARGET_ACTION = _config.ConfigItem("servlet/target-resolver?", "eJWST Target Resolver")

    JWST_MESSAGES = _config.ConfigItem("notification?action=GetNotifications", "JWST Messages")

    JWST_UPLOAD = _config.ConfigItem(JWST_COMMON_SERVER + 'Upload', 'eJWST Upload Server')

    TIMEOUT = 60

    cache_location = os.path.join(paths.get_cache_dir(), 'astroquery/jwst',)

    JWST_LOGIN_SERVER = _config.ConfigItem(JWST_COMMON_SERVER + 'login', "eJWST Login Server")
    JWST_LOGOUT_SERVER = _config.ConfigItem(JWST_COMMON_SERVER + 'logout', "eJWST Logout Server")

    JWST_TOKEN = _config.ConfigItem("jwstToken", "eJWST token")

    JWST_MAIN_TABLE = _config.ConfigItem("jwst.main", "JWST main table, combination of observation and plane tables.")

    JWST_MAIN_TABLE_RA = _config.ConfigItem("target_ra", "Name of RA parameter in table")

    JWST_MAIN_TABLE_DEC = _config.ConfigItem("target_dec", "Name of Dec parameter in table")

    JWST_ARTIFACT_TABLE = _config.ConfigItem("jwst.artifact", "JWST artifacts (data files) table.")

    JWST_OBSERVATION_TABLE = _config.ConfigItem("jwst.observation", "JWST observation table")

    JWST_PLANE_TABLE = _config.ConfigItem("jwst.plane", "JWST plane table")

    JWST_OBS_MEMBER_TABLE = _config.ConfigItem("jwst.observationmember", "JWST observation member table")

    JWST_OBSERVATION_TABLE_RA = _config.ConfigItem("targetposition_coordinates_cval1",
                                                   "Name of RA parameter "
                                                   "in table")

    JWST_OBSERVATION_TABLE_DEC = _config.ConfigItem("targetposition_coordinates_cval2",
                                                    "Name of Dec parameter "
                                                    "in table")

    JWST_ARCHIVE_TABLE = _config.ConfigItem("jwst.archive", "JWST archive table")


conf = Conf()

from .core import Jwst, JwstClass

__all__ = ['Jwst', 'JwstClass', 'Conf', 'conf']
