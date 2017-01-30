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

from astroquery.gaiatap.tapplus.tap import TapPlus
from astroquery.gaiatap.tapplus.model.job import Job
from astropy import config as _config

class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esasky`.
    """
    pass

conf = Conf()

gaiatap = TapPlus(url="http://gea.esac.esa.int/tap-server/tap", verbose=False)

from .core import GaiaTap, GaiaTapClass

__all__ = ['GaiaTap', 'GaiaTapClass', 'TapPlus', 'Job', 'Conf', 'conf']

