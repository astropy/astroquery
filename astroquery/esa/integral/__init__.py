"""
=========
ISLA Init
=========

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

from astropy import config as _config

ISLA_DOMAIN = 'https://isla.esac.esa.int/tap/'
ISLA_TAP_URL = ISLA_DOMAIN + 'tap'


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esa.integral`.
    """
    ISLA_TAP_SERVER = _config.ConfigItem(ISLA_TAP_URL, "ISLA TAP Server")
    ISLA_DATA_SERVER = _config.ConfigItem(ISLA_DOMAIN + 'data?', "ISLA Data Server")
    ISLA_LOGIN_SERVER = _config.ConfigItem(ISLA_DOMAIN + 'login', "ISLA Login Server")
    ISLA_LOGOUT_SERVER = _config.ConfigItem(ISLA_DOMAIN + 'logout', "ISLA Logout Server")
    ISLA_SERVLET = _config.ConfigItem(ISLA_TAP_URL + "/sync/?PHASE=RUN",
                                      "ISLA Sync Request")
    ISLA_TARGET_RESOLVER = _config.ConfigItem(ISLA_DOMAIN + "servlet/target-resolver?TARGET_NAME={}"
                                                            "&RESOLVER_TYPE={}&FORMAT=json",
                                              "ISLA Target Resolver Request")

    ISLA_INSTRUMENT_BAND_QUERY = _config.ConfigItem('select i.name as instrument, b."name" as band, '
                                                    'i.instrument_oid, b.band_oid from ila.instrument i join '
                                                    'ila.band b using(instrument_oid);',
                                                    "ISLA Instrument Band Query")
    ISLA_EPOCH_TARGET_QUERY = _config.ConfigItem("select distinct epoch from ila.epoch where source_id = '{}' and "
                                                 "(instrument_oid = {} or band_oid = {})",
                                                 "ISLA Epoch Query")
    ISLA_EPOCH_QUERY = _config.ConfigItem("select distinct epoch from ila.epoch where "
                                          "(instrument_oid = {} or band_oid = {})",
                                          "ISLA Epoch Query")
    ISLA_OBSERVATION_BASE_QUERY = _config.ConfigItem("select * from ila.cons_pub_obs",
                                                     "ISLA Observation Base Query")
    ISLA_TARGET_CONDITION = _config.ConfigItem("select distinct src.name, src.ra, src.dec, src.source_id from "
                                               "ila.v_cat_source src where "
                                               "src.name ilike '%{}%' order by src.name asc",
                                               "ISLA Target Condition")
    ISLA_CONE_TARGET_CONDITION = _config.ConfigItem("select distinct src.name, src.ra, src.dec, "
                                                    "src.source_id from ila.v_cat_source src where "
                                                    "1=CONTAINS(POINT('ICRS',src.ra,src.dec),CIRCLE('ICRS',{},{},{}))",
                                                    "ISLA Target Condition")
    ISLA_COORDINATE_CONDITION = _config.ConfigItem("1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',{},{},{}))",
                                                   "ISLA Coordinate Condition")
    TIMEOUT = 60


conf = Conf()

from .core import Integral, IntegralClass

__all__ = ['Integral', 'IntegralClass', 'Conf', 'conf']
