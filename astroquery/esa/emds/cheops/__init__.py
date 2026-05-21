"""
==================
Cheops Init
==================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

from astropy import config as _config
from astroquery.esa.emds import Conf as EmdsConf


class Conf(EmdsConf):
    """
    Configuration parameters for Cheops.

    Inherits all EMDS configuration items and adds/overrides only the Cheops ones.
    """

    CHEOPS_OBSERVATION_TABLE = _config.ConfigItem("cheops.observation_request",
                                                      "CHEOPS Observation Table")

    CHEOPS_DATA_PRODUCT_TABLE = _config.ConfigItem("cheops.data_product",
                                                   "CHEOPS Data Product Table")

    CHEOPS_DATA_PRODUCT_QUERY = _config.ConfigItem("select * from cheops.data_product a where a.visit_oid in "
                                                   "(select distinct b.visit_oid from cheops.visit b where {})",
                                                   "CHEOPS Data Product Query")

    DEFAULT_SCHEMAS = _config.ConfigItem("cheops",
                                         "Default TAP schema(s) for this mission (comma-separated) "
                                         "e.g. \"schema1, schema2, schema3\".")

    OBSCORE_TABLE = _config.ConfigItem("",
                                       "Fully-qualified ObsCore table or view name (including schema)")


conf = Conf()

from .core import Cheops, CheopsClass

__all__ = ['Cheops', 'CheopsClass']
