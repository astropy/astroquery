# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
from io import BytesIO
import astropy.units as u
import astropy.coordinates as coord
from astropy.io import fits
from ..query import BaseQuery
from ..utils.docstr_chompers import prepend_docstr_noreturns
from ..utils import commons
from . import conf
from ..exceptions import InvalidQueryError

__all__ = ['Magpis', 'MagpisClass']


class MagpisClass(BaseQuery):
    URL = conf.server
    TIMEOUT = conf.timeout
    surveys = ["gps6",
               "gps6epoch2",
               "gps6epoch3",
               "gps6epoch4",
               "gps20",
               "gps20new",
               "gps90",
               "gpsmsx",
               "gpsmsx2",
               "gpsglimpse36",
               "gpsglimpse45",
               "gpsglimpse58",
               "gpsglimpse80",
               "mipsgal",
               "atlasgal",
               "bolocam"]
    maximsize = 1024

    def _args_to_payload(self, coordinates, image_size=1 * u.arcmin,
                         survey='bolocam', maximsize=None):

        """
        Fetches image cutouts from MAGPIS surveys.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `astropy.coordinates` module.
        radius : str or `~astropy.units.Quantity` object, optional
           The string must be parsable by `astropy.coordinates.Angle`. The
           appropriate `~astropy.units.Quantity` object from `astropy.units`
           may also be used. Specifies the symmetric size of the
           image. Defaults to 1 arcmin.
        survey : str, optional
            The MAGPIS survey you want to cut out. Defaults to
            'bolocam'. The other surveys that can be used can be listed via
            :meth:`~astroquery.magpis.MagpisClass.list_surveys`.
        maximsize : int, optional
            Specify the maximum image size (in pixels on each dimension) that
            will be returned.  Max is 2048.
        """
        request_payload = {}
        request_payload["Survey"] = survey
        c = commons.parse_coordinates(coordinates).transform_to('galactic')
        ra_dec_str = str(c.l.degree) + ' ' + str(c.b.degree)
        request_payload["RA"] = ra_dec_str
        request_payload["Equinox"] = "Galactic"
        request_payload["ImageSize"] = coord.Angle(image_size).to('arcmin').value
        request_payload["ImageType"] = "FITS File"
        request_payload["MaxImSize"] = self.maximsize if maximsize is None else maximsize
        return request_payload

    @prepend_docstr_noreturns("\n" + _args_to_payload.__doc__)
    def get_images(self, coordinates, image_size=1 * u.arcmin,
                   survey='bolocam', get_query_payload=False):
        """
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`

        Returns
        -------
        A list of `astropy.fits.HDUList` objects
        """
        response = self.get_images_async(coordinates, image_size=image_size,
                                         survey=survey,
                                         get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        S = BytesIO(response.content)
        try:
            return fits.open(S, ignore_missing_end=True)
        except IOError:
            raise InvalidQueryError(response.content)

    @prepend_docstr_noreturns("\n" + _args_to_payload.__doc__)
    def get_images_async(self, coordinates, image_size=1 * u.arcmin,
                         survey='bolocam', get_query_payload=False):
        """
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service
        """
        if survey not in self.surveys:
            raise InvalidQueryError("Survey must be one of " +
                                    (",".join(self.list_surveys())))
        request_payload = self._args_to_payload(
            coordinates, image_size=image_size, survey=survey)
        if get_query_payload:
            return request_payload
        response = commons.send_request(self.URL, request_payload,
                                        self.TIMEOUT)
        return response

    def list_surveys(self):
        """Return a list of surveys for MAGPIS"""
        return self.surveys

Magpis = MagpisClass()
