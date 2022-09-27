# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy import wcs as astropy_wcs
from matplotlib.colors import Colormap
from astropy.coordinates import Angle, Longitude, Latitude
import astropy.units as u

from ..core import hips2fits


class TestHips2fitsRemote:

    # Create a new WCS astropy object
    w = astropy_wcs.WCS(header={
        'NAXIS1': 2000,         # Width of the output fits/image
        'NAXIS2': 1000,         # Height of the output fits/image
        'WCSAXES': 2,           # Number of coordinate axes
        'CRPIX1': 1000.0,       # Pixel coordinate of reference point
        'CRPIX2': 500.0,        # Pixel coordinate of reference point
        'CDELT1': -0.18,        # [deg] Coordinate increment at reference point
        'CDELT2': 0.18,         # [deg] Coordinate increment at reference point
        'CUNIT1': 'deg',        # Units of coordinate increment and value
        'CUNIT2': 'deg',        # Units of coordinate increment and value
        'CTYPE1': 'GLON-MOL',   # galactic longitude, Mollweide's projection
        'CTYPE2': 'GLAT-MOL',   # galactic latitude, Mollweide's projection
        'CRVAL1': 0.0,          # [deg] Coordinate value at reference point
        'CRVAL2': 0.0,          # [deg] Coordinate value at reference point
    })
    hips = 'CDS/P/DSS2/red'

    def test_query_jpg(self):
        result = hips2fits.query_with_wcs(
            hips=self.hips,
            wcs=self.w,
            get_query_payload=True,
            format='jpg',
            min_cut=0.5,
            max_cut=99.5,
            cmap=Colormap('viridis'),
        )

        # We must get a numpy array with 3 dimensions, and the last one should be of size 3 (RGB)
        assert result["format"] == 'jpg' and result["hips"] == "CDS/P/DSS2/red"

    def test_query_no_wcs_fits(self):
        result = hips2fits.query(
            hips=self.hips,
            get_query_payload=True,
            width=1000,
            height=500,
            fov=Angle(20 * u.deg),
            ra=Longitude(0 * u.deg),
            dec=Latitude(20 * u.deg),
            projection="TAN",
            min_cut=0.5,
            max_cut=99.5,
            cmap=Colormap('viridis'),
        )

        # We must get a numpy array with 3 dimensions, and the last one should be of size 3 (RGB)
        assert result["format"] == 'fits' and result["hips"] == "CDS/P/DSS2/red"
