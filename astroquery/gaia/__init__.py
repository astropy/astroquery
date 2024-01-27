# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
Gaia TAP plus
=============

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.gaia`.
    """

    MAIN_GAIA_TABLE = _config.ConfigItem("gaiadr3.gaia_source",
                                         "GAIA source data table")
    MAIN_GAIA_TABLE_RA = _config.ConfigItem("ra",
                                            "Name of RA parameter in table")
    MAIN_GAIA_TABLE_DEC = _config.ConfigItem("dec",
                                             "Name of Dec parameter in table")
    ROW_LIMIT = _config.ConfigItem(50,
                                   "Number of rows to return from database "
                                   "query (set to -1 for unlimited).")
    VALID_DATALINK_RETRIEVAL_TYPES = ['EPOCH_PHOTOMETRY',
                                      'XP_CONTINUOUS',
                                      'XP_SAMPLED',
                                      'RVS',
                                      'MCMC_GSPPHOT',
                                      'MCMC_MSC',
                                      'EPOCH_ASTROMETRY',
                                      'RV_EPOCH_SINGLE',
                                      'RV_EPOCH_DOUBLE',
                                      'RVS_EPOCH',
                                      'RVS_TRANSIT']

    VALID_LINKING_PARAMETERS = {'SOURCE_ID', 'TRANSIT_ID', 'IMAGE_ID'}


conf = Conf()


from .core import Gaia, GaiaClass


__all__ = ['Gaia', 'GaiaClass', 'Conf', 'conf']
