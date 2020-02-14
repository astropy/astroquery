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

    MAIN_GAIA_TABLE = _config.ConfigItem("gaiadr2.gaia_source",
                                         "GAIA source data table")
    MAIN_GAIA_TABLE_RA = _config.ConfigItem("ra",
                                            "Name of RA parameter in table")
    MAIN_GAIA_TABLE_DEC = _config.ConfigItem("dec",
                                             "Name of Dec parameter in table")
    ROW_LIMIT = _config.ConfigItem(50,
                                   "Number of rows to return from database "
                                   "query (set to -1 for unlimited).")


conf = Conf()


from .core import Gaia, GaiaClass


__all__ = ['Gaia', 'GaiaClass', 'Conf', 'conf']
