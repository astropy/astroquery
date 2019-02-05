# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
ehst
=============

@author: Javier Duran
@contact: javier.duran@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 13 Ago. 2018

"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esa_hubble`.
    """
    DATA_ACTION = _config.ConfigItem("http://archives.esac.esa.int/"
                                     "ehst-sl-server/servlet/data-action?",
                                     "Main url for retriving hst files")
    METADATA_ACTION = _config.ConfigItem("http://archives.esac.esa.int/"
                                         "ehst-sl-server/servlet/"
                                         "metadata-action?",
                                         "Main url for retriving hst metadata")
    TIMEOUT = 60


conf = Conf()

from .core import ESAHubble, ESAHubbleClass

__all__ = ['ESAHubble', 'ESAHubbleClass', 'Conf', 'conf']
