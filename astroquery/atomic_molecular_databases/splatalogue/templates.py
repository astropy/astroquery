# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Template queries modifying the defaults of Splatalogue
"""

from .core import SplatalogueClass

SplatalogueKelvins = SplatalogueClass(energy_max=500, energy_type='eu_k',
                                      energy_levels=['el4'],
                                      line_strengths=['ls4'],
                                      only_NRAO_recommended=True, noHFS=True)
