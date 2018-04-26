# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
MocServer
-------------------------
:author: Matthieu Baumann (matthieu.baumann@astro.unistra.fr)
"""

from astropy import config as _config

from .output_format import OutputFormat
from .dataset import Dataset
from .constraints import Constraints
from .spatial_constraints import Cone, Polygon, Moc
from .property_constraint import PropertyConstraint


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.template_module`.
    """
    server = _config.ConfigItem(
        ["http://alasky.unistra.fr/MocServer/query",
         "http://alaskybis.unistra.fr/MocServer/query"],
        'Name of the template_module server to use.')

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to template_module server.')


conf = Conf()

from .core import cds, CdsClass

__all__ = ['cds', 'CdsClass',
           'OutputFormat',
           'Dataset',
           'Constraints',
           'Cone', 'Polygon', 'Moc',
           'PropertyConstraint',
           'Conf', 'conf']
