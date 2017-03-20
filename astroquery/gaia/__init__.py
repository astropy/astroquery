# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
Gaia TAP plus
=============

@author: Juan Carlos Segovia
@contact: juan.carlos.segovia@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 30 jun. 2016


"""

from astroquery.utils.tap.core import TapPlus
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.gaia`.
    """
    pass


conf = Conf()

gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap", verbose=False)

from .core import Gaia, GaiaClass

__all__ = ['Gaia', 'GaiaClass', 'Conf', 'conf']
