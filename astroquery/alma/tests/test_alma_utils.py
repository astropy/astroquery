# Licensed under a 3-clause BSD style license - see LICENSE.rst
import numpy as np
import pytest
import warnings

from astropy import wcs
from astropy import units as u
try:
    from pyregion.parser_helper import Shape
    pyregion_OK = True
except ImportError:
    pyregion_OK = False

from .. import utils


frq_sup_str = ('[86.26..88.14GHz,976.56kHz, XX YY] U '
               '[88.15..90.03GHz,976.56kHz, XX YY] U '
               '[98.19..100.07GHz,976.56kHz, XX YY] U '
               '[100.15..102.03GHz,976.56kHz, XX YY]')
beamsizes = u.Quantity([72.09546309, 70.56599373, 63.41898902, 62.18937958],
                       unit=u.arcsec)
franges = u.Quantity([[86.26, 88.14], [88.15, 90.03], [98.19, 100.07],
                      [100.15, 102.03]], unit=u.GHz)


def test_parse_frequency_support(frq_sup_str=frq_sup_str, result=franges):
    assert np.all(utils.parse_frequency_support(frq_sup_str) == result)


def approximate_primary_beam_sizes(frq_sup_str=frq_sup_str,
                                   beamsizes=beamsizes):
    assert np.all(utils.approximate_primary_beam_sizes(frq_sup_str) == beamsizes)
