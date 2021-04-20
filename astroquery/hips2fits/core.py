# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ..query import BaseQuery

from ..utils.class_or_instance import class_or_instance
from ..utils import async_to_sync
from . import conf

from astropy import wcs

__all__ = ['hips2fits', 'hips2fitsClass']
__doctest_skip__ = ['hips2fitsClass.*']

import json

# Numpy is used for deserializing the string of bytes
# returned by hips2fits into a valid float32 numpy array
import numpy as np
# astropy.io.fits is used for creating a new HDUList
# from the image data received
from astropy.io import fits
from astropy.coordinates import Angle
import astropy.units as u

# Used for deserializing string of bytes to an image (i.e. a numpy array)
import io
from PIL import Image

from astropy.utils.exceptions import AstropyUserWarning
import warnings


@async_to_sync
class hips2fitsClass(BaseQuery):
    """
    Query the `CDS hips2fits service <http://alasky.u-strasbg.fr/hips-image-services/hips2fits>`_

    The `CDS hips2fits service <http://alasky.u-strasbg.fr/hips-image-services/hips2fits>`_ offers a way
    to extract FITS images from HiPS sky maps. HiPS is an IVOA standard that combines individual images in
    order to produce a progressive hierarchical sky map describing the whole survey. Please refer to the
    `IVOA paper <http://www.ivoa.net/documents/HiPS/20170519/REC-HIPS-1.0-20170519.pdf>`_ for more info.

    Given an astropy user-defined WCS with an HiPS name
    (see the list of valid HiPS names hosted in CDS `here <http://aladin.unistra.fr/hips/list>`_),
    hips2fits will return you the corresponding FITS image (JPG/PNG output formats are also implemented).

    This package implements two methods:

    * :meth:`~astroquery.hips2fits.hips2fitsClass.query_with_wcs` extracting a FITS image from a HiPS and an astropy ``wcs.WCS``.
        See `here <http://aladin.unistra.fr/hips/list>`_ all the valid HiPS names hosted in CDS.
    * :meth:`~astroquery.hips2fits.hips2fitsClass.query` extracting a FITS image from a HiPS given the output image pixel size, the center of projection, the type of projection and the field of view.
        See `here <http://aladin.unistra.fr/hips/list>`_ all the valid HiPS names hosted in CDS.

    """
    server = conf.server
    timeout = conf.timeout

    def __init__(self, *args):
        super(hips2fitsClass, self).__init__()

    def query_with_wcs(self, hips, wcs, format="fits", min_cut=0.5, max_cut=99.5, stretch="linear", cmap="Greys_r", get_query_payload=False, verbose=False):
        """
        Query the `CDS hips2fits service <http://alasky.u-strasbg.fr/hips-image-services/hips2fits>`_ with a astropy WCS.

        Parameters
        ----------
        hips : str
            ID or keyword identifying the HiPS to use.
            If multiple HiPS surveys match, one is chosen randomly.
            See the list of valid HiPS ids hosted by the CDS `here <http://aladin.unistra.fr/hips/list>`_.
        wcs : `~astropy.wcs.WCS`
            An astropy WCS defining the astrometry you wish.
            Alternatively, you can pass lon, lat, fov, coordsys keywords.
        format : str, optional
            Format of the output image.
            Allowed values are fits (default), jpg and png
            In case of jpg or png format, scaling of the pixels value can be controlled with parameters ``min_cut``, ``max_cut`` and ``stretch``
        min_cut : float, optional
            Minimal value considered for contrast adjustment normalization.
            Only applicable to jpg/png output formats.
            Can be given as a percentile value, for example min_cut=1.5%. Default value is 0.5%.
        max_cut : float, optional
            Maximal value considered for contrast adjustment normalization.
            Only applicable to jpg/png output formats.
            Can be given as a percentile value, for example max_cut=97%. Default value is 99.5%.
        stretch : str, optional
            Stretch function used for contrast adjustment.
            Only applicable to jpg/png output formats.
            Possible values are: power, linear, sqrt, log, asinh. Default value is linear.
        cmap : `~matplotlib.colors.Colormap` or str, optional
            Name of the color map.
            Only applicable to jpg/png output formats.
            Any `colormap supported by Matplotlib <https://matplotlib.org/3.1.1/gallery/color/colormap_reference.html>`_ can be specified.
            Default value is Greys_r (grayscale)
        get_query_payload : bool, optional
            If True, returns a dictionary of the query payload instead of the parsed response.
        verbose : bool, optional

        Returns
        -------
        response : `~astropy.io.fits.HDUList` or `~numpy.ndarray`
            Returns an astropy HDUList for fits output format or a 3-dimensional numpy array
            for jpg/png output formats.

        Examples
        --------
        >>> from astroquery.hips2fits import hips2fits
        >>> import matplotlib.pyplot as plt
        >>> from matplotlib.colors import Colormap
        >>> from astropy import wcs as astropy_wcs
        >>> # Create a new WCS astropy object
        >>> w = astropy_wcs.WCS(header={
        ...     'NAXIS1':                 2000,  # Width of the output fits/image
        ...     'NAXIS2':                 1000,  # Height of the output fits/image
        ...     'WCSAXES':                   2,  # Number of coordinate axes
        ...     'CRPIX1':                1000.0, # Pixel coordinate of reference point
        ...     'CRPIX2':                500.0,  # Pixel coordinate of reference point
        ...     'CDELT1':                -0.18,  # [deg] Coordinate increment at reference point
        ...     'CDELT2':                 0.18,  # [deg] Coordinate increment at reference point
        ...     'CUNIT1': 'deg',                 # Units of coordinate increment and value
        ...     'CUNIT2': 'deg',                 # Units of coordinate increment and value
        ...     'CTYPE1': 'GLON-MOL',            # galactic longitude, Mollweide's projection
        ...     'CTYPE2': 'GLAT-MOL',            # galactic latitude, Mollweide's projection
        ...     'CRVAL1':                  0.0,  # [deg] Coordinate value at reference point
        ...     'CRVAL2':                  0.0,  # [deg] Coordinate value at reference point
        ... })
        >>> hips = 'CDS/P/DSS2/red'
        >>> result = hips2fits.query_with_wcs(
        ...    hips=hips,
        ...    wcs=w,
        ...    get_query_payload=False,
        ...    format='jpg',
        ...    min_cut=0.5,
        ...    max_cut=99.5,
        ...    cmap=Colormap('viridis'),
        ... )
        >>> im = plt.imshow(result)
        >>> plt.show(im)
        """
        response = self.query_with_wcs_async(get_query_payload, hips=hips, wcs=wcs, format=format, min_cut=min_cut, max_cut=max_cut, stretch=stretch, cmap=cmap)

        if get_query_payload:
            return response

        result = self._parse_result(response, verbose=verbose, format=format)
        return result

    @class_or_instance
    def query_with_wcs_async(self, get_query_payload=False, **kwargs):
        request_payload = self._args_to_payload(**kwargs)

        # primarily for debug purposes, but also useful if you want to send
        # someone a URL linking directly to the data
        if get_query_payload:
            return request_payload

        response = self._request(
            method="GET",
            url=self.server,
            data=kwargs.get('data', None),
            cache=False,
            timeout=self.timeout,
            params=request_payload
        )

        return response

    def query(self, hips, width, height, projection, ra, dec, fov, coordsys="icrs", rotation_angle=Angle(0 * u.deg), format="fits", min_cut=0.5, max_cut=99.5, stretch="linear", cmap="Greys_r", get_query_payload=False, verbose=False):
        """
        Query the `CDS hips2fits service <http://alasky.u-strasbg.fr/hips-image-services/hips2fits>`_.

        If you have not any WCS, you can call this method by passing:
        * The width/height size of the output pixel image
        * The center of projection in world coordinates (ra, dec)
        * The fov angle in world coordinates
        * The rotation angle of the projection
        * The name of the projection. All `astropy projections <https://docs.astropy.org/en/stable/wcs/#supported-projections>`_ are supported:

        Parameters
        ----------
        hips : str
            ID or keyword identifying the HiPS to use.
            If multiple HiPS surveys match, one is chosen randomly.
            See the list of valid HiPS ids hosted by the CDS `here <http://aladin.unistra.fr/hips/list>`_.
        width : int
            Width in pixels of the output image.
        height : int
            Height in pixels of the output image.
        projection : str
            Name of the requested projection, eg: SIN, TAN, MOL, AIT, CAR, CEA, STG	Compulsory if wcs is not provided.
            See `this page <https://docs.astropy.org/en/stable/wcs/#supported-projections>`_ for an exhaustive list.
        fov : `~astropy.coordinates.Angle`
            Size (FoV) of the cutout on the sky.
            This is the size of the largest dimension of the image.
        ra : `~astropy.coordinates.Longitude`
            Right ascension of the center of the output image.
        dec : `~astropy.coordinates.Latitude`
            Declination of the center of the output image.
        coordsys : str, optional
            Coordinate frame system to be used for the projection
            Possible values are icrs or galactic.
            Default value is icrs.
        rotation_angle : `~astropy.coordinates.Angle`, optional
            Angle value to be applied to the projection
            Default value is ``Angle(0 * u.deg)``
        format : str, optional
            Format of the output image.
            Allowed values are fits (default), jpg and png
            In case of jpg or png format, scaling of the pixels value can be controlled with parameters ``min_cut``, ``max_cut`` and ``stretch``
        min_cut : float, optional
            Minimal value considered for contrast adjustment normalization.
            Only applicable to jpg/png output formats.
            Can be given as a percentile value, for example min_cut=1.5%. Default value is 0.5%.
        max_cut : float, optional
            Maximal value considered for contrast adjustment normalization.
            Only applicable to jpg/png output formats.
            Can be given as a percentile value, for example max_cut=97%. Default value is 99.5%.
        stretch : str, optional
            Stretch function used for contrast adjustment.
            Only applicable to jpg/png output formats.
            Possible values are: power, linear, sqrt, log, asinh. Default value is linear.
        cmap : `~matplotlib.colors.Colormap` or str, optional
            Name of the color map.
            Only applicable to jpg/png output formats.
            Any `colormap supported by Matplotlib <https://matplotlib.org/3.1.1/gallery/color/colormap_reference.html>`_ can be specified.
            Default value is Greys_r (grayscale)
        get_query_payload : bool, optional
            If True, returns a dictionary of the query payload instead of the parsed response.
        verbose : bool, optional

        Returns
        -------
        response : `~astropy.io.fits.HDUList` or `~numpy.ndarray`
            Returns an astropy HDUList for fits output format or a 3-dimensional numpy array
            for jpg/png output formats.

        Examples
        --------
        >>> from astroquery.hips2fits import hips2fits
        >>> import matplotlib.pyplot as plt
        >>> from matplotlib.colors import Colormap
        >>> import astropy.units as u
        >>> from astropy.coordinates import Longitude, Latitude, Angle
        >>> hips = 'CDS/P/DSS2/red'
        >>> result = hips2fits.query(
        ...    hips=hips,
        ...    width=1000,
        ...    height=500,
        ...    ra=Longitude(0 * u.deg),
        ...    dec=Latitude(20 * u.deg),
        ...    fov=Angle(80 * u.deg),
        ...    projection="TAN",
        ...    get_query_payload=False,
        ...    format='jpg',
        ...    min_cut=0.5,
        ...    max_cut=99.5,
        ...    cmap=Colormap('viridis'),
        ... )
        >>> im = plt.imshow(result)
        >>> plt.show(im)
        """

        response = self.query_async(get_query_payload, hips=hips, width=width, height=height, projection=projection, ra=ra, dec=dec, fov=fov, coordsys=coordsys, rotation_angle=rotation_angle, format=format, min_cut=min_cut, max_cut=max_cut, stretch=stretch, cmap=cmap)

        if get_query_payload:
            return response

        result = self._parse_result(response, verbose=verbose, format=format)
        return result

    @class_or_instance
    def query_async(self, get_query_payload=False, **kwargs):
        request_payload = self._args_to_payload(**kwargs)

        # primarily for debug purposes, but also useful if you want to send
        # someone a URL linking directly to the data
        if get_query_payload:
            return request_payload

        response = self._request(
            method="GET",
            url=self.server,
            data=kwargs.get('data', None),
            cache=False,
            timeout=self.timeout,
            params=request_payload
        )

        return response

    def _parse_result(self, response, verbose, format):
        # Parse the json string result
        if response.status_code != 200:
            # Error code status
            content = response.json()
            # Print a good user message based on what the
            # server returned
            # The server returns a dict with two items:
            # - The title of the error
            # - A little description of the error
            msg = content['title']
            if 'description' in content.keys():
                msg += ': ' + content['description'] + '\n'

            raise AttributeError(msg)
        else:
            # The request succeeded
            bytes_str = response.content
            # Check the format. At this point, we are sure
            # that the format is correct i.e. either, fits, jpg or png
            if format == 'fits':
                hdul = fits.HDUList.fromstring(bytes_str)
                return hdul
            else:
                # jpg/png formats
                bytes = io.BytesIO(bytes_str)
                im = Image.open(bytes)
                data = np.asarray(im)
                return data

    def _args_to_payload(self, **kwargs):
        # Convert arguments to a valid requests payload
        # Build the payload
        payload = {}

        # If a wcs is still present in the kwargs it means
        # the user called query_with_wcs
        if kwargs.get('wcs'):
            wcs = kwargs.pop('wcs')
            header = wcs.to_header()

            # hips2fits needs the size of the output image
            if wcs.pixel_shape is not None:
                nx, ny = wcs.pixel_shape
                header['NAXIS1'] = nx
                header['NAXIS2'] = ny
            else:
                # The wcs does not contain the size of the image
                raise AttributeError("""The WCS passed does not contain the size of the pixel image.
                Please add it to the WCS or refer to the query method.""")

            # Add the WCS to the payload
            header_json = dict(header.items())
            header_str = json.dumps(header_json)
            payload.update({'wcs': header_str})
        else:
        # The user called query
            payload.update({
                'width': kwargs.pop("width"),
                'height': kwargs.pop("height"),
                'projection': kwargs.pop("projection"),
                'coordsys': kwargs.pop("coordsys"),
                'rotation_angle': kwargs.pop("rotation_angle").to_value(u.deg),
                'ra': kwargs.pop("ra").to_value(u.deg),
                'dec': kwargs.pop("dec").to_value(u.deg),
                'fov': kwargs.pop("fov").to_value(u.deg),
            })

        # Min-cut
        min_cut_value = kwargs.pop('min_cut')
        min_cut_kw = str(min_cut_value) + '%'
        payload.update({'min_cut': min_cut_kw})

        # Max-cut
        max_cut_value = kwargs.pop('max_cut')
        max_cut_kw = str(max_cut_value) + '%'
        payload.update({'max_cut': max_cut_kw})

        # Colormap
        cmap = kwargs.pop('cmap')
        from matplotlib.colors import Colormap
        if isinstance(cmap, Colormap):
            cmap = cmap.name
        payload.update({'cmap': cmap})

        # Stretch
        stretch = kwargs.pop('stretch')
        # TODO remove that: it must be handled properly by the server side
        # that should return a json error
        if stretch not in ('power', 'linear', 'sqrt', 'log', 'asinh'):
            msg = "stretch: must either 'power', 'linear', 'sqrt', 'log' or 'asinh'.\n"
            msg += str(stretch) + ' is ignored.'

            warnings.warn(msg, AstropyUserWarning)
        else:
            payload.update({'stretch': stretch})
        payload.update({'stretch': stretch})

        # HiPS
        hips = kwargs.pop("hips")
        # Output format
        format = kwargs.pop("format")
        payload.update({
            "hips": hips,
            "format": format,
        })

        # Check that all the arguments have been handled
        assert kwargs == {}

        return payload


hips2fits = hips2fitsClass()
