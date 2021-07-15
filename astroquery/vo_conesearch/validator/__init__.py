# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os

from astropy import config as _config
from astropy.utils.data import get_pkg_data_contents

__all__ = []


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.vo_conesearch.validator`.
    """
    # http://www.ivoa.net/documents/RegTAP/20171206/WD-RegTAP-1.1-20171206.pdf
    conesearch_master_list = _config.ConfigItem(
        'https://vao.stsci.edu/regtap/tapservice.aspx/sync?lang=adql&'
        'query=SELECT%20*%20FROM%20rr.capability%20'
        'NATURAL%20JOIN%20rr.interface%20NATURAL%20JOIN%20rr.resource%20'
        'NATURAL%20JOIN%20rr.res_subject%20WHERE%20'
        'standard_id%20like%20%27ivo://ivoa.net/std/conesearch%%27AND%20'
        'intf_type=%27vs:paramhttp%27',
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
