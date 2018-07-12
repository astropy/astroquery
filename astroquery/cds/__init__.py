# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
astroquery.cds package
-------------------------
:author: Matthieu Baumann (matthieu.baumann@astro.unistra.fr)
"""

from astropy import config as _config

from .output_format import OutputFormat
from .constraints import Constraints
from .properties_constraint import PropertiesConstraint


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for ``astroquery.template_module``.
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
           'Constraints',
           'PropertiesConstraint',
           'Conf', 'conf',
           ]
