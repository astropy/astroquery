# Licensed under a 3-clause BSD style license - see LICENSE.rst
from io import BytesIO
import astropy.units as u
import astropy.coordinates as coord
from astropy.io import fits
from ...query import BaseQuery
from ...utils import commons, prepend_docstr_nosections
from . import conf
from ...exceptions import InvalidQueryError

__all__ = ['First', 'FirstClass']


class FirstClass(BaseQuery):
    URL = conf.server
    TIMEOUT = conf.timeout
    maximsize = 1024

    def _args_to_payload(self, coordinates, *, image_size=1 * u.arcmin,
                         maximsize=None):
        """
        Fetches image cutouts from FIRST survey.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `astropy.coordinates` module.
        image_size : str or `~astropy.units.Quantity` object, optional
           The string must be parsable by `astropy.coordinates.Angle`. The
           appropriate `~astropy.units.Quantity` object from `astropy.units`
           may also be used. Specifies the symmetric size of the
           image. Defaults to 1 arcmin.
        maximsize : int, optional
            Specify the maximum image size (in pixels on each dimension) that
            will be returned.  Max is 2048.
        """
        request_payload = {}
        c = commons.parse_coordinates(coordinates).transform_to('icrs')
        ra_dec_str = str(c.ra.hour) + ' ' + str(c.dec.degree)
        request_payload["RA"] = ra_dec_str
        request_payload["Equinox"] = "J2000"
        request_payload["ImageSize"] = coord.Angle(image_size).arcmin
        request_payload["ImageType"] = "FITS File"
        request_payload["MaxImSize"] = self.maximsize if maximsize is None else maximsize
        return request_payload

    @prepend_docstr_nosections("\n" + _args_to_payload.__doc__)
    def get_images(self, coordinates, *, image_size=1 * u.arcmin,
                   get_query_payload=False):
        """
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`

        Returns
        -------
        A list of `~astropy.io.fits.HDUList` objects
        """
        response = self.get_images_async(coordinates, image_size=image_size,
                                         get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        S = BytesIO(response.content)
        try:
            return fits.open(S, ignore_missing_end=True)
        except OSError:
            raise InvalidQueryError(response.content)

    @prepend_docstr_nosections("\n" + _args_to_payload.__doc__)
    def get_images_async(self, coordinates, *, image_size=1 * u.arcmin,
                         get_query_payload=False):
        """
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service
        """
        request_payload = self._args_to_payload(
            coordinates, image_size=image_size)
        if get_query_payload:
            return request_payload
        response = self._request("POST", url=self.URL, data=request_payload,
                                 timeout=self.TIMEOUT)
        return response


First = FirstClass()
