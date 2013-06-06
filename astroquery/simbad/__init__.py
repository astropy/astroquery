# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
TODO: add short description
"""
from astropy.config import ConfigurationItem

SIMBAD_SERVER = ConfigurationItem('simbad_server', ['simbad.u-strasbg.fr',
                                                    'simbad.harvard.edu'], 'Name of the SIMBAD mirror to use.')

from .queries import *
from .result import *
from .simbad_votable import *

votabledef = 'main_id, coordinates'
