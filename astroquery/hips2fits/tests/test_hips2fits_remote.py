# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst
import sys
import pytest

from ..core import hips2fits

from astropy import wcs as astropy_wcs
from astropy.io import fits
import numpy as np

from astropy.utils.exceptions import AstropyUserWarning
from matplotlib.colors import Colormap


@pytest.mark.remote_data
class TestHips2fitsRemote(object):

    # Create a new WCS astropy object
    w = astropy_wcs.WCS(header={
        'NAXIS1': 2000,  # Width of the output fits/image
        'NAXIS2': 1000,  # Height of the output fits/image
        'WCSAXES': 2,  # Number of coordinate axes
        'CRPIX1': 1000.0,  # Pixel coordinate of reference point
        'CRPIX2': 500.0,  # Pixel coordinate of reference point
        'CDELT1': -0.18,  # [deg] Coordinate increment at reference point
        'CDELT2': 0.18,  # [deg] Coordinate increment at reference point
        'CUNIT1': 'deg',                 # Units of coordinate increment and value
        'CUNIT2': 'deg',                 # Units of coordinate increment and value
        'CTYPE1': 'GLON-MOL',            # galactic longitude, Mollweide's projection
        'CTYPE2': 'GLAT-MOL',            # galactic latitude, Mollweide's projection
        'CRVAL1': 0.0,  # [deg] Coordinate value at reference point
        'CRVAL2': 0.0,  # [deg] Coordinate value at reference point
    })
    hips = 'CDS/P/DSS2/red'

    def test_query_jpg(self):
        result = hips2fits.query_with_wcs(
            hips=self.hips,
            wcs=self.w,
            get_query_payload=False,
            format='jpg',
            min_cut=0.5,
            max_cut=99.5,
            cmap=Colormap('viridis'),
        )

        # import matplotlib.cm as cm
        # import matplotlib.pyplot as plt

        # im = plt.imshow(result)
        # plt.show(im)

        # We must get a numpy array with 3 dimensions, and the last one should be of size 3 (RGB)
        assert isinstance(result, np.ndarray) and result.shape[2] == 3

    def test_query_jpg_no_wcs(self):
        from astropy.coordinates import Longitude
        from astropy.coordinates import Latitude
        from astropy.coordinates import Angle
        import astropy.units as u

        result = hips2fits.query(
            hips=self.hips,
            width=1000,
            height=500,
            fov=Angle(20 * u.deg),
            ra=Longitude(0 * u.deg),
            dec=Latitude(20 * u.deg),
            projection="TAN",
            get_query_payload=False,
            format='jpg',
            min_cut=0.5,
            max_cut=99.5,
            cmap=Colormap('viridis'),
        )

        # import matplotlib.cm as cm
        # import matplotlib.pyplot as plt

        # im = plt.imshow(result)
        # plt.show(im)

        # We must get a numpy array with 3 dimensions, and the last one should be of size 3 (RGB)
        assert isinstance(result, np.ndarray) and result.shape[2] == 3

    def test_bad_strech(self):
        with pytest.raises(AttributeError):
            result = hips2fits.query_with_wcs(
                hips=self.hips,
                wcs=self.w,
                get_query_payload=False,
                format='jpg',
                stretch="azs",
                min_cut=0.5,
                max_cut=99.5,
                cmap=Colormap('viridis'),
            )

    def test_query_fits(self):
        result = hips2fits.query_with_wcs(
            hips=self.hips,
            wcs=self.w,
            get_query_payload=False,
        )

        assert isinstance(result, fits.HDUList)

    def test_query_fits(self):
        result = hips2fits.query_with_wcs(
            hips=self.hips,
            wcs=self.w,
            # Here we send additional keywords incompatible with
            # the fits output format
            min_cut=1.5,
            max_cut=96,
            stretch='asinh',
            cmap='twilight',
        )

    def test_query_png(self):
        result = hips2fits.query_with_wcs(
            hips=self.hips,
            wcs=self.w,
            get_query_payload=False,
            format='png'
        )
        # We must get a numpy array with 3 dimensions, and the last one should be of size 4 (RGBA)
        assert isinstance(result, np.ndarray) and result.shape[2] == 4

    def test_bad_format_asked(self):
        with pytest.raises(AttributeError):
            result = hips2fits.query_with_wcs(
                hips=self.hips,
                wcs=self.w,
                get_query_payload=False,
                format='sdfsg'
            )

    def test_wcs_having_no_naxis(self):
        w2 = astropy_wcs.WCS(header={
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

        with pytest.raises(AttributeError):
            result = hips2fits.query_with_wcs(
                hips=self.hips,
                wcs=w2,
                get_query_payload=False,
                format='jpg',
                min_cut=0.5,
                max_cut=99.5,
                cmap=Colormap('viridis'),
            )
