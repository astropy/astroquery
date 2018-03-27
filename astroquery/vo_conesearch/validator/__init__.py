# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os

from astropy import config as _config
from astropy.utils.data import get_pkg_data_contents

__all__ = []


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.vo_conesearch.validator`.
    """
    conesearch_master_list = _config.ConfigItem(
        'http://vao.stsci.edu/directory/NVORegInt.asmx/VOTCapabilityPredOpt?'
        'predicate=1%3D1&capability=conesearch&VOTStyleOption=2',
        'URL to the cone search services master list for validation.')
    conesearch_urls = _config.ConfigItem(
        get_pkg_data_contents(
            os.path.join('data', 'conesearch_urls.txt')).split(),
        'A list of conesearch URLs to validate.', 'list')
    noncritical_warnings = _config.ConfigItem(
        ['W03', 'W06', 'W07', 'W09', 'W10', 'W15', 'W17', 'W20', 'W21', 'W22',
         'W27', 'W28', 'W29', 'W41', 'W42', 'W48', 'W50'],
        'A list of `astropy.io.votable` warning codes that are considered '
        'non-critical.', 'list')


conf = Conf()
