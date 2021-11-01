# Licensed under a 3-clause BSD style license - see LICENSE.rst


# put all imports organized as shown below
# 1. standard library imports

# 2. third party imports
import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable
from astropy.coordinates import SkyCoord
import requests
from astropy.table import Table, vstack
from astropy.io import fits

import io
import time

# 3. local imports - use relative imports
# commonly required local imports shown below as example
# all Query classes should inherit from BaseQuery.
from ..query import BaseQuery
# has common functions required by most modules
from ..utils import commons
# prepend_docstr is a way to copy docstrings between methods
from ..utils import prepend_docstr_nosections
# async_to_sync generates the relevant query tools from _async methods
from ..utils import async_to_sync
# import configurable items declared in __init__.py
from . import conf

import pyvo as vo
from numpy import pi, cos
# export all the public classes and methods
__all__ = ['LegacySurvey', 'LegacySurveyClass']

# declare global variables and constants if any


# Now begin your main class
# should be decorated with the async_to_sync imported previously
from ..utils.commons import FileContainer


@async_to_sync
class LegacySurveyClass(BaseQuery):

    """
    Not all the methods below are necessary but these cover most of the common
    cases, new methods may be added if necessary, follow the guidelines at
    <http://astroquery.readthedocs.io/en/latest/api.html>
    """
    # use the Configuration Items imported from __init__.py to set the URL,
    # TIMEOUT, etc.
    URL = conf.server
    TIMEOUT = conf.timeout

    # all query methods are implemented with an "async" method that handles
    # making the actual HTTP request and returns the raw HTTP response, which
    # should be parsed by a separate _parse_result method.   The query_object
    # method is created by async_to_sync automatically.  It would look like
    # this:
    """
    def query_object(object_name, get_query_payload=False)
        response = self.query_object_async(object_name,
                                           get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result
    """

    def query_object_async(self, object_name, get_query_payload=False,
                           cache=True, data_release=9):
        """
        This method is for services that can parse object names. Otherwise
        use :meth:`astroquery.template_module.TemplateClass.query_region`.
        Put a brief description of what the class does here.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            This should default to False. When set to `True` the method
            should return the HTTP request parameters as a dict.
        verbose : bool, optional
           This should default to `False`, when set to `True` it displays
           VOTable warnings.
        any_other_param : <param_type>
            similarly list other parameters the method takes

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.

        Examples
        --------
        While this section is optional you may put in some examples that
        show how to use the method. The examples are written similar to
        standard doctests in python.

        """
        # the async method should typically have the following steps:
        # 1. First construct the dictionary of the HTTP request params.
        # 2. If get_query_payload is `True` then simply return this dict.
        # 3. Else make the actual HTTP request and return the corresponding
        #    HTTP response
        # All HTTP requests are made via the `BaseQuery._request` method. This
        # use a generic HTTP request method internally, similar to
        # `requests.Session.request` of the Python Requests library, but
        # with added caching-related tools.

        # See below for an example:

        # first initialize the dictionary of HTTP request parameters
        request_payload = dict()

        # Now fill up the dictionary. Here the dictionary key should match
        # the exact parameter name as expected by the remote server. The
        # corresponding dict value should also be in the same format as
        # expected by the server. Additional parsing of the user passed
        # value may be required to get it in the right units or format.
        # All this parsing may be done in a separate private `_args_to_payload`
        # method for cleaner code.

        #request_payload['object_name'] = object_name
        # similarly fill up the rest of the dict ...

        if get_query_payload:
            return request_payload
        # BaseQuery classes come with a _request method that includes a
        # built-in caching system

        # TODO: implement here http query as needed
        # e.g. I suspect we get files like this one: https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/tractor/000/tractor-0001m002.fits
        # to confirm with AG, AN
        # if so:
         
        URL = f"{self.URL}/dr{data_release}/north/tractor/000/tractor-0001m002.fits"

        response = self._request('GET', URL, params={},
                                 timeout=self.TIMEOUT, cache=cache)
        return response

    def query_brick_list_async(self, data_release=9, get_query_payload=False, emisphere="north",
                           cache=True):
        """

        """
        request_payload = dict()

        if get_query_payload:
            return request_payload
        URL = f"{self.URL}/dr{data_release}/{emisphere}/survey-bricks-dr{data_release}-{emisphere}.fits.gz"
        # TODO make it work with the original request
        # response = self._request('GET', URL, params={},
        #                          timeout=self.TIMEOUT, cache=cache)

        response = requests.get(URL)

        print("completed fits file request")

        return response

    # For services that can query coordinates, use the query_region method.
    # The pattern is similar to the query_object method. The query_region
    # method also has a 'radius' keyword for specifying the radius around
    # the coordinates in which to search. If the region is a box, then
    # the keywords 'width' and 'height' should be used instead. The coordinates
    # may be accepted as an `astropy.coordinates` object or as a string, which
    # may be further parsed.

    # similarly we write a query_region_async method that makes the
    # actual HTTP request and returns the HTTP response

    def query_region_async(self, coordinates, radius,
                           get_query_payload=False, cache=True, data_release=9, use_tap=True):
        """
        Queries a region around the specified coordinates.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            coordinates around which to query
        radius : str or `astropy.units.Quantity`.
            the radius of the cone search
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

        if use_tap:
            # TAP query
            # Download tractor catalogue
            url = 'https://datalab.noirlab.edu/tap'
            tap_service = vo.dal.TAPService(url)
            qstr = "SELECT all * FROM ls_dr" + str(data_release) + ".tractor WHERE dec>" + str(coordinates.dec.deg - radius.deg) + " and dec<" + str(
                coordinates.dec.deg + radius.deg) + " and ra>" + str(coordinates.ra.deg - radius.deg / cos(coordinates.dec.deg * pi / 180.)) + " and ra<" + str(
                coordinates.ra.deg + radius.deg / cos(coordinates.dec.deg * pi / 180))

            tap_result = tap_service.run_sync(qstr)
            tap_result = tap_result.to_table()
            # filter out duplicated lines from the table
            mask = tap_result['type'] != 'D'
            filtered_table = tap_result[mask]

            return filtered_table
        else:
            # call the brick list
            table_north = self.query_brick_list(data_release=data_release, emisphere="north")
            table_south = self.query_brick_list(data_release=data_release, emisphere="south")
            # needed columns: ra1, ra2, dec1, dec2 (corners of the bricks), and also brickname
            # radius not used for the moment, but it will be in the future
            # must find the brick within ra1 and ra2
            dec = coordinates.dec.deg
            ra = coordinates.ra.deg

            responses = []

            # north table extraction
            brick_name = table_north['brickname']
            ra1 = table_north['ra1']
            dec1 = table_north['dec1']
            ra2 = table_north['ra2']
            dec2 = table_north['dec2']

            corners1 = SkyCoord(ra1, dec1, unit="deg")
            corners2 = SkyCoord(ra1, dec2, unit="deg")
            corners3 = SkyCoord(ra2, dec1, unit="deg")
            corners4 = SkyCoord(ra2, dec2, unit="deg")

            sep1 = coordinates.separation(corners1)
            sep2 = coordinates.separation(corners2)
            sep3 = coordinates.separation(corners3)
            sep4 = coordinates.separation(corners4)

            t0 = time.time()
            print("Beginning processing bricks northern emishpere")
            for i in range(len(table_north)):
                if ((ra1[i] < ra < ra2[i]) and (dec1[i] < dec < dec2[i])) \
                        or (sep1[i] < radius) or (sep2[i] < radius) or (sep3[i] < radius) or (sep4[i] < radius):
                    # row_north_list.append(table_north[i])
                    brickname = brick_name[i]
                    raIntPart = "{0:03}".format(int(ra1[i]))
                    URL = f"{self.URL}/dr{data_release}/north/tractor/{raIntPart}/tractor-{brickname}.fits"

                    response = requests.get(URL)
                    if response is not None and response.status_code == 200:
                        responses.append(response)
            print("Completion processing bricks northern emishpere, total time: ", time.time() - t0)

            # south table extraction
            brick_name = table_south['brickname']
            ra1 = table_south['ra1']
            dec1 = table_south['dec1']
            ra2 = table_south['ra2']
            dec2 = table_south['dec2']

            corners1 = SkyCoord(ra1, dec1, unit="deg")
            corners2 = SkyCoord(ra1, dec2, unit="deg")
            corners3 = SkyCoord(ra2, dec1, unit="deg")
            corners4 = SkyCoord(ra2, dec2, unit="deg")

            sep1 = coordinates.separation(corners1)
            sep2 = coordinates.separation(corners2)
            sep3 = coordinates.separation(corners3)
            sep4 = coordinates.separation(corners4)

            t0 = time.time()
            print("Beginning processing bricks southern emisphere")
            for i in range(len(table_south)):
                if ((ra1[i] < ra < ra2[i]) and (dec1[i] < dec < dec2[i])) \
                        or (sep1[i] < radius) or (sep2[i] < radius) or (sep3[i] < radius) or (sep4[i] < radius):
                    # row_south_list.append(table_south[i])
                    brickname = brick_name[i]
                    raIntPart = "{0:03}".format(int(ra1[i]))
                    URL = f"{self.URL}/dr{data_release}/south/tractor/{raIntPart}/tractor-{brickname}.fits"

                    response = requests.get(URL)
                    if response is not None and response.status_code == 200:
                        responses.append(response)
            print("Completion processing bricks southern emisphere, total time: ", time.time() - t0)
            print("-----------------------------------------------------")

            return responses

    def get_images_async(self, position, survey, coordinates=None, data_release=9,
                         projection=None, pixels=None, scaling=None,
                         sampler=None, resolver=None, deedger=None, lut=None,
                         grid=None, gridlabels=None, radius=None, height=None,
                         width=None, cache=True, show_progress=True, image_band='g'):
        """
        Returns
        -------
        A list of context-managers that yield readable file-like objects
        """

        image_size_arcsec = radius.arcsec
        pixsize = 2 * image_size_arcsec / pixels

        image_url = 'https://www.legacysurvey.org/viewer/fits-cutout?ra=' + str(coordinates.ra.deg) + '&dec=' + str(coordinates.dec.deg) + '&size=' + str(
            pixels) + '&layer=ls-dr' + str(data_release) + '&pixscale=' + str(pixsize) + '&bands=' + image_band

        print("image_url: ", image_url)

        return commons.FileContainer(image_url, encoding='binary', show_progress=show_progress)

    # as we mentioned earlier use various python regular expressions, etc
    # to create the dict of HTTP request parameters by parsing the user
    # entered values. For cleaner code keep this as a separate private method:

    def _args_to_payload(self, *args, **kwargs):
        request_payload = dict()
        # code to parse input and construct the dict
        # goes here. Then return the dict to the caller

        return request_payload

    # the methods above call the private _parse_result method.
    # This should parse the raw HTTP response and return it as
    # an `astropy.table.Table`. Below is the skeleton:

    def _parse_result(self, responses, verbose=False):
        tables_list = []
        output_table = Table()

        if isinstance(responses, Table):
            return responses

        if isinstance(responses, FileContainer):
            return responses

        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()
        # try to parse the result into an astropy.Table, else
        # return the raw result with an informative error message.
        try:
            if not isinstance(responses, list):
                responses = [responses]

            # do something with regex to get the result into
            # astropy.Table form. return the Table.
            # data = io.BytesIO(response.content)
            # table = Table.read(data)

            for r in responses:
                if r.status_code == 200:
                    # TODO figure out on how to avoid writing in a file
                    with open('/tmp/file_content', 'wb') as fin:
                        fin.write(r.content)

                    table = Table.read('/tmp/file_content', hdu=1)
                    tables_list.append(table)

            if len(tables_list) > 0:
                output_table = vstack(tables_list)

        except ValueError:
            # catch common errors here, but never use bare excepts
            # return raw result/ handle in some way
            pass

        return output_table

 
# the default tool for users to interact with is an instance of the Class
LegacySurvey = LegacySurveyClass()

# once your class is done, tests should be written
# See ./tests for examples on this

# Next you should write the docs in astroquery/docs/module_name
# using Sphinx.
