from astropy.config import ConfigurationItem

SKYVIEW_URL = ConfigurationItem(
    'skyview_url', 'http://skyview.gsfc.nasa.gov/current/cgi/basicform.pl',
    'SkyView URL')

from .core import SkyView, SkyViewClass

__all__ = ['SkyView', 'SkyViewClass']
