"""

@author: Jesus Salgado
@contact: jesusjuansalgado@gmail.com

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 15 July 2020

"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esa.iso`.
    """
    DATA_ACTION = _config.ConfigItem("http://nida.esac.esa.int/nida-sl-tap/data?",
                                     "Main url for retrieving ISO Data Archive files")

    METADATA_ACTION = _config.ConfigItem("http://nida.esac.esa.int/nida-sl-tap/tap/",
                                         "Main url for retrieving ISO Data Archive metadata")

    TIMEOUT = 60


conf = Conf()

from .core import ISO, ISOClass

__all__ = ['ISO', 'ISOClass', 'Conf', 'conf']
