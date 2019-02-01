# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
CADC
====


Module to query the Canadian Astronomy Data Centre (CADC).
"""

import logging
import warnings

from ..utils.class_or_instance import class_or_instance
from ..utils import async_to_sync, commons
from ..query import BaseQuery
from bs4 import BeautifulSoup
from six import BytesIO
from astropy.io.votable import parse_single_table
from astroquery.cadc.cadctap.core import TapPlusCadc
from astroquery.cadc.cadctap.job import JobCadc
from . import conf

import requests

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

    def __init__(self, url=None, tap_plus_handler=None, verbose=False):
        """
        Initialize Cadc object

        Parameters
        ----------
        url : str, optional, default 'None;
            a url to use instead of the default
        tap_plus_handler : TAP/TAP+ object, optional, default 'None'
            connection to use instead of the default one created
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        Cadc object
        """

        super(CadcClass, self).__init__()
        if url is not None and tap_plus_handler is not None:
            raise AttributeError('Can not input both url and tap handler')

        if tap_plus_handler is None:
            if url is None:
                u = get_access_url(self.CADCTAP_SERVICE_URI)
                # remove capabilities endpoint to get to the service url
                u = u.rstrip('capabilities')
                self.__cadctap = TapPlusCadc(
                    url=u,
                    verbose=verbose)
            else:
                self.__cadctap = TapPlusCadc(url=url, verbose=verbose)
        else:
            self.__cadctap = tap_plus_handler

        self.data_link_url = get_access_url(
            self.CADCDATALINK_SERVICE_URI,
            "ivo://ivoa.net/std/DataLink#links-1.0")

    def login(self, user=None, password=None, certificate_file=None):
        """
        Login, set varibles to use for logging in

        Parameters
        ----------
        user : str, required if certificate is None
            username to login with
        password : str, required if user is set
            password to login with
        certificate : str, required if user is None
            path to certificate to use with logging in
        """
        login_url = get_access_url(self.CADCLOGIN_SERVICE_URI,
                                   'ivo://ivoa.net/std/UMS#login-0.1')
        return self.__cadctap.login(user=user, password=password,
                                    certificate_file=certificate_file,
                                    cookie_prefix=CADC_COOKIE_PREFIX,
                                    login_url=login_url,
                                    verbose=False)

    def logout(self, verbose=False):
        """
        Logout
        """
        return self.__cadctap.logout(verbose)

    @class_or_instance
    def query_region_async(self, coordinates, radius=0.016666666666667,
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

        request_payload = self._args_to_payload(coordinates=coordinates,
                                                radius=radius,
                                                collection=collection)
        # primarily for debug purposes, but also useful if you want to send
        # someone a URL linking directly to the data
        if get_query_payload:
            return request_payload
        response = self.run_query(request_payload['query'], operation='sync')
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
        response = self.run_query(
            "select * from caom2.Observation o join caom2.Plane p "
            "on o.obsID=p.obsID where lower(target_name) like '%{}%'".
            format(name.lower()), operation='sync')
        return response

    @class_or_instance
    def get_data_urls(self, query_result, include_auxiliaries=False):
        """
        Function to map the results of a CADC query into URLs to
        corresponding data that can be later downloaded.

        The function uses the IVOA DataLink Service
        (http://www.ivoa.net/documents/DataLink/) implemented at the CADC.
        It works directly with the results produced by Cadc.query_region and
        Cadc.query_name but in principle it can work with other query
        results produced with the Cadc query as long as the results
        contain the 'caomPublisherID' column. This column is part of the
        caom2.Plane table.

        Parameters
        ----------
        query_result : result returned by Cadc.query_region() or
                    Cadc.query_name(). In general, the result of any
                    CADC TAP query that contains the 'caomPublisherID' column
                    can be use here.
        include_auxiliaries : boolean
                    True to return URLs to auxiliary files such as
                    previews, False otherwise

        Returns
        -------
        A list of URLs to data.
        """

        if not query_result:
            raise AttributeError('Missing metadata argument')

        try:
            publisher_ids = query_result['caomPublisherID']
        except KeyError:
            raise AttributeError(
                'caomPublisherID column missing from query_result argument')
        result = []
        for pid in publisher_ids:
            response = self._request('GET', self.data_link_url,
                                     params={'ID': pid})
            response.raise_for_status()
            buffer = BytesIO(response.content)

            # at this point we don't need cutouts or other SODA services so
            # just get the urls from the response VOS table
            tb = parse_single_table(buffer)
            for row in tb.array:
                semantics = row['semantics'].decode('ascii')
                if semantics == '#this':
                    result.append(row['access_url'].decode('ascii'))
                elif row['access_url'] and include_auxiliaries:
                    result.append(row['access_url'].decode('ascii'))
        return result

    def get_tables(self, only_names=False, verbose=False):
        """
        Gets all public tables

        Parameters
        ----------
        only_names : bool, TAP+ only, optional, default 'False'
            True to load table names only
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of table objects
        """
        return self.__cadctap.load_tables(only_names, verbose)

    def get_table(self, table, verbose=False):
        """
        Gets the specified table

        Parameters
        ----------
        table : str, mandatory
            full qualified table name (i.e. schema name + table name)
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A table object
        """
        return self.__cadctap.load_table(table,
                                         verbose)

    def query_async(self, query):
        """
        Runs a query and returns results in Table format

        Parameters
        ----------
        query: str
            query: query to run

        Returns
        -------

        results in `~astropy.table.Table` format
        """
        return self.run_query(query, operation='sync')

    def run_query(self, query, operation, output_file=None,
                  output_format="votable", verbose=False,
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
        verbose : bool, optional, default 'False'
            flag to display information about the process
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
        if output_file is not None:
            save_to_file = True
        else:
            save_to_file = False
        if operation == 'sync':
            job = self.__cadctap.launch_job(
                query,
                None,
                output_file=output_file,
                output_format=output_format,
                verbose=verbose,
                dump_to_file=save_to_file,
                upload_resource=upload_resource,
                upload_table_name=upload_table_name)
            op = False
        elif operation == 'async':
            job = self.__cadctap.launch_job_async(
                query,
                None,
                output_file=output_file,
                output_format=output_format,
                verbose=verbose,
                dump_to_file=save_to_file,
                background=True,
                upload_resource=upload_resource,
                upload_table_name=upload_table_name)
            op = True
        cjob = JobCadc(async_job=op, query=job.parameters['query'],
                       connhandler=self.__cadctap._TapPlus__getconnhandler())
        cjob.jobid = job.jobid
        cjob.outputFile = job.outputFile
        cjob.set_response_status(job._Job__responseStatus,
                                 job._Job__responseMsg)
        cjob.remoteLocation = job.remoteLocation
        cjob.parameters['format'] = job.parameters['format']
        cjob._phase = job._phase
        if operation == 'async':
            if save_to_file:
                cjob.save_results(output_file, verbose)
            else:
                cjob.get_results()
        else:
            if job.results is not None:
                cjob.set_results(job.results)
        return cjob

    def load_async_job(self, jobid, verbose=False):
        """
        Loads an asynchronous job

        Parameters
        ----------
        jobid : str, mandatory
            job identifier
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A Job object
        """
        return self.__cadctap.load_async_job(jobid, verbose=verbose)

    def list_async_jobs(self, verbose=False):
        """
        Returns all the asynchronous jobs

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of Job objects
        """
        try:
            joblist = self.__cadctap.list_async_jobs(verbose)
            cadclist = []
            if joblist is not None:
                for job in joblist:
                    newJob = JobCadc(async_job=True,
                                     connhandler=job.connHandler)
                    newJob.jobid = job.jobid
                    cadclist.append(newJob)
        except requests.exceptions.HTTPError:
            return
        return cadclist

    def save_results(self, job, filename, verbose=False):
        """
        Saves job results

        Parameters
        ----------
        job : Job, mandatory
            job
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        return self.__cadctap.save_results(job, filename, verbose)

    def _parse_result(self, result, verbose=False):
        # result is a job
        # TODO check state of the job
        if result._phase != 'COMPLETED':
            raise RuntimeError('Query not completed')
        return result.results

    def _args_to_payload(self, *args, **kwargs):
        # convert arguments to a valid requests payload
        coordinates = commons.parse_coordinates(kwargs['coordinates'])
        radius = kwargs['radius']
        payload = {format: 'VOTable'}
        payload['query'] = \
            "SELECT * from caom2.Observation o join caom2.Plane p " \
            "ON o.obsID=p.obsID " \
            "WHERE INTERSECTS( " \
            "CIRCLE('ICRS', {}, {}, {}), position_bounds) = 1 AND " \
            "(quality_flag IS NULL OR quality_flag != 'junk')".\
            format(coordinates.ra.degree, coordinates.dec.degree, radius)
        if 'collection' in kwargs and kwargs['collection']:
            payload['query'] = "{} AND collection='{}'".\
                format(payload['query'], kwargs['collection'])
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

    query = BaseQuery()
    caps_url = ''
    if service.startswith('http'):
        if not capability:
            return service
        caps_url = service
    else:
        # get caps from the CADC registry
        if not get_access_url.caps:
            try:
                r = query._request('GET', conf.CADC_REGISTRY_URL)
                r.raise_for_status()
            except requests.exceptions.HTTPError as err:
                logger.debug(
                    "ERROR getting the CADC registry: {}".format(str(err)))
                raise err
            for line in r.text.splitlines():
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
        c = query._request('GET', caps_url)
        c.raise_for_status()
    except Exception as e:
        logger.debug(
            "ERROR getting the service capabilities: {}".format(str(e)))
        raise e

    soup = BeautifulSoup(c.text, features="html5lib")
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


Cadc = CadcClass
