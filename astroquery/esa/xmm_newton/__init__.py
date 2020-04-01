"""

@author: Elena Colomo
@contact: ecolomo@esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 3 Sept. 2019

"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esa.xmm_newton`.
    """
    DATA_ACTION = _config.ConfigItem("http://nxsa.esac.esa.int/"
                                     "nxsa-sl/servlet/data-action?",
                                     "Main url for retriving XSA files")
    DATA_ACTION_AIO = _config.ConfigItem("http://nxsa.esac.esa.int/"
                                         "nxsa-sl/servlet/data-action-aio?",
                                         "Main url for retriving XSA files")
    METADATA_ACTION = _config.ConfigItem("http://nxsa.esac.esa.int/"
                                         "nxsa-sl/servlet/"
                                         "metadata-action?",
                                         "Main url for retriving XSA metadata")
    TIMEOUT = 60


conf = Conf()

from .core import XMMNewton, XMMNewtonClass

__all__ = ['XMMNewton', 'XMMNewtonClass', 'Conf', 'conf']
