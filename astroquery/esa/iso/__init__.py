"""
=====================
ISO Astroquery Module
=====================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esa.iso`.
    """
    DATA_ACTION = _config.ConfigItem("https://nida.esac.esa.int/nida-sl-tap/data?",
                                     "Main url for retrieving ISO Data Archive files")

    METADATA_ACTION = _config.ConfigItem("https://nida.esac.esa.int/nida-sl-tap/tap/",
                                         "Main url for retrieving ISO Data Archive metadata")

    TIMEOUT = 60


conf = Conf()

from .core import ISO, ISOClass

__all__ = ['ISO', 'ISOClass', 'Conf', 'conf']
