from astropy.config import ConfigurationItem

# TODO: use ConfigItem instead of deprecated ConfigurationItem
XMATCH_URL = ConfigurationItem(
    'xmatch_url', 'http://cdsxmatch.u-strasbg.fr/xmatch/api/v1/sync',
    'xMatch URL', module='astroquery.xmatch')

XMATCH_TIMEOUT = ConfigurationItem(
    'timeout', 60, 'time limit for connecting to xMatch server')

from .core import XMatch, XMatchClass

__all__ = ['XMatch', 'XMatchClass']
