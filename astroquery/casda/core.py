# Licensed under a 3-clause BSD style license - see LICENSE.rst

# 1. standard library imports
from io import BytesIO
from urllib.parse import unquote
import time
from xml.etree import ElementTree
from datetime import datetime, timezone

# 2. third party imports
import astropy.units as u
import astropy.coordinates as coord
from astropy.table import Table
from astropy.io.votable import parse
from astropy import log

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

# export all the public classes and methods
__all__ = ['Casda', 'CasdaClass']


@async_to_sync
class CasdaClass(BaseQuery):

    """
    Class for accessing ASKAP data through the CSIRO ASKAP Science Data Archive (CASDA). Typical usage:

    result = Casda.query_region('22h15m38.2s -45d50m30.5s', radius=0.5 * u.deg)
    """
    # use the Configuration Items imported from __init__.py to set the URL,
    # TIMEOUT, etc.
    URL = conf.server
    TIMEOUT = conf.timeout
    POLL_INTERVAL = conf.poll_interval
    _soda_base_url = conf.soda_base_url
    _uws_ns = {'uws': 'http://www.ivoa.net/xml/UWS/v1.0'}

    def __init__(self, user=None, password=None):
        super(CasdaClass, self).__init__()
        if user is None:
            self._authenticated = False
        else:
            self._authenticated = True
            # self._user = user
            # self._password = password
            self._auth = (user, password)

    def query_region_async(self, coordinates, radius=None, height=None, width=None,
                           get_query_payload=False, cache=True):
        """
        Queries a region around the specified coordinates. Either a radius or both a height and a width must be provided.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            coordinates around which to query
        radius : str or `astropy.units.Quantity`.
            the radius of the cone search
        width : str or `astropy.units.Quantity`
            the width for a box region
        height : str or `astropy.units.Quantity`
            the height for a box region
        get_query_payload : bool, optional
            Just return the dict of HTTP request parameters.
        cache: bool, optional
            Use the astroquery internal query result cache

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.
        """
        request_payload = self._args_to_payload(coordinates=coordinates, radius=radius, height=height,
                                                width=width)
        if get_query_payload:
            return request_payload

        response = self._request('GET', self.URL, params=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)

        # result = self._parse_result(response)
        return response

    # Create the dict of HTTP request parameters by parsing the user
    # entered values.
    def _args_to_payload(self, **kwargs):
        request_payload = dict()

        # Convert the coordinates to FK5
        coordinates = kwargs.get('coordinates')
        c = commons.parse_coordinates(coordinates).transform_to(coord.FK5)

        if kwargs['radius'] is not None:
            radius = u.Quantity(kwargs['radius']).to(u.deg)
            pos = 'CIRCLE {} {} {}'.format(c.ra.degree, c.dec.degree, radius.value)
        elif kwargs['width'] is not None and kwargs['height'] is not None:
            width = u.Quantity(kwargs['width']).to(u.deg).value
            height = u.Quantity(kwargs['height']).to(u.deg).value
            top = c.dec.degree - (height/2)
            bottom = c.dec.degree + (height/2)
            left = c.ra.degree - (width/2)
            right = c.ra.degree + (width/2)
            pos = 'RANGE {} {} {} {}'.format(left, right, top, bottom)
        else:
            raise ValueError("Either 'radius' or both 'height' and 'width' must be supplied.")

        request_payload['POS'] = pos

        return request_payload

    # the methods above implicitly call the private _parse_result method.
    # This should parse the raw HTTP response and return it as
    # an `astropy.table.Table`.
    def _parse_result(self, response, verbose=False):
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()
        # try to parse the result into an astropy.Table, else
        # return the raw result with an informative error message.
        try:
            # do something with regex to get the result into
            # astropy.Table form. return the Table.
            data = BytesIO(response.content)
            table = Table.read(data)
            return table
        except ValueError as e:
            # catch common errors here, but never use bare excepts
            # return raw result/ handle in some way
            log.info("Failed to convert query result to table", e)
            return response

    def filter_out_unreleased(self, table):
        """
        Return a subset of the table which only includes released (public) data.

        Parameters
        ----------
        table: `astropy.table.Table`
            A table of results as returned by query_region. Must include an obs_release_date column.

        Returns
        -------
        table : `astropy.table.Table`
            The table with all unreleased (non public) data products filtered out.
        """
        now = str(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f'))
        return table[(table['obs_release_date'] != '') & (table['obs_release_date'] < now)]

    def stage_data(self, table, verbose=False):
        """
        Request access to a set of data files. All requests for data must use authentication. If you have access to the
        data, the requested files will be brought online and a set of URLs to download the files will be returned.

        Parameters
        ----------
        table: `astropy.table.Table`
            A table describing the files to be staged, such as produced by query_region. It must include an
            access_url column.
        verbose: bool, optional
            Should status message be logged periodically, defaults to False

        Returns
        -------
        A list of urls of both the requested files and the checksums for the files
        """
        if not self._authenticated:
            raise ValueError("Credentials must be supplied to download CASDA image data")

        if table is None or len(table) == 0:
            return []

        # Use datalink to get authenticated access for each file
        tokens = []
        for row in table:
            access_url = row['access_url']
            response = self._request('GET', access_url, auth=self._auth,
                                     timeout=self.TIMEOUT, cache=False)
            response.raise_for_status()
            soda_url, id_token = self._parse_datalink_for_service_and_id(response, 'cutout_service')
            tokens.append(id_token)

        # Create job to stage all files
        job_url = self._create_soda_job(tokens, soda_url=soda_url)
        if verbose:
            log.info("Created data staging job " + job_url)

        # Wait for job to be complete
        final_status = self._run_job(job_url, verbose, poll_interval=self.POLL_INTERVAL)
        if final_status != 'COMPLETED':
            if verbose:
                log.info("Job ended with status " + final_status)
            raise ValueError('Data staging job did not complete successfully. Status was ' + final_status)

        # Build list of result file urls
        job_details = self._get_job_details_xml(job_url)
        fileurls = []
        for result in job_details.find("uws:results", self._uws_ns).findall("uws:result", self._uws_ns):
            file_location = unquote(result.get("{http://www.w3.org/1999/xlink}href"))
            fileurls.append(file_location)

        return fileurls

    def download_files(self, urls, savedir=''):
        """
        Download a series of files

        Parameters
        ----------
        urls: list of strings
            The list of URLs of the files to be downloaded.
        savedir: str, optional
            The directory in which to save the files.

        Returns
        -------
        A list of the full filenames of the downloaded files.
        """
        # for each url in list, download file and checksum
        filenames = []
        for url in urls:
            fn = self._request('GET', url, save=True, savedir=savedir, timeout=self.TIMEOUT, cache=False)
            if fn:
                filenames.append(fn)

        return filenames

    def _parse_datalink_for_service_and_id(self, response, service_name):
        """
        Parses a datalink file into a vo table, and returns the async service url and the authenticated id token.

        Parameters
        ----------
        response: `requests.Response`
            The datalink query response.
        service_name: str
            The name of the service to be utilised.

        Returns
        -------
        The url of the async service and the authenticated id token of the file.
        """
        data = BytesIO(response.content)

        votable = parse(data, pedantic=False)
        results = next(resource for resource in votable.resources if
                       resource.type == "results")
        if results is None:
            return None
        results_array = results.tables[0].array
        async_url = None
        authenticated_id_token = None

        # Find the authenticated id token for accessing the image cube
        for x in results_array:
            service_def = x['service_def']
            if isinstance(service_def, bytes):
                service_def = service_def.decode("utf8")
            if service_def == service_name:
                authenticated_id_token = x['authenticated_id_token']
                if isinstance(service_def, bytes):
                    authenticated_id_token = authenticated_id_token.decode("utf8")

        # Find the async url
        for x in votable.resources:
            if x.type == "meta":
                if x.ID == service_name:
                    for p in x.params:
                        if p.name == "accessURL":
                            async_url = p.value
                            if isinstance(async_url, bytes):
                                async_url = async_url.decode()

        return async_url, authenticated_id_token

    def _create_soda_job(self, authenticated_id_tokens, soda_url=None):
        """
        Creates the async job, returning the url to query the job status and details

        Parameters
        ----------
        authenticated_id_tokens: list of str
            A list of tokens identifying the data products to be accessed.
        soda_url: str, optional
            The URL to be used to access the soda service. If not provided, the default CASDA one will be used.

        Returns
        -------
        The url of the SODA job.
        """
        id_params = list(
            map((lambda authenticated_id_token: ('ID', authenticated_id_token)),
                authenticated_id_tokens))
        async_url = soda_url if soda_url else self._get_soda_url()

        resp = self._request('POST', async_url, params=id_params, cache=False)
        resp.raise_for_status()
        return resp.url

    def _run_job(self, job_location, verbose, poll_interval=20):
        """
        Start an async job (e.g. TAP or SODA) and wait for it to be completed.

        Parameters
        ----------
        job_location: str
            The url to query the job status and details
        verbose: bool
            Should progress be logged periodically
        poll_interval: int, optional
            The number of seconds to wait between checks on the status of the job.

        Returns
        -------
        The single word final status of the job. Normally COMPLETED or ERROR
        """
        # Start the async job
        if verbose:
            log.info("Starting the retrieval job...")
        self._request('POST', job_location + "/phase", data={'phase': 'RUN'}, cache=False)

        # Poll until the async job has finished
        prev_status = None
        count = 0
        job_details = self._get_job_details_xml(job_location)
        status = self._read_job_status(job_details, verbose)
        while status == 'EXECUTING' or status == 'QUEUED' or status == 'PENDING':
            count += 1
            if verbose and (status != prev_status or count > 10):
                log.info("Job is %s, polling every %d seconds." % (status, poll_interval))
                count = 0
                prev_status = status
            time.sleep(poll_interval)
            job_details = self._get_job_details_xml(job_location)
            status = self._read_job_status(job_details, verbose)
        return status

    def _get_soda_url(self):
        return self._soda_base_url + "data/async"

    def _get_job_details_xml(self, async_job_url):
        """
        Get job details as XML

        Parameters
        ----------
        async_job_url: str
            The url to query the job details

        Returns
        -------
        `xml.etree.ElementTree` The job details object
        """
        response = self._request('GET', async_job_url, cache=False)
        response.raise_for_status()
        job_response = response.text
        return ElementTree.fromstring(job_response)

    def _read_job_status(self, job_details_xml, verbose):
        """
        Read job status from the job details XML

        Parameters
        ----------
        job_details_xml: `xml.etree.ElementTree`
            The SODA job details
        verbose: bool
            Should additional information be logged for errors

        Returns
        -------
        The single word status of the job. e.g. COMPLETED, EXECUTING, ERROR
        """
        status_node = job_details_xml.find("{http://www.ivoa.net/xml/UWS/v1.0}phase")
        if status_node is None:
            if verbose:
                log.info("Unable to find status in status xml:")
                ElementTree.dump(job_details_xml)
            raise ValueError('Invalid job status xml received.')
        status = status_node.text
        return status


# the default tool for users to interact with is an instance of the Class
Casda = CasdaClass()
