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


@pytest.mark.skipif('not pyregion_OK')
def test_pyregion_subset():
    header = dict(naxis=2, crpix1=15, crpix2=15, crval1=0.1, crval2=0.1,
                  cdelt1=-1. / 3600, cdelt2=1. / 3600., ctype1='GLON-CAR',
                  ctype2='GLAT-CAR')
    mywcs = wcs.WCS(header)
    # circle with radius 10" at 0.1, 0.1
    shape = Shape('circle', (0.1, 0.1, 10. / 3600.))
    shape.coord_format = 'galactic'
    shape.coord_list = (0.1, 0.1, 10. / 3600.)
    shape.attr = ([], {})
    data = np.ones([40, 40])

    # The following line raises a DeprecationWarning from pyregion, ignore it
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        (xlo, xhi, ylo, yhi), d = utils.pyregion_subset(shape, data, mywcs)

    # sticky note over check-engine light solution... but this problem is too
    # large in scope to address here.  See
    # https://github.com/astropy/astropy/pull/3992
    assert d.sum() >= 313 & d.sum() <= 315  # VERY approximately pi
    np.testing.assert_almost_equal(xlo,
                                   data.shape[0] / 2 - mywcs.wcs.crpix[0] - 1)
    np.testing.assert_almost_equal(xhi,
                                   data.shape[0] - mywcs.wcs.crpix[0] - 1)
    np.testing.assert_almost_equal(ylo,
                                   data.shape[1] / 2 - mywcs.wcs.crpix[1] - 1)
    np.testing.assert_almost_equal(yhi,
                                   data.shape[1] - mywcs.wcs.crpix[1] - 1)


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


@pytest.mark.remote_data
@pytest.mark.skipif('not pyregion_OK')
def test_make_finder_chart():
    import matplotlib
    matplotlib.use('agg')
    if matplotlib.get_backend() != 'agg':
        pytest.xfail("Matplotlib backend was incorrectly set to {0}, could "
                     "not run finder chart test.".format(matplotlib.get_backend()))

    result = utils.make_finder_chart('Eta Carinae', 3 * u.arcmin,
                                     'Eta Carinae')
    image, catalog, hit_mask_public, hit_mask_private = result

    assert len(catalog) >= 6  # down to 6 on Nov 17, 2016
    assert 3 in [int(x) for x in hit_mask_public]
    # Feb 8 2016: apparently the 60s integration hasn't actually been released yet...
    if 3 in hit_mask_public:
        assert hit_mask_public[3][256, 256] >= 30.23
    elif b'3' in hit_mask_public:
        assert hit_mask_public[b'3'][256, 256] >= 30.23
    else:
        raise ValueError("hit_mask keys are not of any known type")
