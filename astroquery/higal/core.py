# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import json
from six.moves.urllib.parse import urljoin
import io

import astropy.units as u
from astropy import coordinates
import astropy.io.votable as votable
from astropy.table import Table
from astropy.io import fits

from ..query import BaseQuery
from ..utils import commons
from ..utils import prepend_docstr_nosections
from ..utils import async_to_sync
from . import conf

__all__ = ['HiGal', 'HiGalClass']

# declare global variables and constants if any


# Now begin your main class
# should be decorated with the async_to_sync imported previously
@async_to_sync
class HiGalClass(BaseQuery):

    """
    Not all the methods below are necessary but these cover most of the common
    cases, new methods may be added if necessary, follow the guidelines at
    <http://astroquery.readthedocs.io/en/latest/api.html>
    """
    # use the Configuration Items imported from __init__.py to set the URL,
    # TIMEOUT, etc.
    URL = conf.server + "HiGALSearch.jsp"
    TIMEOUT = conf.timeout
    CATALOG_URL = conf.server + "MMCAjaxFunction"
    #https://tools.ssdc.asi.it/MMCAjaxFunction?
    #&mission=Hi-GAL&action=getMMCCatalogData&catalogId=4048&radius=10&ra=281.85238759&dec=-1.93488693&_=1546540568988
    HIGAL_CATALOGS = {'blue': 4047,
                      'red': 4051,
                      'psw': 4050,
                      'pmw': 4049,
                      'plw': 4048,
                     }
    HIGAL_WAVELENGTHS = {'blue': '070',
                         'red': '160',
                         'psw': '250',
                         'pmw': '350',
                         'plw': '500',
                        }

    def query_region_async(self, coordinates, radius,
                           catalog='blue',
                           catalog_query=True,
                           get_query_payload=False, cache=True):
        """
        Queries a region around the specified coordinates.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            coordinates around which to query
        radius : str or `astropy.units.Quantity`.
            the radius of the cone search
        catalog_query : bool
            Query the catalog or the generic search interface?  No parser
            is implemented for the generic search interface yet.
        catalog : 'blue', 'red', 'psw', 'pmw', or 'plw'
            Which HiGal catalog to query.
        get_query_payload : bool, optional
            Just return the dict of HTTP request parameters.
        verbose : bool, optional
            Display VOTable warnings or not.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.
        """
        request_payload = self._args_to_payload(coords=coordinates,
                                                radius=radius,
                                                catalog_id=self.HIGAL_CATALOGS[catalog.lower()],
                                                catalog_query=catalog_query,
                                               )
        if get_query_payload:
            return request_payload

        if catalog_query:
            response = self._request('GET', self.CATALOG_URL, params=request_payload,
                                     timeout=self.TIMEOUT, cache=cache)
        else:
            response = self._request('POST', self.URL, params=request_payload,
                                     timeout=self.TIMEOUT, cache=cache)

        response.raise_for_status()

        return response

    def _args_to_payload(self, coords=None, name=None, radius=10*u.arcmin,
                         catalog_id=None, catalog_query=True, *args, **kwargs):

        if not hasattr(self, '_session_id'):
            # set up session: get cookies
            initial_response = self._request('GET', self.URL, cache=False,
                                             timeout=self.TIMEOUT)
            initial_response.raise_for_status()

            # multiple cookies are returned
            self._session_id = self._session.cookies.values()[1]

            # remove the bad session ID associated with CAS rather
            # than root; this may confuse later download attempts
            for cookie in self._session.cookies:
                if cookie.name == 'JSESSIONID':
                    if cookie.path == '/cas/':
                        self._session.cookies.clear(cookie.domain,
                                                    cookie.path,
                                                    cookie.name)


        if name is not None:
            coords = coordinates.SkyCoord.from_name(name)

        if catalog_query:
            request_payload = {
                'mission':'Hi-GAL',
                'action': 'getMMCCatalogData',
                'catalogId': catalog_id, #[4048-4051
                "radius": "{0}".format(radius.to(u.arcmin).value),
                "ra": coords.fk5.ra.value,
                "dec": coords.fk5.dec.value,
            }
        else:
            # this is the "default" query to the service that produces
            # the cutouts; it's needed by get_images
            request_payload = {
                "coordobjc": "{0} {1}".format(coords.fk5.ra.value,
                                              coords.fk5.dec.value),
                "RA": coords.fk5.ra.value,
                "DEC": coords.fk5.dec.value,
                "coordsType": "RADEC", # or "LB"
                "NameResolverLOCAL": "LOCAL",
                "radius": "arcmin",
                "size": "",
                "radiusInput": "{0}".format(radius.to(u.arcmin).value),
                "radius_all": "{0}".format(radius.to(u.arcmin).value),
                "HIGAL": "HIGAL",
                "catalog": [4047, 4048, 4049, 4050, 4051],
                "catalog_radius_4047": 1.0,
                "catalog_radius_4051": 1.0,
                "catalog_radius_4050": 1.0,
                "catalog_radius_4049": 1.0,
                "catalog_radius_4048": 1.0,
                "resolution": "",
                "sourceString": "",
                "sessionId": self._session_id,
                "editId": "",
            }

        return request_payload

    def _parse_result(self, response, verbose=False):
        jdata = response.json()

        return Table(jdata['aaData'])

    def get_images(self, coordinates, radius, get_query_payload=False,
                   cache=False):
        """
        A query function that searches for image cut-outs around coordinates

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            coordinates around which to query
        radius : str or `astropy.units.Quantity`.
            the radius of the cone search
        get_query_payload : bool, optional
            If true than returns the dictionary of query parameters, posted to
            remote server. Defaults to `False`.

        Returns
        -------
        A list of `astropy.fits.HDUList` objects
        """
        responses = self.get_images_async(coordinates, radius,
                                          get_query_payload=get_query_payload,
                                          cache=cache)
        if get_query_payload:
            return responses
        return [fits.open(io.BytesIO(response.content)) for response in responses]

    @prepend_docstr_nosections(get_images.__doc__)
    def get_images_async(self, coordinates, radius, get_query_payload=False,
                         cache=False):
        """
        Returns
        -------
        A list of context-managers that yield readable file-like objects
        """
        image_urls = self.get_image_list(coordinates, radius,
                                         get_query_payload=get_query_payload)
        if get_query_payload:
            return image_urls

        responses = []
        for url in image_urls:
            response = self._request('GET', url, timeout=self.TIMEOUT,
                                     cache=cache)
            response.raise_for_status()
            responses.append(response)

        return responses

    @prepend_docstr_nosections(get_images.__doc__)
    def get_image_list(self, coordinates, radius, get_query_payload=False,
                       cache=True):
        """
        Returns
        -------
        list of image urls
        """
        if get_query_payload:
            return {}

        base_response = self.query_region_async(coordinates=coordinates,
                                                radius=radius,
                                                catalog_query=False,
                                                cache=False,
                                               )
        base_response.raise_for_status()

        lines = base_response.text.split("\n")
        dataline = [line for line in lines if 'fitsHeaders = JSON.parse(\'' in line][0]

        json_data = dataline.split('fitsHeaders = JSON.parse(\'')[1].strip('\');')

        jdict = json.loads(json_data)
        filenames = {wlname: jdict[str(wlnum)]['FILENAME']
                     for wlname, wlnum in self.HIGAL_CATALOGS.items()
                     if str(wlnum) in jdict}

        image_list = [urljoin(conf.server,
                              filenames[wlname].replace('jpeg', 'fits'))
                      for wlname in self.HIGAL_CATALOGS
                      if wlname in filenames
                     ]

        return image_list


HiGal = HiGalClass()
