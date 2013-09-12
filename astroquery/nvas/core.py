# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import re

import astropy.units as u
from astropy.io import fits
from astropy import coordinates as coord
import astropy.utils.data as aud

from ..query import BaseQuery
from ..utils.class_or_instance import class_or_instance
from ..utils import commons
from . import NVAS_SERVER, NVAS_TIMEOUT

__all__ = ["Nvas"]


class Nvas(BaseQuery):
    URL = NVAS_SERVER()
    TIMEOUT = NVAS_TIMEOUT()
    valid_bands = ["all","L","C","X","U","K","Q"]

    band_freqs = {
        "L": (1,2),
        "S": (2,4),
        "C": (4,8),
        "X": (8,12),
        "U": (12,18),
        "K": (18,26.5),
        "Ka": (26.5,40),
        "Q": (30,50),
        "V": (50,75),
        "E": (60,90),
        "W": (75,110),
        "F": (90,140),
        "D": (110,170),
    }

    @class_or_instance
    def get_images(self, coordinates, radius=0.25 * u.arcmin, max_rms=10000,
                   band="all", get_uvfits=False, verbose=True, get_query_payload=False):
        """
        Get an image around a target/ coordinates from the NVAS image archive

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the appropriate
            `astropy.coordinates` object. ICRS coordinates may also be entered as strings
            as specified in the `astropy.coordinates` module.
        radius : str or `astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The appropriate
            `Quantity` object from `astropy.units` may also be used. Defaults to 0.25 arcmin.
        max_rms : float, optional
            Maximum allowable noise level in the image (mJy). Defaults to 10000 mJy.
        band : str, optional
            The band of the image to fetch. Valid bands must be from
            ["all","L","C","X","U","K","Q"]. Defaults to 'all'
        get_uvfits : bool, optional
            Gets the UVfits files instead of the IMfits files when set to `True`.
            Defaults to `False`.
        verbose : bool, optional
            When `True` print out additional messgages. Defaults to `True`.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.

        Returns
        -------
        A list of `astropy.fits.HDUList` objects
        """
        readable_objs = self.get_images_async(coordinates, radius=radius, max_rms=max_rms,
                                              band=band, get_uvfits=get_uvfits, verbose=verbose,
                                              get_query_payload=get_query_payload)
        if get_query_payload:
            return readable_objs

        filelist = []
        for obj in readable_objs:
            with obj as f:
                filelist.append(fits.open(f,ignore_missing_end=True))

        return filelist

    @class_or_instance
    def get_images_async(self, coordinates, radius=0.25 * u.arcmin, max_rms=10000,
                         band="all", get_uvfits=False, verbose=True, get_query_payload=False):
        """
        Serves the same purpose as :meth:`~astroquery.nvas.core.Nvas.get_images` but
        returns a list of file handlers to remote files

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the appropriate
            `astropy.coordinates` object. ICRS coordinates may also be entered as strings
            as specified in the `astropy.coordinates` module.
        radius : str or `astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The appropriate
            `Quantity` object from `astropy.units` may also be used. Defaults to 0.25 arcmin.
        max_rms : float, optional
            Maximum allowable noise level in the image (mJy). Defaults to 10000 mJy.
        band : str, optional
            The band of the image to fetch. Valid bands must be from
            ["all","L","C","X","U","K","Q"]. Defaults to 'all'
        get_uvfits : bool, optional
            Gets the UVfits files instead of the IMfits files when set to `True`.
            Defaults to `False`.
        verbose : bool, optional
            When `True` print out additional messgages. Defaults to `True`.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.

        Returns
        -------
        A list of context-managers that yield readable file-like objects
        """

        image_urls = self.get_image_list(coordinates, radius=radius, max_rms=max_rms,
                                         band=band, get_uvfits=get_uvfits,
                                         get_query_payload=get_query_payload)
        if get_query_payload:
            return image_urls

        if verbose:
            print("{num} images found.".format(num=len(image_urls)))

        return [aud.get_readable_fileobj(U) for U in image_urls]

    @class_or_instance
    def get_image_list(self, coordinates, radius=0.25 * u.arcmin, max_rms=10000,
                       band="all", get_uvfits=False, get_query_payload=False):
        """
        Function that returns a list of urls from which to download the FITS images.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the appropriate
            `astropy.coordinates` object. ICRS coordinates may also be entered as strings
            as specified in the `astropy.coordinates` module.
        radius : str or `astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The appropriate
            `Quantity` object from `astropy.units` may also be used. Defaults to 0.25 arcmin.
        max_rms : float, optional
            Maximum allowable noise level in the image (mJy). Defaults to 10000 mJy.
        band : str, optional
            The band of the image to fetch. Valid bands must be from
            ["all","L","C","X","U","K","Q"]. Defaults to 'all'
        get_uvfits : bool, optional
            Gets the UVfits files instead of the IMfits files when set to `True`.
            Defaults to `False`.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.

        Returns
        -------
        list of image urls

        """
        if band.upper() not in Nvas.valid_bands and band != 'all':
            raise ValueError("'band' must be one of {!s}".format(Nvas.valid_bands))
        request_payload = {}
        request_payload["nvas_pos"] = _parse_coordinates(coordinates)
        request_payload["nvas_rad"] = _parse_radius(radius)
        request_payload["nvas_rms"] = max_rms
        request_payload["nvas_scl"] = "yes"
        request_payload["submit"] = "Search"
        request_payload["nvas_bnd"] = "" if band == "all" else band.upper()
        if get_query_payload:
            return request_payload
        response = commons.send_request(Nvas.URL, request_payload, Nvas.TIMEOUT)
        image_urls = self.extract_image_urls(response.content, get_uvfits=get_uvfits)
        return image_urls

    @class_or_instance
    def extract_image_urls(self, html_in, get_uvfits=False):
        """
        Helper function that uses reges to extract the image urls from the given HTML.

        Parameters
        ----------
        html_in : str
            source from which the urls are to be extracted.
        get_uvfits : bool, optional
            Gets the UVfits files instead of the IMfits files when set to `True`.
            Defaults to `False`.

        Returns
        -------
        image_urls : list
            The list of URLS extracted from the input.
        """
        imfits_re = re.compile("http://[^\"]*\\.imfits")
        uvfits_re = re.compile("http://[^\"]*\\.uvfits")
        if get_uvfits:
            image_urls = uvfits_re.findall(html_in)
        else:
            image_urls = imfits_re.findall(html_in)
        return image_urls


