# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord

try:
    from regions import CircleSkyRegion

    HAS_REGIONS = True
except ImportError:
    HAS_REGIONS = False

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


mosaic_footprint_str = '''Polygon ICRS 266.519781 -28.724666 266.524678 -28.731930 266.536683
    -28.737784 266.543860 -28.737586 266.549277 -28.733370 266.558133
    -28.729545 266.560136 -28.724666 266.558845 -28.719605 266.560133
    -28.694332 266.555234 -28.687069 266.543232 -28.681216 266.536058
    -28.681414 266.530644 -28.685630 266.521788 -28.689453 266.519784
    -28.694332 266.521332 -28.699778'''


@pytest.mark.skipif(not HAS_REGIONS, reason="regions is required")
def test_footprint_to_reg_mosaic(mosaic_footprint_str=mosaic_footprint_str):

    pairs = zip(mosaic_footprint_str.split()[2::2], mosaic_footprint_str.split()[3::2])
    vertices = [SkyCoord(float(ra) * u.deg, float(dec) * u.deg, frame='icrs')
                for ra, dec in pairs]

    reg_output = utils.footprint_to_reg(mosaic_footprint_str)

    assert len(reg_output) == 1

    for vertex in vertices:
        assert vertex in reg_output[0].vertices


@pytest.mark.skipif(not HAS_REGIONS, reason="regions is required")
def test_footprint_to_reg_mosaic_multiple(mosaic_footprint_str=mosaic_footprint_str):

    multiple_mosaic_footprint_str = f"{mosaic_footprint_str} {mosaic_footprint_str}"

    print(multiple_mosaic_footprint_str)

    pairs = zip(mosaic_footprint_str.split()[2::2], mosaic_footprint_str.split()[3::2])
    vertices = [SkyCoord(float(ra) * u.deg, float(dec) * u.deg, frame='icrs')
                for ra, dec in pairs]

    reg_output = utils.footprint_to_reg(multiple_mosaic_footprint_str)

    assert len(reg_output) == 2

    for this_region in reg_output:

        for vertex in vertices:
            assert vertex in this_region.vertices


pointing_footprint_str = 'Circle ICRS 266.519781 -28.724666 0.01'


@pytest.mark.skipif(not HAS_REGIONS, reason="regions is required")
def test_footprint_to_reg_pointing(pointing_footprint_str=pointing_footprint_str):

    ra, dec, rad = pointing_footprint_str.split()[2:]

    center = SkyCoord(float(ra) * u.deg, float(dec) * u.deg, frame='icrs')

    actual_reg = CircleSkyRegion(center, radius=float(rad) * u.deg)

    reg_output = utils.footprint_to_reg(pointing_footprint_str)

    assert len(reg_output) == 1

    assert actual_reg.center.ra == reg_output[0].center.ra
    assert actual_reg.center.dec == reg_output[0].center.dec
    assert actual_reg.radius == reg_output[0].radius
