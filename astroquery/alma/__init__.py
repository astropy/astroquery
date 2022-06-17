# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
ALMA Archive service.
"""
from astropy import config as _config


# map Service IDs to their ARC hosts
_arc_service_id_map = {
    'almascience.eso.org': 'alma.eu',
    'almascience.nrao.edu': 'alma.na',
    'almascience.nao.ac.jp': 'alma.ea'
}

# separate list of ARC URLs as they each deploy their own IVOA services.
_arc_url_list = [f'https://{id}' for id in _arc_service_id_map]

# list the URLs here separately so they can be used in tests.
_url_list = ['https://almascience.org'] + _arc_url_list

auth_urls = ['asa.alma.cl', 'rh-cas.alma.cl']


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.alma`.
    """

    # Used if the current discovered host has no Service ID equivalent.  This
    # is used when overriding the default registry, which assumes to have
    # just almascience.org as the authority in the Service IDs.
    default_service_id_auth = 'almascience.org'

    service_uri_map = _arc_service_id_map

    registry_path = _config.ConfigItem(
        '/reg/resource-caps',
        'ALMA Registry path')

    tap_service_uri_path = _config.ConfigItem(
        '/tap',
        'ALMA TAP ObsCore service URI path')

    tap_standard_id = _config.ConfigItem(
        'ivo://ivoa.net/std/TAP',
        'ALMA TAP service standard ID')

    datalink_service_uri_path = _config.ConfigItem(
        '/datalink',
        'ALMA DataLink service URI path')

    datalink_standard_id = _config.ConfigItem(
        'ivo://ivoa.net/std/DataLink#links-1.0',
        'ALMA DataLink service standard ID'
    )

    sia_service_uri_path = _config.ConfigItem(
        '/sia',
        'ALMA SIAv2 service URI path')

    sia_standard_id = _config.ConfigItem(
        'ivo://ivoa.net/std/SIA#query-2.0',
        'ALMA SIAv2 service standard ID')

    timeout = _config.ConfigItem(60, "Timeout in seconds.")

    archive_url = _config.ConfigItem(
        _url_list,
        'The ALMA Archive mirror to use.')

    auth_url = _config.ConfigItem(
        auth_urls,
        'ALMA Central Authentication Service URLs'
    )

    username = _config.ConfigItem(
        "",
        'Optional default username for ALMA archive.')


conf = Conf()

from .core import Alma, AlmaClass, ALMA_BANDS

__all__ = ['Alma', 'AlmaClass',
           'Conf', 'conf', 'ALMA_BANDS'
           ]
