"""
Canadian Astronomy Data Centre (CADC).
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.cadc`.
    """

    CADC_REGISTRY_URL = _config.ConfigItem(
        'http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/resource-caps',
        'CADC registry information')
    CADCTAP_SERVICE_URI = _config.ConfigItem('ivo://cadc.nrc.ca/tap',
                                             'CADC TAP service identifier')
    CADCDATLINK_SERVICE_URI = _config.ConfigItem(
        'ivo://cadc.nrc.ca/caom2ops', 'CADC DataLink service identifier')
    CADCLOGIN_SERVICE_URI = _config.ConfigItem(
        'ivo://cadc.nrc.ca/gms', 'CADC login service identified')
    TIMEOUT = _config.ConfigItem(
        30, 'Time limit for connecting to template_module server.')


conf = Conf()

from .core import Cadc, CadcClass  # noqa

__all__ = ['Cadc', 'CadcClass', 'conf']
