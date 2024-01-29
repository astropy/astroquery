# Licensed under a 3-clause BSD style license - see LICENSE.rst

from io import BytesIO
import os
from urllib.parse import unquote, urlparse
import time
from xml.etree import ElementTree
from datetime import datetime, timezone
import keyring

import astropy.units as u
import astropy.coordinates as coord
from astropy.table import Table
from astropy.io.votable import parse
from astroquery import log
import numpy as np

from ..query import QueryWithLogin
from ..utils import commons
from ..utils import async_to_sync
from . import conf
from ..exceptions import LoginError


__all__ = ['Casda', 'CasdaClass']


@async_to_sync
class CasdaClass(QueryWithLogin):

    """
    Class for accessing ASKAP data through the CSIRO ASKAP Science Data Archive (CASDA). Typical usage:

    result = Casda.query_region('22h15m38.2s -45d50m30.5s', radius=0.5 * u.deg)
    """
    # use the Configuration Items imported from __init__.py to set the URL,
    # TIMEOUT, etc.
    URL = conf.server
    TIMEOUT = conf.timeout
    POLL_INTERVAL = conf.poll_interval
    USERNAME = conf.username
    _soda_base_url = conf.soda_base_url
    _login_url = conf.login_url
    _uws_ns = {'uws': 'http://www.ivoa.net/xml/UWS/v1.0'}

    def __init__(self):
        super().__init__()

    def _login(self, *, username=None, store_password=False,
               reenter_password=False):
        """
        login to non-public data as a known user

        Parameters
        ----------
        username : str, optional
            Username to the CASDA archive, uses ATNF OPAL credentials. If not given, it should be
            specified in the config file.
        store_password : bool, optional
            Stores the password securely in your keyring. Default is False.
        reenter_password : bool, optional
            Asks for the password even if it is already stored in the
            keyring. This is the way to overwrite an already stored passwork
            on the keyring. Default is False.
        """

        if username is None:
            if not self.USERNAME:
                raise LoginError("If you do not pass a username to login(), "
                                 "you should configure a default one!")
            else:
                username = self.USERNAME

        # Get password from keyring or prompt
        password, password_from_keyring = self._get_password(
            "astroquery:casda.csiro.au", username, reenter=reenter_password)

        # Login to CASDA to test credentals
        log.info("Authenticating {0} on CASDA ...".format(username))
        auth = (username, password)
        login_response = self._request("GET", self._login_url, auth=auth,
                                       timeout=self.TIMEOUT, cache=False)
        authenticated = login_response.status_code == 200

        if authenticated:
            log.info("Authentication successful!")
            self.USERNAME = username
            self._auth = (username, password)

            # When authenticated, save password in keyring if needed
            if password_from_keyring is None and store_password:
                keyring.set_password("astroquery:casda.csiro.au", username, password)
        else:
            log.exception("Authentication failed")

        return authenticated

    def query_region_async(self, coordinates, *, radius=1*u.arcmin, height=None, width=None,
                           get_query_payload=False, cache=True):
        """
        Queries a region around the specified coordinates. Either a radius or both a height and a width
        must be provided.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            coordinates around which to query
        radius : str or `astropy.units.Quantity`, optional
            the radius of the cone search
        height : str or `astropy.units.Quantity`, optional
            the height for a box region
        width : str or `astropy.units.Quantity`, optional
            the width for a box region
        get_query_payload : bool, optional
            Just return the dict of HTTP request parameters.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

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
    def _args_to_payload(self, *, radius=1*u.arcmin, **kwargs):
        request_payload = dict()

        # Convert the coordinates to FK5
        coordinates = kwargs.get('coordinates')
        if coordinates is not None:
            fk5_coords = commons.parse_coordinates(coordinates).transform_to(coord.FK5)

            if kwargs.get('width') is not None and kwargs.get('height') is not None:
                width = u.Quantity(kwargs['width']).to(u.deg).value
                height = u.Quantity(kwargs['height']).to(u.deg).value
                top = fk5_coords.dec.degree + (height/2)
                bottom = fk5_coords.dec.degree - (height/2)
                left = fk5_coords.ra.degree - (width/2)
                right = fk5_coords.ra.degree + (width/2)
                pos = f'RANGE {left} {right} {bottom} {top}'
            else:
                radius = u.Quantity(radius).to(u.deg)
                pos = f'CIRCLE {fk5_coords.ra.degree} {fk5_coords.dec.degree} {radius.value}'

            request_payload['POS'] = pos

        band = kwargs.get('band')
        channel = kwargs.get('channel')
        if band is not None:
            if channel is not None:
                raise ValueError("Either 'channel' or 'band' values may be provided but not both.")

            if (not isinstance(band, (list, tuple, np.ndarray))) or len(band) != 2 or \
                    (band[0] is not None and not isinstance(band[0], u.Quantity)) or \
                    (band[1] is not None and not isinstance(band[1], u.Quantity)):
                raise ValueError("The 'band' value must be a list of 2 wavelength or frequency values.")

            bandBoundedLow = band[0] is not None
            bandBoundedHigh = band[1] is not None
            if bandBoundedLow and bandBoundedHigh and band[0].unit.physical_type != band[1].unit.physical_type:
                raise ValueError("The 'band' values must have the same kind of units.")
            if bandBoundedLow or bandBoundedHigh:
                unit = band[0].unit if bandBoundedLow else band[1].unit
                if unit.physical_type == 'length':
                    min_band = '-Inf' if not bandBoundedLow else band[0].to(u.m).value
                    max_band = '+Inf' if not bandBoundedHigh else band[1].to(u.m).value
                elif unit.physical_type == 'frequency':
                    # Swap the order when changing frequency to wavelength
                    min_band = '-Inf' if not bandBoundedHigh else band[1].to(u.m, equivalencies=u.spectral()).value
                    max_band = '+Inf' if not bandBoundedLow else band[0].to(u.m, equivalencies=u.spectral()).value
                else:
                    raise ValueError("The 'band' values must be wavelengths or frequencies.")
                # If values were provided in the wrong order, swap them
                if bandBoundedLow and bandBoundedHigh and min_band > max_band:
                    temp_val = min_band
                    min_band = max_band
                    max_band = temp_val

                request_payload['BAND'] = f'{min_band} {max_band}'

        if channel is not None:
            if not isinstance(channel, (list, tuple, np.ndarray)) or len(channel) != 2 or \
                    not isinstance(channel[0], (int, np.integer)) or not isinstance(channel[1], (int, np.integer)):
                raise ValueError("The 'channel' value must be a list of 2 integer values.")
            if channel[0] <= channel[1]:
                request_payload['CHANNEL'] = f'{channel[0]} {channel[1]}'
            else:
                # If values were provided in the wrong order, swap them
                request_payload['CHANNEL'] = f'{channel[1]} {channel[0]}'

        return request_payload

    # the methods above implicitly call the private _parse_result method.
    # This should parse the raw HTTP response and return it as
    # an `astropy.table.Table`.
    def _parse_result(self, response, *, verbose=False):
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

    def _create_job(self, table, service_name, verbose):
        # Use datalink to get authenticated access for each file
        tokens = []
        soda_url = None
        for row in table:
            access_url = row['access_url']
            if access_url:
                response = self._request('GET', access_url, auth=self._auth,
                                         timeout=self.TIMEOUT, cache=False)
                response.raise_for_status()
                service_url, id_token = self._parse_datalink_for_service_and_id(response, service_name)
                if id_token:
                    tokens.append(id_token)
                    soda_url = service_url

        # Trap a request with no allowed data
        if not soda_url:
            raise ValueError('You do not have access to any of the requested data files.')

        # Create job to stage all files
        job_url = self._create_soda_job(tokens, soda_url=soda_url)
        if verbose:
            log.info("Created data staging job " + job_url)

        return job_url

    def _complete_job(self, job_url, verbose):
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

    def stage_data(self, table, *, verbose=False):
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
        A list of urls of both the requested files/cutouts and the checksums for the files/cutouts
        """
        if not self._authenticated:
            raise ValueError("Credentials must be supplied to download CASDA image data")

        if table is None or len(table) == 0:
            return []

        job_url = self._create_job(table, 'async_service', verbose)

        return self._complete_job(job_url, verbose)

    def cutout(self, table, *, coordinates=None, radius=1*u.arcmin, height=None,
               width=None, band=None, channel=None, verbose=False):
        """
        Produce a cutout from each selected file. All requests for data must use authentication. If you have access to
        the data, the requested files will be brought online, a cutout produced from each file and a set of URLs to
        download the cutouts will be returned.

        If a set of coordinates is provided along with either a radius or a box height and width, then CASDA will
        produce a spatial cutout at that location from each data file specified in the table. If a band or channel pair
        is provided then CASDA will produce a spectral cutout of that range from each data file. These can be combined
        to produce subcubes with restrictions in both spectral and spatial axes.

        Parameters
        ----------
        table: `astropy.table.Table`
            A table describing the files to be staged, such as produced by query_region. It must include an
            access_url column.
        coordinates : str or `astropy.coordinates`, optional
            coordinates around which to produce a cutout, the radius will be 1 arcmin if no radius, height or width is
            provided.
        radius : str or `astropy.units.Quantity`, optional
            the radius of the cutout
        height : str or `astropy.units.Quantity`, optional
            the height for a box cutout
        width : str or `astropy.units.Quantity`, optional
            the width for a box cutout
        band : list of `astropy.units.Quantity` with two elements, optional
            the spectral range to be included, may be low and high wavelengths in metres or low and high frequencies in
            Hertz. Use None for an open bound.
        channel : list of int with two elements, optional
            the spectral range to be included, the low and high channels (i.e. planes of a cube) inclusive
        verbose: bool, optional
            Should status messages be logged periodically, defaults to False

        Returns
        -------
        A list of urls of both the requested files/cutouts and the checksums for the files/cutouts
        """
        if not self._authenticated:
            raise ValueError("Credentials must be supplied to download CASDA image data")

        if table is None or len(table) == 0:
            return []

        job_url = self._create_job(table, 'cutout_service', verbose)

        cutout_spec = self._args_to_payload(radius=radius, coordinates=coordinates, height=height, width=width,
                                            band=band, channel=channel, verbose=verbose)

        if not cutout_spec:
            raise ValueError("Please provide cutout parameters such as coordinates, band or channel.")

        self._add_cutout_params(job_url, verbose, cutout_spec)

        return self._complete_job(job_url, verbose)

    def download_files(self, urls, *, savedir=''):
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
            parseResult = urlparse(url)
            local_filename = unquote(os.path.basename(parseResult.path))
            if os.name == 'nt':
                # Windows doesn't allow special characters in filenames like
                # ":" so replace them with an underscore
                local_filename = local_filename.replace(':', '_')
            local_filepath = os.path.join(savedir or self.cache_location or '.', local_filename)
            self._download_file(url, local_filepath, timeout=self.TIMEOUT, cache=False)
            filenames.append(local_filepath)

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

        votable = parse(data, verify='warn')
        results = next(resource for resource in votable.resources if
                       resource.type == "results")
        if results is None:
            return None
        results_array = results.tables[0].array
        async_url = None
        authenticated_id_token = None

        # Find the authenticated id token for accessing the image cube
        for result in results_array:
            service_def = result['service_def']
            if isinstance(service_def, bytes):
                service_def = service_def.decode("utf8")
            if service_def == service_name:
                authenticated_id_token = result['authenticated_id_token']
                if isinstance(service_def, bytes):
                    authenticated_id_token = authenticated_id_token.decode("utf8")

        # Find the async url
        for resource in votable.resources:
            if resource.type == "meta":
                if resource.ID == service_name:
                    for param in resource.params:
                        if param.name == "accessURL":
                            async_url = param.value
                            if isinstance(async_url, bytes):
                                async_url = async_url.decode()

        return async_url, authenticated_id_token

    def _create_soda_job(self, authenticated_id_tokens, *, soda_url=None):
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

    def _add_cutout_params(self, job_location, verbose, cutout_spec):
        """
        Add a cutout specification to an async SODA job. This will change the job
        from just retrieving the full file to producing a cutout from the target file.

        Parameters
        ----------
        job_location: str
            The url to query the job status and details
        verbose: bool
            Should progress be logged periodically
        cutout_spec: map
            The map containing the POS parameter defining the cutout.
        """
        if verbose:
            log.info("Adding parameters: " + str(cutout_spec))
        resp = self._request('POST', job_location + '/parameters', data=cutout_spec, cache=False)
        resp.raise_for_status()

    def _run_job(self, job_location, verbose, *, poll_interval=20):
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
