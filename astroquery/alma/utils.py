"""
Utilities for making finder charts and overlay images for ALMA proposing
"""
import string

from astropy import units as u
from astropy.coordinates import SkyCoord

__all__ = ['parse_frequency_support', 'footprint_to_reg', 'approximate_primary_beam_sizes']


def parse_frequency_support(frequency_support_str):
    """
    ALMA "Frequency Support" strings have the form:

    [100.63..101.57GHz,488.28kHz, XX YY] U
    [102.43..103.37GHz,488.28kHz, XX YY] U
    [112.74..113.68GHz,488.28kHz, XX YY] U
    [114.45..115.38GHz,488.28kHz, XX YY]

    at least, as far as we have seen.  The "U" is meant to be the Union symbol.
    This function will parse such a string into a list of pairs of astropy
    Quantities representing the frequency range.  It will ignore the resolution
    and polarizations.
    """
    if not isinstance(frequency_support_str, str):
        supports = frequency_support_str.tostring().decode('ascii').split('U')
    else:
        supports = frequency_support_str.split('U')

    freq_ranges = [(float(sup[0]),
                    float(sup[1].split(',')[0].strip(string.ascii_letters)))
                   * u.Unit(sup[1].split(',')[0].strip(string.punctuation + string.digits))
                   for i in supports for sup in [i.strip('[] ').split('..'), ]]
    return u.Quantity(freq_ranges)


def footprint_to_reg(footprint):
    """
    ALMA footprints have the form:
    'Polygon ICRS 266.519781 -28.724666 266.524678 -28.731930 266.536683
    -28.737784 266.543860 -28.737586 266.549277 -28.733370 266.558133
    -28.729545 266.560136 -28.724666 266.558845 -28.719605 266.560133
    -28.694332 266.555234 -28.687069 266.543232 -28.681216 266.536058
    -28.681414 266.530644 -28.685630 266.521788 -28.689453 266.519784
    -28.694332 266.521332 -28.699778'
    Some of them have *additional* polygons
    """

    if footprint[:7] != 'Polygon' and footprint[:6] != 'Circle':
        raise ValueError("Unrecognized footprint type")

    try:
        import regions
    except ImportError:
        print('Could not import `regions`, which is required for the '
              'functionality of this function.')
        raise

    reglist = []

    meta = {'source': 1, 'include': 1, 'fixed': 0, 'text': ''}
    visual = {'color': 'green', 'dash': '0', 'dashlist': '8 3',
              'font': '"helvetica 10 normal roman"', 'width': '1'}

    entries = footprint.split()
    if entries[0] == 'Circle':
        center = SkyCoord(float(entries[2]), float(entries[3]), frame='icrs', unit=(u.deg, u.deg))
        reg = regions.CircleSkyRegion(center, radius=float(entries[4])*u.deg,
                                      meta=meta, visual=visual)
        reglist.append(reg)

    else:
        polygons = [index for index, entry in enumerate(entries) if entry == 'Polygon']

        for start, stop in zip(polygons, polygons[1:]+[len(entries)]):
            start += 1
            ra = [float(x) for x in entries[start+1:stop:2]]*u.deg
            dec = [float(x) for x in entries[start+2:stop:2]]*u.deg
            vertices = SkyCoord(ra, dec, frame='icrs')
            reg = regions.PolygonSkyRegion(vertices=vertices, meta=meta, visual=visual)
            reglist.append(reg)

    return reglist


def approximate_primary_beam_sizes(frequency_support_str,
                                   dish_diameter=12 * u.m, first_null=1.220):
    r"""
    Using parse_frequency_support, determine the mean primary beam size in each
    observed band

    Parameters
    ----------
    frequency_support_str : str
        The frequency support string, see `parse_frequency_support`
    dish_diameter : `~astropy.units.Quantity`
        Meter-equivalent unit.  The diameter of the dish.
    first_null : float
        The position of the first null of an Airy.  Used to compute resolution
        as :math:`R = 1.22 \lambda/D`
    """
    freq_ranges = parse_frequency_support(frequency_support_str)
    beam_sizes = [(first_null * fr.mean().to(u.m, u.spectral())
                   / (dish_diameter)).to(u.arcsec, u.dimensionless_angles())
                  for fr in freq_ranges]
    return u.Quantity(beam_sizes)
