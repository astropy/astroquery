# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
CADC
====


Module to query the Canadian Astronomy Data Centre (CADC).
"""

import logging
import warnings
import requests
from numpy import ma
from six.moves.urllib.parse import urlencode
from six.moves.urllib_error import HTTPError

from ..utils.class_or_instance import class_or_instance
from ..utils import async_to_sync, commons
from ..query import BaseQuery
from bs4 import BeautifulSoup
from astropy.utils.exceptions import AstropyDeprecationWarning
from astroquery.utils.decorators import deprecated
from astropy import units as u
from . import conf

try:
    import pyvo
    from pyvo.auth import authsession
except ImportError:
    print('Please install pyvo. astropy.cadc does not work without it.')
except AstropyDeprecationWarning as e:
    if str(e) == 'The astropy.vo.samp module has now been moved to astropy.samp':
        # CADC does not use samp and this only affects Python 2.7
        print('AstropyDeprecationWarning: {}'.format(str(e)))
    else:
        raise e

__all__ = ['Cadc', 'CadcClass']

CADC_COOKIE_PREFIX = 'CADC_SSO'

logger = logging.getLogger(__name__)

# TODO figure out what do to if anything about them. Some might require
# fixes on the CADC servers
warnings.filterwarnings('ignore', module='astropy.io.votable')


@async_to_sync
class CadcClass(BaseQuery):
    """
    Class for accessing CADC data. Typical usage:

    result = Cadc.query_region('08h45m07.5s +54d18m00s', collection='CFHT')

    ... do something with result (optional) such as filter as in example below

    urls = Cadc.get_data_urls(result[result['target_name']=='Nr3491_1'])

    ... access data

    Other ways to query the CADC data storage:

    - target name:
        Cadc.query_region(SkyCoord.from_name('M31'))
    - target name in the metadata:
        Cadc.query_name('M31-A-6')  # queries as a like '%lower(name)%'
    - TAP query on the CADC metadata (CAOM2 format -
        http://www.opencadc.org/caom2/)
        Cadc.get_tables()  # list the tables
        Cadc.get_table(table_name)  # list table schema
        Cadc.query


    """

    CADC_REGISTRY_URL = conf.CADC_REGISTRY_URL
    CADCTAP_SERVICE_URI = conf.CADCTAP_SERVICE_URI
    CADCDATALINK_SERVICE_URI = conf.CADCDATLINK_SERVICE_URI
    CADCLOGIN_SERVICE_URI = conf.CADCLOGIN_SERVICE_URI
    TIMEOUT = conf.TIMEOUT

    def __init__(self, url=None, tap_plus_handler=None, verbose=None,
                 auth_session=None):
        """
        Initialize Cadc object

        Parameters
        ----------
        url : str, optional, default 'None;
            a url to use instead of the default
        tap_plus_handler : deprecated
        verbose : deprecated
        auth_session: `requests.Session` or `pyvo.auth.authsession.AuthSession`
            A existing authenticated session containing the appropriate
            credentials to be used by the client to communicate with the
            server. This is an alternative to using login/logout methods that
            allows clients to reuse existing session with multiple services.
        Returns
        -------
        Cadc object
        """
        if tap_plus_handler:
            raise AttributeError('tap handler no longer supported')
        if verbose is not None:
            warnings.warn('verbose deprecated since version 0.4.0')

        super(CadcClass, self).__init__()
        self.baseurl = url
        if auth_session:
            self._auth_session = auth_session
        else:
            self._auth_session = None

    @property
    def cadctap(self):
        if not self._auth_session:
            self._auth_session = authsession.AuthSession()
        if not hasattr(self, '_cadctap'):
            if self.baseurl is None:
                self.baseurl = get_access_url(self.CADCTAP_SERVICE_URI)
                # remove capabilities endpoint to get to the service url
                self.baseurl = self.baseurl.rstrip('capabilities')
                self._cadctap = pyvo.dal.TAPService(
                    self.baseurl, session=self._auth_session)
            else:
                self._cadctap = pyvo.dal.TAPService(
                    self.baseurl, session=self._auth_session)
        return self._cadctap

    @property
    def data_link_url(self):
        if not hasattr(self, '_data_link_url'):
            self._data_link_url = get_access_url(
                self.CADCDATALINK_SERVICE_URI,
                "ivo://ivoa.net/std/DataLink#links-1.0")
        return self._data_link_url

    def login(self, user=None, password=None, certificate_file=None):
        """
        login allows user to authenticate to the service. Both user/password
        and https client certificates are supported.

         Alternatively, the Cadc class can be instantiated with an
         authenticated session.

        Parameters
        ----------
        user : str, required if certificate is None
            username to login with
        password : str, required if user is set
            password to login with
        certificate : str, required if user is None
            path to certificate to use with logging in

        """
        # start with a new session
        if not isinstance(self.cadctap._session, (requests.Session,
                                                  authsession.AuthSession)):
            raise TypeError('Cannot login with user provided session that is '
                            'not an pyvo.authsession.AuthSession or '
                            'requests.Session')
        if not certificate_file and not (user and password):
            raise AttributeError('login credentials missing (user/password '
                                 'or certificate)')
        if certificate_file:
            if isinstance(self.cadctap._session, authsession.AuthSession):
                self.cadctap._session.credentials.\
                    set_client_certificate(certificate_file)
            else:
                # if the session was already used to call CADC, requests caches
                # it without using the cert. Therefore need to close all
                # existing https sessions first.
                https_adapter = self.cadctap._session.adapters['https://']
                if https_adapter:
                    https_adapter.close()
                self.cadctap._session.cert = certificate_file
        if user and password:
            login_url = get_access_url(self.CADCLOGIN_SERVICE_URI,
                                       'ivo://ivoa.net/std/UMS#login-0.1')
            if login_url is None:
                raise RuntimeError("No login URL")
            # need to login and get a cookie
            args = {
                "username": str(user),
                "password": str(password)}
            header = {
                "Content-type": "application/x-www-form-urlencoded",
                "Accept": "text/plain"
            }
            response = self._request(method='POST', url=login_url, data=args,
                                     headers=header, cache=False)
            try:
                response.raise_for_status()
            except Exception as e:
                logger.error('Logging error: {}'.format(e))
                raise e
            # extract cookie
            cookie = '"{}"'.format(response.text)
            if cookie is not None:
                if isinstance(self.cadctap._session, authsession.AuthSession):
                    self.cadctap._session.credentials.set_cookie(
                        CADC_COOKIE_PREFIX, cookie)
                else:
                    self.cadctap._session.cookies.set(
                        CADC_COOKIE_PREFIX, cookie)

    def logout(self, verbose=None):
        """
        Logout. Anonymous access with all the subsequent use of the
        object. Note that the original session is not affected (in case
        it was passed when the object was first intantiated)

        Parameters
        ----------
        verbose : deprecated

        """
        if verbose is not None:
            warnings.warn('verbose deprecated since 0.4.0')

        # the only way to ensure complete logout is to start with a new
        # session. This is mainly because of certificates. Adding cert
        # argument to a session already in use does not force it to
        # re-do the HTTPS hand shake
        self.cadctap._session = authsession.AuthSession()
        self.cadctap._session.update_from_capabilities(
            self.cadctap.capabilities)

    @class_or_instance
    def query_region_async(self, coordinates, radius=0.016666666666667*u.deg,
                           collection=None,
                           get_query_payload=False):
        """
        Queries the CADC for a region around the specified coordinates.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            coordinates around which to query
        radius : str or `astropy.units.Quantity`.
            the radius of the cone search
        collection: Name of the CADC collection to query, optional
        get_query_payload : bool, optional
            Just return the dict of HTTP request parameters.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.
        """

        if isinstance(radius, (int, float)):
            warnings.warn('Radius should be of type str or '
                          '`astropy.units.Quantity`')
            radius = radius * u.deg

        request_payload = self._args_to_payload(coordinates=coordinates,
                                                radius=radius,
                                                collection=collection)
        # primarily for debug purposes, but also useful if you want to send
        # someone a URL linking directly to the data
        if get_query_payload:
            return request_payload
        response = self.exec_sync(request_payload['query'])
        return response

    @class_or_instance
    def query_name_async(self, name):
        """
        Query CADC metadata for a name and return the corresponding metadata in
         the CAOM2 format (http://www.opencadc.org/caom2/).

        Parameters
        ----------
        name: str
                name of object to query for

        Returns
        -------
        response : `~astropy.table.Table`
            Results of the query in a tabular format.

        """
        response = self.exec_sync(
            "select * from caom2.Observation o join caom2.Plane p "
            "on o.obsID=p.obsID where lower(target_name) like '%{}%'".
            format(name.lower()))
        return response

    @class_or_instance
    def get_collections(self):
        """
        Query CADC for all the hosted collections

        Returns
        -------
        A dictionary of collections hosted at the CADC where the key is the
        collection and value represents details of that collection.
        """
        response = self.exec_sync(
            'select distinct collection, energy_emBand from caom2.EnumField')
        collections = {}
        for row in response:
            if row['collection'] not in collections:
                collection = {
                    'Description': 'The {} collection at the CADC'.
                    format(row['collection']), 'Bands': []}
                if row['energy_emBand'] is not ma.masked:
                    collection['Bands'].append(row['energy_emBand'])
                collections[row['collection']] = collection
            elif row['energy_emBand'] is not ma.masked:
                collections[row['collection']]['Bands'].\
                    append(row['energy_emBand'])
        return collections

    @class_or_instance
    def get_images(self, coordinates, radius,
                   collection=None,
                   get_url_list=False,
                   show_progress=False):
        """
        A coordinate-based query function that returns a list of
        fits files with cutouts around the passed in coordinates.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            Coordinates around which to query.
        radius : str or `astropy.units.Quantity`
            The radius of the cone search AND cutout area.
        collection : str, optional
            Name of the CADC collection to query.
        get_url_list : bool, optional
            If ``True``, returns the list of data urls rather than
            the downloaded FITS files. Default is ``False``.
        show_progress : bool, optional
            Whether to display a progress bar if the file is downloaded
            from a remote server.  Default is ``False``.

        Returns
        -------
        list : A list of `~astropy.io.fits.HDUList` objects (or a list of
        str if returning urls).
        """

        filenames = self.get_images_async(coordinates, radius, collection,
                                          get_url_list, show_progress)

        if get_url_list:
            return filenames

        images = []

        for fn in filenames:
            try:
                images.append(fn.get_fits())
            except HTTPError as err:
                # Catch HTTPError if user is unauthorized to access file
                logger.debug(
                    "{} - Problem retrieving the file: {}".
                    format(str(err), str(err.url)))
                pass

        return images

    def get_images_async(self, coordinates, radius, collection=None,
                         get_url_list=False, show_progress=False):
        """
        A coordinate-based query function that returns a list of
        context managers with cutouts around the passed in coordinates.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            Coordinates around which to query.
        radius : str or `astropy.units.Quantity`
            The radius of the cone search AND cutout area.
        collection : str, optional
            Name of the CADC collection to query.
        get_url_list : bool, optional
            If ``True``, returns the list of data urls rather than
            the list of context managers. Default is ``False``.
        show_progress : bool, optional
            Whether to display a progress bar if the file is downloaded
            from a remote server.  Default is ``False``.

        Returns
        -------
        list : A list of context-managers that yield readable file-like objects
        """
        request_payload = self._args_to_payload(coordinates=coordinates,
                                                radius=radius,
                                                collection=collection,
                                                data_product_type='image')
        query_result = self.exec_sync(request_payload['query'])
        images_urls = self.get_image_list(query_result, coordinates, radius)

        if get_url_list:
            return images_urls

        return [commons.FileContainer(url, encoding='binary',
                                      show_progress=show_progress)
                for url in images_urls]

    def get_image_list(self, query_result, coordinates, radius):
        """
        Function to map the results of a CADC query into URLs to
        corresponding data and cutouts that can be later downloaded.

        The function uses the IVOA DataLink Service
        (http://www.ivoa.net/documents/DataLink/) implemented at the CADC.
        It works directly with the results produced by `query_region` and
        `query_name` but in principle it can work with other query
        results produced with the Cadc query as long as the results
        contain the 'publisherID' column. This column is part of the
        'caom2.Plane' table.

        Parameters
        ----------
        query_result : A `~astropy.table.Table` object
            Result returned by `query_region` or
            `query_name`. In general, the result of any
            CADC TAP query that contains the 'publisherID'
            column can be used here.
        coordinates : str or `astropy.coordinates`.
            Center of the cutout area.
        radius : str or `astropy.units.Quantity`.
            The radius of the cutout area.

        Returns
        -------
        list : A list of URLs to cutout data.
        """

        if not query_result:
            raise AttributeError('Missing query_result argument')

        parsed_coordinates = commons.parse_coordinates(coordinates).fk5
        radius_deg = commons.radius_to_unit(radius, unit='degree')
        ra = parsed_coordinates.ra.degree
        dec = parsed_coordinates.dec.degree
        cutout_params = {'POS': 'CIRCLE {} {} {}'.format(ra, dec, radius_deg)}

        try:
            publisher_ids = query_result['publisherID']
        except KeyError:
            raise AttributeError(
                'publisherID column missing from query_result argument')

        result = []

        # Send datalink requests in batches of 20 publisher ids
        batch_size = 20

        # Iterate through list of sublists to send datalink requests in batches
        for pid_sublist in (publisher_ids[pos:pos + batch_size] for pos in
                            range(0, len(publisher_ids), batch_size)):
            datalink = pyvo.dal.adhoc.DatalinkResults.from_result_url(
                '{}?{}'.format(self.data_link_url,
                               urlencode({'ID': pid_sublist}, True)))
            for service_def in datalink.bysemantics('#cutout'):
                access_url = service_def.access_url
                if isinstance(access_url, bytes):  # ASTROPY_LT_4_1
                    access_url = access_url.decode('ascii')
                if '/sync' in access_url:
                    service_params = service_def.input_params
                    input_params = {param.name: param.value
                                    for param in service_params if
                                    param.name in ['ID', 'RUNID']}
                    input_params.update(cutout_params)
                    result.append('{}?{}'.format(access_url,
                                                 urlencode(input_params)))

        return result

    @class_or_instance
    def get_data_urls(self, query_result, include_auxiliaries=False):
        """
        Function to map the results of a CADC query into URLs to
        corresponding data that can be later downloaded.

        The function uses the IVOA DataLink Service
        (http://www.ivoa.net/documents/DataLink/) implemented at the CADC.
        It works directly with the results produced by `query_region` and
        `query_name` but in principle it can work with other query
        results produced with the Cadc query as long as the results
        contain the 'publisherID' column. This column is part of the
        'caom2.Plane' table.

        Parameters
        ----------
        query_result : A `~astropy.table.Table` object
                Result returned by `query_region` or
                `query_name`. In general, the result of any
                CADC TAP query that contains the 'publisherID' column
                can be use here.
        include_auxiliaries : boolean
                ``True`` to return URLs to auxiliary files such as
                previews, ``False`` otherwise

        Returns
        -------
        A list of URLs to data.
        """

        if not query_result:
            raise AttributeError('Missing metadata argument')

        try:
            publisher_ids = query_result['publisherID']
        except KeyError:
            raise AttributeError(
                'publisherID column missing from query_result argument')
        result = []
        # Send datalink requests in batches of 20 publisher ids
        batch_size = 20

        # Iterate through list of sublists to send datalink requests in batches
        for pid_sublist in (publisher_ids[pos:pos + batch_size] for pos in
                            range(0, len(publisher_ids), batch_size)):
            # REQUEST=download-only is a CADC optimization to restrict
            # results to downloadable URLs as opposed to redirects
            # to other services such as cutouts that are not required
            datalink = pyvo.dal.adhoc.DatalinkResults.from_result_url(
                '{}?{}'.format(self.data_link_url,
                               urlencode({'ID': pid_sublist,
                                          'REQUEST': 'downloads-only'}, True)))
            for service_def in datalink:
                if service_def.semantics == 'http://www.openadc.org/caom2#pkg':
                    # pkg is an alternative for downloading multiple
                    # data files in a tar file as an alternative to separate
                    # downloads. It doesn't make much sense in this case so
                    # filter it out.
                    continue
                if not include_auxiliaries \
                   and service_def.semantics != '#this':
                    continue
                result.append(service_def.access_url)
        return result

    def get_tables(self, only_names=False, verbose=None):
        """
        Gets all public tables

        Parameters
        ----------
        only_names : bool, optional, default False
            True to load table names only
        verbose : deprecated

        Returns
        -------
        A list of table objects
        """
        if verbose is not None:
            warnings.warn('verbose deprecated since 0.4.0')
        table_set = self.cadctap.tables
        if only_names:
            return list(table_set.keys())
        else:
            return list(table_set.values())

    def get_table(self, table, verbose=None):
        """
        Gets the specified table

        Parameters
        ----------
        table : str, mandatory
            full qualified table name (i.e. schema name + table name)
        verbose : deprecated

        Returns
        -------
        A table object
        """
        if verbose is not None:
            warnings.warn('verbose deprecated since 0.4.0')
        tables = self.get_tables()
        for t in tables:
            if table == t.name:
                return t

    def exec_sync(self, query, maxrec=None, uploads=None, output_file=None):
        """
        Run a query and return the results or save them in a output_file

        Parameters
        ----------
        query : str, mandatory
            SQL to execute
        maxrec : int
            the maximum records to return. defaults to the service default
        uploads:
            Temporary tables to upload and run with the queries
        output_file: str or file handler:
            File to save the results to

        Returns
        -------
        Results of running the query in (for now) votable format

        Notes
        -----
        Support for other output formats (tsv, csv) to be added as soon
        as they are available in pyvo.
        """
        response = self.cadctap.search(query, language='ADQL',
                                       uploads=uploads)
        result = response.to_table()
        if output_file:
            if isinstance(output_file, str):
                with open(output_file, 'bw') as f:
                    f.write(result)
            else:
                output_file.write(result)
        return result

    def create_async(self, query, maxrec=None, uploads=None):
        """
        Creates a TAP job to execute and returns it to the caller. The
        caller then can start the execution and monitor the job.
        Typical (no error handling) sequence of events:

            job = create_async(query)
            job = job.run().wait()
            job.raise_if_error()
            result = job.fetch_result()
            job.delete() # optional

        See ``pyvo.dal.tap`` for details about the ``AsyncTAPJob``

        Parameters
        ----------
        query : str, mandatory
            SQL to execute
        maxrec : int
            the maximum records to return. defaults to the service default
        uploads:
            Temporary tables to upload and run with the queries
        output_file: str or file handler:
            File to save the results to

        Returns
        -------
        AsyncTAPJob
            the query instance

        Notes
        -----
        Support for other output formats (tsv, csv) to be added as soon
        as they are available in pyvo.
        """
        return self.cadctap.submit_job(query, language='ADQL',
                                       uploads=uploads)

    @deprecated('0.4.0', 'Use exec_sync or create_async instead')
    def run_query(self, query, operation, output_file=None,
                  output_format="votable", verbose=None,
                  background=False, upload_resource=None,
                  upload_table_name=None):
        """
        Runs a query

        Parameters
        ----------
        query : str, mandatory
            query to be executed
        operation : str, mandatory,
            'sync' or 'async' to run a synchronous or asynchronous job
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format, 'csv', 'tsv' and 'votable'
        verbose : deprecated
        save_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory
        background : bool, optional, default 'False'
            when the job is executed in asynchronous mode,
            this flag specifies whether the execution will wait until results
            are available
        upload_resource: str, optional, default None
            resource to be uploaded to UPLOAD_SCHEMA
        upload_table_name: str, required if uploadResource is provided,
            default None
            resource temporary table name associated to the uploaded resource

        Returns
        -------
        A Job object
        """
        raise NotImplementedError('No longer supported. '
                                  'Use exec_sync or create_async instead.')

    def load_async_job(self, jobid, verbose=None):
        """
        Loads an asynchronous job

        Parameters
        ----------
        jobid : str, mandatory
            job identifier
        verbose : deprecated

        Returns
        -------
        A Job object
        """
        if verbose is not None:
            warnings.warn('verbose deprecated since 0.4.0')

        return pyvo.dal.AsyncTAPJob('{}/async/{}'.format(
            self.cadctap.baseurl, jobid))

    def list_async_jobs(self, phases=None, after=None, last=None,
                        short_description=True, verbose=None):
        """
        Returns all the asynchronous jobs

        Parameters
        ----------
        phases: list of str
            Union of job phases to filter the results by.
        after: datetime
            Return only jobs created after this datetime
        last: int
            Return only the most recent number of jobs
        short_description: flag - True or False
            If True, the jobs in the list will contain only the information
            corresponding to the TAP ShortJobDescription object (job ID, phase,
            run ID, owner ID and creation ID) whereas if False, a separate GET
            call to each job is performed for the complete job description
        verbose : deprecated

        Returns
        -------
        A list of Job objects
        """
        if verbose is not None:
            warnings.warn('verbose deprecated since 0.4.0')

        return self.cadctap.get_job_list(phases=phases, after=after, last=last,
                                         short_description=short_description)

    def _parse_result(self, result, verbose=None):
        return result

    def _args_to_payload(self, *args, **kwargs):
        # convert arguments to a valid requests payload
        # and force the coordinates to FK5 (assuming FK5/ICRS are
        # interchangeable) since RA/Dec are used below
        coordinates = commons.parse_coordinates(kwargs['coordinates']).fk5
        radius_deg = commons.radius_to_unit(kwargs['radius'], unit='degree')
        payload = {format: 'VOTable'}
        payload['query'] = \
            "SELECT * from caom2.Observation o join caom2.Plane p " \
            "ON o.obsID=p.obsID " \
            "WHERE INTERSECTS( " \
            "CIRCLE('ICRS', {}, {}, {}), position_bounds) = 1 AND " \
            "(quality_flag IS NULL OR quality_flag != 'junk')".\
            format(coordinates.ra.degree, coordinates.dec.degree, radius_deg)
        if 'collection' in kwargs and kwargs['collection']:
            payload['query'] = "{} AND collection='{}'".\
                format(payload['query'], kwargs['collection'])
        if 'data_product_type' in kwargs and kwargs['data_product_type']:
            payload['query'] = "{} AND dataProductType='{}'".\
                format(payload['query'], kwargs['data_product_type'])
        return payload


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


@static_vars(caps={})
def get_access_url(service, capability=None):
    """
    Returns the URL corresponding to a service by doing a lookup in the cadc
    registry. It returns the access URL corresponding to cookie authentication.
    :param service: the service the capability belongs to. It can be identified
    by a CADC uri ('ivo://cadc.nrc.ca/) which is looked up in the CADC registry
    or by the URL where the service capabilities is found.
    :param capability: uri representing the capability for which the access
    url is sought
    :return: the access url

    Note
    ------
    This function implements the functionality of a CADC registry as defined
    by the IVOA. It should be eventually moved to its own directory.

    Caching should be considered to reduce the number of remote calls to
    CADC registry
    """

    caps_url = ''
    if service.startswith('http'):
        if not capability:
            return service
        caps_url = service
    else:
        # get caps from the CADC registry
        if not get_access_url.caps:
            try:
                response = requests.get(conf.CADC_REGISTRY_URL)
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                logger.debug(
                    "ERROR getting the CADC registry: {}".format(str(err)))
                raise err
            for line in response.text.splitlines():
                if len(line) > 0 and not line.startswith('#'):
                    service_id, capabilies_url = line.split('=')
                    get_access_url.caps[service_id.strip()] = \
                        capabilies_url.strip()
        # lookup the service
        service_uri = service
        if not service.startswith('ivo'):
            # assume short form of CADC service
            service_uri = 'ivo://cadc.nrc.ca/{}'.format(service)
        if service_uri not in get_access_url.caps:
            raise AttributeError(
                "Cannot find the capabilities of service {}".format(service))
        # look up in the CADC reg for the service capabilities
        caps_url = get_access_url.caps[service_uri]
        if not capability:
            return caps_url
    try:
        response2 = requests.get(caps_url)
        response2.raise_for_status()
    except Exception as e:
        logger.debug(
            "ERROR getting the service capabilities: {}".format(str(e)))
        raise e

    soup = BeautifulSoup(response2.text, features="html5lib")
    for cap in soup.find_all('capability'):
        if cap.get("standardid", None) == capability:
            if len(cap.find_all('interface')) == 1:
                return cap.find_all('interface')[0].accessurl.text
            for i in cap.find_all('interface'):
                if hasattr(i, 'securitymethod'):
                    sm = i.securitymethod
                    if not sm or sm.get("standardid", None) is None or\
                       sm['standardid'] == "ivo://ivoa.net/sso#cookie":
                        return i.accessurl.text
    raise RuntimeError("ERROR - capabilitiy {} not found or not working with "
                       "anonymous or cookie access".format(capability))


Cadc = CadcClass()
