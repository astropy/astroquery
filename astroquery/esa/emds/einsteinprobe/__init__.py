"""
==================
EinsteinProbe Init
==================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

from astropy import config as _config
from astroquery.esa.emds import Conf as EmdsConf

class Conf(EmdsConf):
    """
    Configuration parameters for EinsteinProbe.

    Inherits all EMDS configuration items and adds/overrides only the EinsteinProbe ones.
    """
    DEFAULT_SCHEMA = _config.ConfigItem("einsteinprobe",
                            "Default TAP schema for Einstein Probe")
    OBSCORE_TABLE = _config.ConfigItem("einsteinprobe.obscore_extended",
                                       "Fully-qualified ObsCore table or view name (including schema)")

conf = Conf()

from .core import EinsteinProbe, EinsteinProbeClass

__all__ = ['EinsteinProbe', 'EinsteinProbeClass']
