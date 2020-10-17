# Licensed under a 3-clause BSD style license - see LICENSE.rst


import re

import astropy.units as u
from astropy import coordinates as coord

from ..query import BaseQuery
from ..utils import commons
from . import conf

__all__ = ["Nvas", "NvasClass"]


class NvasClass(BaseQuery):
    URL = conf.server
    TIMEOUT = conf.timeout
    valid_bands = ["all", "L", "C", "X", "U", "K", "Q"]

    band_freqs = {
        "L": (1, 2),
        "S": (2, 4),
        "C": (4, 8),
        "X": (8, 12),
        "U": (12, 18),
        "K": (18, 26.5),
        "Ka": (26.5, 40),
        "Q": (30, 50),
        "V": (50, 75),
        "E": (60, 90),
        "W": (75, 110),
        "F": (90, 140),
        "D": (110, 170),
    }

    def get_images(self, coordinates, radius=0.25 * u.arcmin, max_rms=10000,
                   band="all", get_uvfits=False, verbose=True,
                   get_query_payload=False, show_progress=True):
        """
        Get an image around a target/ coordinates from the NVAS image archive.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `astropy.coordinates` module.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.25 arcmin.
        max_rms : float, optional
            Maximum allowable noise level in the image (mJy). Defaults to
            10000 mJy.
        band : str, optional
            The band of the image to fetch. Valid bands must be from
            ["all","L","C","X","U","K","Q"]. Defaults to 'all'
        get_uvfits : bool, optional
            Gets the UVfits files instead of the IMfits files when set to
            `True`.  Defaults to `False`.
        verbose : bool, optional
            When `True` print out additional messages. Defaults to `True`.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`.

        Returns
        -------
        A list of `~astropy.io.fits.HDUList` objects
        """
        readable_objs = self.get_images_async(
            coordinates, radius=radius, max_rms=max_rms,
            band=band, get_uvfits=get_uvfits, verbose=verbose,
            get_query_payload=get_query_payload, show_progress=show_progress)
        if get_query_payload:
            return readable_objs

        filelist = [obj.get_fits() for obj in readable_objs]

        return filelist

    def get_images_async(self, coordinates, radius=0.25 * u.arcmin,
                         max_rms=10000, band="all", get_uvfits=False,
                         verbose=True, get_query_payload=False,
                         show_progress=True):
        """
        Serves the same purpose as `~astroquery.nvas.NvasClass.get_images` but
        returns a list of file handlers to remote files.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `astropy.coordinates` module.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.25 arcmin.
        max_rms : float, optional
            Maximum allowable noise level in the image (mJy). Defaults to
            10000 mJy.
        band : str, optional
            The band of the image to fetch. Valid bands must be from
            ["all","L","C","X","U","K","Q"]. Defaults to 'all'
        get_uvfits : bool, optional
            Gets the UVfits files instead of the IMfits files when set to
            `True`.  Defaults to `False`.
        verbose : bool, optional
            When `True` print out additional messages. Defaults to `True`.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`.

        Returns
        -------
        A list of context-managers that yield readable file-like objects
        """

        image_urls = self.get_image_list(
            coordinates, radius=radius, max_rms=max_rms,
            band=band, get_uvfits=get_uvfits,
            get_query_payload=get_query_payload)
        if get_query_payload:
            return image_urls

        if verbose:
            print("{num} images found.".format(num=len(image_urls)))

        return [commons.FileContainer(U, encoding='binary',
                                      show_progress=show_progress)
                for U in image_urls]

    def get_image_list(self, coordinates, radius=0.25 * u.arcmin,
                       max_rms=10000, band="all", get_uvfits=False,
                       get_query_payload=False):
        """
        Function that returns a list of urls from which to download the FITS
        images.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `astropy.coordinates` module.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.25 arcmin.
        max_rms : float, optional
            Maximum allowable noise level in the image (mJy). Defaults to
            10000 mJy.
        band : str, optional
            The band of the image to fetch. Valid bands must be from
            ["all","L","C","X","U","K","Q"]. Defaults to 'all'
        get_uvfits : bool, optional
            Gets the UVfits files instead of the IMfits files when set to
            `True`.  Defaults to `False`.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`.

        Returns
        -------
        list of image urls

        """
        if band.upper() not in Nvas.valid_bands and band != 'all':
            raise ValueError("'band' must be one of {!s}"
                             .format(Nvas.valid_bands))
        request_payload = {}
        request_payload["nvas_pos"] = _parse_coordinates(coordinates)
        request_payload["nvas_rad"] = coord.Angle(radius).arcmin
        request_payload["nvas_rms"] = max_rms
        request_payload["nvas_scl"] = "yes"
        request_payload["submit"] = "Search"
        request_payload["nvas_bnd"] = "" if band == "all" else band.upper()
        if get_query_payload:
            return request_payload
        response = self._request("POST", url=Nvas.URL, data=request_payload,
                                 timeout=Nvas.TIMEOUT)
        image_urls = self.extract_image_urls(response.text,
                                             get_uvfits=get_uvfits)
        return image_urls

    def extract_image_urls(self, html_in, get_uvfits=False):
        """
        Helper function that uses regexps to extract the image urls from the
        given HTML.

        Parameters
        ----------
        html_in : str
            source from which the urls are to be extracted.
        get_uvfits : bool, optional
            Gets the UVfits files instead of the IMfits files when set to
            `True`.  Defaults to `False`.

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


Nvas = NvasClass()


def _parse_coordinates(coordinates):
    """
    Helper function to parse the entered coordinates in form expected by NVAS

    Parameters
    ----------
    coordinates : str or `astropy.coordinates` object
        The target around which to search. It may be specified as a string
        in which case it is resolved using online services or as the
        appropriate `astropy.coordinates` object. ICRS coordinates may also
        be entered as strings as specified in the `astropy.coordinates`
        module.

    Returns
    -------
    radecstr : str
        The formatted coordinates as string

    """
    c = commons.parse_coordinates(coordinates).transform_to(coord.ICRS)
    # numpy 1.5 returns an object array, so we need to force it to a pair of
    # strings
    # numpy 1.6, 1.7 apparently return string arrays and concatenate
    # without issue hack to deal with variably astropy coordinates API
    hms = c.ra.hms
    dms = c.dec.dms
    radecstr = "%02i %02i %09.6f %+03i %02i %09.6f" % (hms + dms)
    return radecstr