def _parse_coordinates(coordinates):
    """
    Helper function to parse the entered coordinates in form expected by NVAS

    Parameters
    ----------
    coordinates : str or `astropy.coordinates` object
        The target around which to search. It may be specified as a string
        in which case it is resolved using online services or as the appropriate
        `astropy.coordinates` object. ICRS coordinates may also be entered as strings
        as specified in the `astropy.coordinates` module.

    Returns
    -------
    radecstr : str
        The formatted coordinates as string

    """
    c = commons.parse_coordinates(coordinates)
    # numpy 1.5 returns an object array, so we need to force it to a pair of strings
    # numpy 1.6, 1.7 apparently return string arrays and concatenate without issue
    radecstr = str(c.icrs.ra.format(u.hour, sep=" ")) + " " + str(c.icrs.dec.format(sep=" ", alwayssign=True))
    return radecstr


def _parse_radius(radius):
    """
    Parses the radius and returns it in the format expected by UKIDSS.

    Parameters
    ----------
    radius : str, `astropy.units.Quantity`

    Returns
    -------
    radius_in_min : float
        The value of the radius in arcminutes.
    """
    if isinstance(radius, u.Quantity) and radius.unit in u.deg.find_equivalent_units():
        radius_in_min = commons.radius_to_unit(radius, u.arcmin)
    # otherwise must be an Angle or be specified in hours...
    else:
        try:
            radius_in_min = commons.radius_to_unit(radius, u.arcmin)
        except (u.UnitsException, coord.errors.UnitsError, AttributeError):
            raise u.UnitsException("Radius not in proper units")
    return radius_in_min
