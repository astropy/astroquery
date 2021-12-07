# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
==========
eJWST Init
==========

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""


from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esa.jwst`.
    """

    JWST_TAP_SERVER = _config.ConfigItem("https://jwst.esac.esa.int/server/tap", "eJWST TAP Server")
    JWST_DATA_SERVER = _config.ConfigItem("https://jwst.esac.esa.int/server/data?", "eJWST Data Server")
    JWST_TOKEN = _config.ConfigItem("jwstToken", "eJWST token")
    JWST_MESSAGES = _config.ConfigItem("notification?action=GetNotifications", "eJWST Messages")

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


conf = Conf()

from .core import Jwst, JwstClass
from .data_access import JwstDataHandler

__all__ = ['Jwst', 'JwstClass', 'JwstDataHandler', 'Conf', 'conf']
