# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import os
import astropy.units as u
import astropy.coordinates as coord
from astropy.io import fits
from ...query import BaseQuery
from ...utils import commons, prepend_docstr_nosections
from ...process_asyncs import async_to_sync
from . import conf
from ...exceptions import InvalidQueryError
from bs4 import BeautifulSoup

__all__ = ['Thor', 'ThorClass']


@async_to_sync
class ThorClass(BaseQuery):
    URL = conf.server
    TIMEOUT = conf.timeout

    def _args_to_payload(self, coordinates, image_size=1 * u.arcmin):
        """
        Fetches image cutouts from THOR surveys.

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
        """
        request_payload = {}
        request_payload["catalog"] = "thor"
        c = commons.parse_coordinates(coordinates).transform_to('galactic')
        request_payload["x_coord"] = c.lon
        request_payload["y_coord"] = c.lat
        request_payload["coord_type"] = "Galactic"
        request_payload["size_long"] = coord.Angle(image_size).deg
        request_payload["size_lat"] = coord.Angle(image_size).deg
        request_payload["size_type"] = "degrees"
        return request_payload

    @prepend_docstr_nosections("\n" + _args_to_payload.__doc__)
    def get_images_async(self, coordinates, image_size=1 * u.arcmin,
                         get_query_payload=False, **kwargs):
        """
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service
        """
        request_payload = self._args_to_payload(coordinates,
                                                image_size=image_size)
        if get_query_payload:
            return request_payload
        response = self._request("POST", url=self.URL, data=request_payload,
                                 timeout=self.TIMEOUT, verify=False)
        return response

    def _parse_result(self, response, verbose=False):
        """
        """
        soup = BeautifulSoup(response.text)

        links = soup.findAll('a')

        download_link = [x for x in links if x.text == 'Download FITS Files'][0]

        url = download_link.href
        filename = url.split("/")[-1]

        local_filepath = os.path.join(self.cache_location, filename)

        fileobj = self._download_file(url, local_filepath, timeout=self.TIMEOUT)

        return fileobj



Thor = ThorClass()
