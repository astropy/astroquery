# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Simbad query class for accessing the Simbad Service
"""

import re
import requests
import json
import os
from collections import namedtuple
from io import BytesIO
from functools import lru_cache
import warnings
import astropy.units as u
from astropy.utils import isiterable
from astropy.utils.data import get_pkg_data_filename
import astropy.coordinates as coord
from astropy.table import Table
import astropy.io.votable as votable

from astroquery.query import BaseQuery, BaseVOQuery
from astroquery.utils import commons, async_to_sync
from astroquery.exceptions import TableParseError, LargeQueryWarning, BlankResponseWarning

from pyvo.dal import TAPService
from . import conf


__all__ = ['Simbad', 'SimbadClass', 'SimbadBaseQuery']


def validate_epoch(value):
    pattern = re.compile(r'^[JB]\d+[.]?\d+$', re.IGNORECASE)
    if pattern.match(value) is None:
        raise ValueError("Epoch must be specified as [J|B]<epoch>.\n"
                         "Example: epoch='J2000'")
    return value


def validate_equinox(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValueError("Equinox must be a number")


def validate_epoch_decorator(func):
    """
    A method decorator that checks if the epoch value entered by the user
    is acceptable.
    """
    def wrapper(*args, **kwargs):
        if kwargs.get('epoch'):
            value = kwargs['epoch']
            validate_epoch(value)
        return func(*args, **kwargs)
    return wrapper


def validate_equinox_decorator(func):
    """
    A method decorator that checks if the equinox value entered by the user
    is acceptable.
    """
    def wrapper(*args, **kwargs):
        if kwargs.get('equinox'):
            value = kwargs['equinox']
            validate_equinox(value)
        return func(*args, **kwargs)
    return wrapper


def strip_field(field, keep_filters=False):
    """Helper tool: remove parameters from VOTABLE fields
    However, this should only be applied to a subset of VOTABLE fields:

     * ra
     * dec
     * otype
     * id
     * coo
     * bibcodelist

    *if* keep_filters is specified
    """
    if '(' in field:
        root = field[:field.find('(')]
        if (root in ('ra', 'dec', 'otype', 'id', 'coo', 'bibcodelist')
                or not keep_filters):
            return root

    # the overall else (default option)
    return field


def _adql_parameter(entry: str):
    """Replace single quotes by two single quotes.

    This should be applied to parameters used in ADQL queries.
    It is not a SQL injection protection: it just allows to search, for example,
    for authors with quotes in their names or titles/descriptions with apostrophes.

    Parameters
    ----------
    entry : str

    Returns
    -------
    str
    """
    return entry.replace("'", "''")


error_regex = re.compile(r'(?ms)\[(?P<line>\d+)\]\s?(?P<msg>.+?)(\[|\Z)')
SimbadError = namedtuple('SimbadError', ('line', 'msg'))
VersionInfo = namedtuple('VersionInfo', ('major', 'minor', 'micro', 'patch'))


class SimbadResult:
    __sections = ('script', 'console', 'error', 'data')

    def __init__(self, txt, verbose=False):
        self.__txt = txt
        self.__stringio = None
        self.__indexes = {}
        self.verbose = verbose
        self.exectime = None
        self.sim_version = None
        self.__split_sections()
        self.__parse_console_section()
        self.__warn()

    def __split_sections(self):
        for section in self.__sections:
            match = re.search(r'(?ims)^::%s:+?\r?$(?P<content>.*?)(^::|\Z)' %
                              section, self.__txt)
            if match:
                self.__indexes[section] = (match.start('content'),
                                           match.end('content'))

    def __parse_console_section(self):
        if self.console is None:
            return
        match = re.search(r'(?ims)total execution time: ([.\d]+?)\s*?secs',
                          self.console)
        if match:
            self.exectime = float(match.group(1))

        match = re.search(r'(?ms)SIMBAD(\d) rel (\d)[.](\d+)([^\d^\s])?',
                          self.console)
        if match:
            self.sim_version = VersionInfo(*match.groups(None))

    def __warn(self):
        for error in self.errors:
            warnings.warn("Warning: The script line number %i raised "
                          "an error (recorded in the `errors` attribute "
                          "of the result table): %s" %
                          (error.line, error.msg),
                          BlankResponseWarning
                          )

    def __get_section(self, section_name):
        if section_name in self.__indexes:
            return self.__txt[self.__indexes[section_name][0]:
                              self.__indexes[section_name][1]].strip()

    @property
    def script(self):
        return self.__get_section('script')

    @property
    def console(self):
        return self.__get_section('console')

    @property
    def error_raw(self):
        return self.__get_section('error')

    @property
    def data(self):
        return self.__get_section('data')

    @property
    def errors(self):
        result = []
        if self.error_raw is None:
            return result
        for err in error_regex.finditer(self.error_raw):
            result.append(SimbadError(int(err.group('line')),
                                      err.group('msg').replace('\n', ' ')))
        return result

    @property
    def nb_errors(self):
        if self.error_raw is None:
            return 0
        return len(self.errors)


class SimbadVOTableResult(SimbadResult):
    """VOTable-type Simbad result"""

    def __init__(self, txt, verbose=False, pedantic=False):
        self.__pedantic = pedantic
        self.__table = None
        if not verbose:
            commons.suppress_vo_warnings()
        super().__init__(txt, verbose=verbose)

    @property
    def table(self):
        if self.__table is None:
            self.bytes = BytesIO(self.data.encode('utf8'))
            tbl = votable.parse_single_table(self.bytes, verify='warn')
            self.__table = tbl.to_table()
            self.__table.convert_bytestring_to_unicode()
        return self.__table


bibcode_regex = re.compile(r'query\s+bibcode\s+(wildcard)?\s+([\w]*)')


class SimbadBibcodeResult(SimbadResult):
    """Bibliography-type Simbad result"""
    @property
    def table(self):
        splitter = bibcode_regex.search(self.script).group(2)
        ref_list = [[splitter + ref] for ref in self.data.split(splitter)[1:]]
        max_len = max(len(r[0]) for r in ref_list)
        return Table(rows=ref_list, names=['References'], dtype=[f"U{max_len}"])


class SimbadObjectIDsResult(SimbadResult):
    """Object identifier list Simbad result"""
    @property
    def table(self):
        split_lines = self.data.splitlines()
        ids = [[id.strip()] for id in split_lines]
        max_len = max(map(len, split_lines))
        return Table(rows=ids, names=['ID'], dtype=[f"S{max_len}"])


class SimbadBaseQuery(BaseQuery):
    """
    SimbadBaseQuery overloads the base query because we know that SIMBAD will
    sometimes blacklist users for exceeding rate limits.  This warning results
    in a "connection refused" error (error 61) instead of a more typical "error
    8" that you would get from not having an internet connection at all.
    """

    def _request(self, *args, **kwargs):
        try:
            response = super()._request(*args, **kwargs)
        except requests.exceptions.ConnectionError as ex:
            if 'Errno 61' in str(ex):
                extratext = ("\n\n"
                             "************************* \n"
                             "ASTROQUERY ADDED WARNING: \n"
                             "************************* \n"
                             "Error 61 received from SIMBAD server.  "
                             "This may indicate that you have been "
                             "blacklisted for exceeding the query rate limit."
                             "  See the astroquery SIMBAD documentation.  "
                             "Blacklists are generally cleared after ~1 hour.  "
                             "Please reconsider your approach, you may want "
                             "to use vectorized queries."
                             )
                ex.args[0].args = (ex.args[0].args[0] + extratext,)
            raise ex

        if response.status_code == 403:
            errmsg = ("Error 403: Forbidden.  You may get this error if you "
                      "exceed the SIMBAD server's rate limits.  Try again in "
                      "a few seconds or minutes.")
            raise requests.exceptions.HTTPError(errmsg)
        else:
            response.raise_for_status()

        return response


@async_to_sync
class SimbadClass(BaseVOQuery, SimbadBaseQuery):
    """
    The class for querying the Simbad web service.

    Note that SIMBAD suggests submitting no more than 6 queries per second; if
    you submit more than that, your IP may be temporarily blacklisted
    (https://simbad.cds.unistra.fr/guide/sim-url.htx)

    """
    SIMBAD_URL = 'https://' + conf.server + '/simbad/sim-script'
    TIMEOUT = conf.timeout
    WILDCARDS = {
        '*': 'Any string of characters (including an empty one)',
        '?': 'Any character (exactly one character)',
        '[abc]': ('Exactly one character taken in the list. '
                  'Can also be defined by a range of characters: [A-Z]'
                  ),
        '[^0-9]': 'Any (one) character not in the list.'}

    # query around not included since this is a subcase of query_region
    _function_to_command = {
        'query_object_async': 'query id',
        'query_region_async': 'query coo',
        'query_catalog_async': 'query cat',
        'query_criteria_async': 'query sample',
        'query_bibcode_async': 'query bibcode',
        'query_bibobj_async': 'query bibobj'
    }

    ROW_LIMIT = conf.row_limit

    # also find a way to fetch the votable fields table from
    # <https://simbad.cds.unistra.fr/guide/sim-fscript.htx#VotableFields>
    # tried something for this in this ipython nb
    # <http://nbviewer.ipython.org/5851110>
    _VOTABLE_FIELDS = ['main_id', 'coordinates']

    def __init__(self):
        super().__init__()
        self._VOTABLE_FIELDS = self._VOTABLE_FIELDS.copy()
        self._server = conf.server
        self._tap = None

    @property
    def server(self):
        """The Simbad mirror to use."""
        return self._server

    @server.setter
    def server(self, server: str):
        """Allows to switch server between Simbad mirrors.

        Parameters
        ----------
        server : str
            It should be one of `~astroquery.simbad.conf.servers_list`.
        """
        if server in conf.servers_list:
            self._server = server
        else:
            raise ValueError(f"'{server}' does not correspond to a Simbad server, "
                             f"the two existing ones are {conf.servers_list}.")

    @property
    def tap(self):
        """A `~pyvo.dal.TAPService` service for Simbad."""
        tap_url = f"https://{self.server}/simbad/sim-tap"
        # only creates a new tap instance if there are no existing one
        # or if the server property changed since the last getter call.
        if (not self._tap) or (self._tap.baseurl != tap_url):
            self._tap = TAPService(baseurl=tap_url, session=self._session)
        return self._tap

    @property
    @lru_cache(1)
    def hardlimit(self):
        """The maximum number of lines for Simbad's output.

        This property is cached to avoid calls to simbad's capability
        webpage each time the getter is called.
        """
        # replace stack of property and lru_cache by functools.cache_property when
        # astroquery drops python 3.7 support
        return self.tap.hardlimit

    def list_wildcards(self):
        """
        Displays the available wildcards that may be used in Simbad queries and
        their usage.

        Examples
        --------
        >>> from astroquery.simbad import Simbad
        >>> Simbad.list_wildcards()
        * : Any string of characters (including an empty one)...

        [^0-9] : Any (one) character not in the list.

        ? : Any character (exactly one character)

        [abc] : Exactly one character taken in the list.
                Can also be defined by a range of characters: [A-Z]
        """
        print("\n\n".join(f"{k} : {v}" for k, v in self.WILDCARDS.items()))

    def list_votable_fields(self):
        """
        Lists all the fields that can be fetched for a VOTable.

        Examples
        --------
        >>> from astroquery.simbad import Simbad
        >>> Simbad.list_votable_fields()
        --NOTES--...
        """
        # display additional notes:
        notes_file = get_pkg_data_filename(
            os.path.join('data', 'votable_fields_notes.json'))
        with open(notes_file, "r") as f:
            notes = json.load(f)
        print("--NOTES--\n")
        for i, line in list(enumerate(notes)):
            print("{lineno}. {msg}\n".format(lineno=i + 1, msg=line))

        dict_file = get_pkg_data_filename(
            os.path.join('data', 'votable_fields_dict.json'))
        with open(dict_file, "r") as f:
            fields_dict = json.load(f)

        print("Available VOTABLE fields:\n")
        for field in sorted(fields_dict.keys()):
            print(str(field))
        print("For more information on a field:\n"
              "Simbad.get_field_description ('field_name') \n"
              "Currently active VOTABLE fields:\n {0}"
              .format(self._VOTABLE_FIELDS))

    def get_field_description(self, field_name):
        """
        Displays a description of the VOTable field.

        Parameters
        ----------
        field_name : str
            the name of the field to describe. Must be one of those listed
            by `list_votable_fields`.

        Examples
        --------
        >>> from astroquery.simbad import Simbad
        >>> Simbad.get_field_description('main_id')
        main identifier of an astronomical object. It is the same as id(1)
        >>> Simbad.get_field_description('bibcodelist(y1-y2)')
        number of references. The parameter is optional and limit the count to
        the references between the years y1 and y2
        """
        # first load the dictionary from json
        dict_file = get_pkg_data_filename(
            os.path.join('data', 'votable_fields_dict.json'))
        with open(dict_file, "r") as f:
            fields_dict = json.load(f)

        try:
            print(fields_dict[field_name])
        except KeyError:
            raise KeyError("No such field_name")

    def get_votable_fields(self):
        """
        Display votable fields

        Examples
        --------
        >>> from astroquery.simbad import Simbad
        >>> Simbad.get_votable_fields()
        ['main_id', 'coordinates']
        """
        return self._VOTABLE_FIELDS

    def add_votable_fields(self, *args):
        """
        Sets fields to be fetched in the VOTable. Must be one of those listed
        by `list_votable_fields`.

        Parameters
        ----------
        list of field_names
        """
        dict_file = get_pkg_data_filename(
            os.path.join('data', 'votable_fields_dict.json'))

        with open(dict_file, "r") as f:
            fields_dict = {strip_field(k): v for k, v in json.load(f).items()}

        for field in args:
            sf = strip_field(field)
            if sf not in fields_dict:
                raise KeyError("{field}: no such field".format(field=field))
            else:
                self._VOTABLE_FIELDS.append(field)

    def remove_votable_fields(self, *args, strip_params=False):
        """
        Removes the specified field names from ``SimbadClass._VOTABLE_FIELDS``

        Parameters
        ----------
        list of field_names to be removed
        strip_params: bool, optional
            If true, strip the specified keywords before removing them:
            e.g., ra(foo) would remove ra(bar) if this is True
        """
        if strip_params:
            sargs = {strip_field(a) for a in args}
            sfields = [strip_field(a) for a in self._VOTABLE_FIELDS]
        else:
            sargs = set(args)
            sfields = self._VOTABLE_FIELDS

        for field in sargs.difference(sfields):
            warnings.warn("{field}: this field is not set".format(field=field))

        zipped_fields = zip(sfields, self._VOTABLE_FIELDS)
        self._VOTABLE_FIELDS = [f for b, f in zipped_fields if b not in sargs]

        # check if all fields are removed
        if not self._VOTABLE_FIELDS:
            warnings.warn("All fields have been removed. "
                          "Resetting to defaults.")
            self.reset_votable_fields()

    def reset_votable_fields(self):
        """
        resets VOTABLE_FIELDS to defaults
        """
        self._VOTABLE_FIELDS = ['main_id', 'coordinates']

    def query_criteria(self, *args, **kwargs):
        """
        Query SIMBAD based on any criteria.

        Parameters
        ----------
        args:
            String arguments passed directly to SIMBAD's script
            (e.g., 'region(box, GAL, 10.5 -10.5, 0.5d 0.5d)')
        kwargs:
            Keyword / value pairs passed to SIMBAD's script engine
            (e.g., {'otype':'SNR'} will be rendered as otype=SNR)

        Returns
        -------
        table : `~astropy.table.Table`
            Query results table
        """
        verbose = kwargs.pop('verbose', False)
        result = self.query_criteria_async(*args, **kwargs)
        return self._parse_result(result, SimbadVOTableResult, verbose=verbose)

    def query_criteria_async(self, *args, cache=True, **kwargs):
        """
        Query SIMBAD based on any criteria.

        Parameters
        ----------
        args:
            String arguments passed directly to SIMBAD's script
            (e.g., 'region(box, GAL, 10.5 -10.5, 0.5d 0.5d)')
        kwargs:
            Keyword / value pairs passed to SIMBAD's script engine
            (e.g., {'otype':'SNR'} will be rendered as otype=SNR)
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        response : `requests.Response`
            Response of the query from the server
        """

        request_payload = self._args_to_payload(caller='query_criteria_async',
                                                *args, **kwargs)
        response = self._request("POST", self.SIMBAD_URL, data=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        return response

    def query_object(self, object_name, *, wildcard=False, verbose=False,
                     get_query_payload=False):
        """
        Queries Simbad for the given object and returns the result as a
        `~astropy.table.Table`. Object names may also be specified with
        wildcard.  See examples below.

        Parameters
        ----------
        object_name : str
            name of object to be queried
        wildcard : boolean, optional
            When it is set to `True` it implies that the object is specified
            with wildcards. Defaults to `False`.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters.
            Defaults to `False`.

        Returns
        -------
        table : `~astropy.table.Table`
            Query results table
        """
        response = self.query_object_async(object_name, wildcard=wildcard,
                                           get_query_payload=get_query_payload)
        if get_query_payload:
            return response

        return self._parse_result(response, SimbadVOTableResult,
                                  verbose=verbose)

    def query_object_async(self, object_name, *, wildcard=False, cache=True,
                           get_query_payload=False):
        """
        Serves the same function as `query_object`, but
        only collects the response from the Simbad server and returns.

        Parameters
        ----------
        object_name : str
            name of object to be queried
        wildcard : boolean, optional
            When it is set to `True` it implies that the object is specified
            with wildcards. Defaults to `False`.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters.
            Defaults to `False`.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        response : `requests.Response`
            Response of the query from the server
        """
        request_payload = self._args_to_payload(object_name, wildcard=wildcard,
                                                caller='query_object_async')

        if get_query_payload:
            return request_payload

        response = self._request("POST", self.SIMBAD_URL, data=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        return response

    def query_objects(self, object_names, *, wildcard=False, verbose=False,
                      get_query_payload=False):
        """
        Queries Simbad for the specified list of objects and returns the
        results as a `~astropy.table.Table`. Object names may be specified
        with wildcards if desired.

        Parameters
        ----------
        object_names : sequence of strs
            names of objects to be queried
        wildcard : boolean, optional
            When `True`, the names may have wildcards in them. Defaults to
            `False`.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters.
            Defaults to `False`.

        Returns
        -------
        table : `~astropy.table.Table`
            Query results table
        """
        return self.query_object('\n'.join(object_names), wildcard=wildcard,
                                 get_query_payload=get_query_payload)

    def query_objects_async(self, object_names, *, wildcard=False, cache=True,
                            get_query_payload=False):
        """
        Same as `query_objects`, but only collects the response from the
        Simbad server and returns.

        Parameters
        ----------
        object_names : sequence of strs
            names of objects to be queried
        wildcard : boolean, optional
            When `True`, the names may have wildcards in them. Defaults to
            `False`.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters.
            Defaults to `False`.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        response : `requests.Response`
            Response of the query from the server
        """
        return self.query_object_async('\n'.join(object_names),
                                       wildcard=wildcard, cache=cache,
                                       get_query_payload=get_query_payload)

    def query_region_async(self, coordinates, radius=2*u.arcmin, *,
                           equinox=2000.0, epoch='J2000', cache=True,
                           get_query_payload=False):
        """
        Serves the same function as `query_region`, but
        only collects the response from the Simbad server and returns.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            the identifier or coordinates around which to query.
        radius : str or `~astropy.units.Quantity`
            the radius of the region.  Defaults to 2 arcmin.
        equinox : float, optional
            the equinox of the coordinates. If missing set to
            default 2000.0.
        epoch : str, optional
            the epoch of the input coordinates. Must be specified as
            [J|B] <epoch>. If missing, set to default J2000.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters.
            Defaults to `False`.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        response : `requests.Response`
             Response of the query from the server.
        """

        if radius is None:
            # this message is specifically for deprecated use of 'None' to mean 'Default'
            raise ValueError("Radius must be specified as an angle-equivalent quantity, not None")

        equinox = validate_equinox(equinox)
        epoch = validate_epoch(epoch)

        base_query_str = "query coo {ra} {dec} radius={rad} frame={frame} equi={equinox}"

        header = self._get_query_header()
        footer = self._get_query_footer()

        ra, dec, frame = _parse_coordinates(coordinates)

        # handle the vector case
        if isinstance(ra, list):
            if len(ra) > 10000:
                warnings.warn("For very large queries, you may receive a "
                              "timeout error.  SIMBAD suggests splitting "
                              "queries with >10000 entries into multiple "
                              "threads", LargeQueryWarning)

            if len(set(frame)) > 1:
                raise ValueError("Coordinates have different frames")
            else:
                frame = frame[0]

            # `radius` as `str` is iterable, but contains only one value.
            if isiterable(radius) and not isinstance(radius, str):
                if len(radius) != len(ra):
                    raise ValueError("Mismatch between radii and coordinates")
            else:
                radius = [_parse_radius(radius)] * len(ra)

            query_str = "\n".join(base_query_str
                                  .format(ra=ra_, dec=dec_, rad=rad_,
                                          frame=frame, equinox=equinox)
                                  for ra_, dec_, rad_ in zip(ra, dec, radius))

        else:
            radius = _parse_radius(radius)
            query_str = base_query_str.format(ra=ra, dec=dec, frame=frame,
                                              rad=radius, equinox=equinox)

        request_payload = {'script': "\n".join([header, query_str, footer])}

        if get_query_payload:
            return request_payload

        response = self._request("POST", self.SIMBAD_URL, data=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        return response

    def query_catalog(self, catalog, *, verbose=False, cache=True,
                      get_query_payload=False):
        """
        Queries a whole catalog.

        Results may be very large -number of rows
        should be controlled by configuring `SimbadClass.ROW_LIMIT`.

        Parameters
        ----------
        catalog : str
            the name of the catalog.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters.
            Defaults to `False`.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        table : `~astropy.table.Table`
            Query results table
        """
        response = self.query_catalog_async(catalog, cache=cache,
                                            get_query_payload=get_query_payload)
        if get_query_payload:
            return response

        return self._parse_result(response, SimbadVOTableResult,
                                  verbose=verbose)

    def query_catalog_async(self, catalog, *, cache=True, get_query_payload=False):
        """
        Serves the same function as `query_catalog`, but
        only collects the response from the Simbad server and returns.

        Parameters
        ----------
        catalog : str
            the name of the catalog.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters.
            Defaults to `False`.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        response : `requests.Response`
             Response of the query from the server.

        """
        request_payload = self._args_to_payload(catalog,
                                                caller='query_catalog_async')
        if get_query_payload:
            return request_payload

        response = self._request("POST", self.SIMBAD_URL, data=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        return response

    def query_bibobj(self, bibcode, *, verbose=False, get_query_payload=False):
        """
        Query all the objects that are contained in the article specified by
        the bibcode, and return results as a `~astropy.table.Table`.

        Parameters
        ----------
        bibcode : str
            the bibcode of the article
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters.
            Defaults to `False`.

        Returns
        -------
        table : `~astropy.table.Table`
            Query results table
        """
        response = self.query_bibobj_async(bibcode,
                                           get_query_payload=get_query_payload)
        if get_query_payload:
            return response

        return self._parse_result(response, SimbadVOTableResult,
                                  verbose=verbose)

    def query_bibobj_async(self, bibcode, *, cache=True, get_query_payload=False):
        """
        Serves the same function as `query_bibobj`, but only collects the
        response from the Simbad server and returns.

        Parameters
        ----------
        bibcode : str
            the bibcode of the article
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters.
            Defaults to `False`.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        response : `requests.Response`
             Response of the query from the server.

        """
        request_payload = self._args_to_payload(bibcode, caller='query_bibobj_async')

        if get_query_payload:
            return request_payload

        response = self._request("POST", self.SIMBAD_URL, data=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        return response

    def query_bibcode(self, bibcode, *, wildcard=False, verbose=False,
                      cache=True, get_query_payload=False):
        """
        Queries the references corresponding to a given bibcode, and returns
        the results in a `~astropy.table.Table`. Wildcards may be used to
        specify bibcodes.

        Parameters
        ----------
        bibcode : str
            the bibcode of the article
        wildcard : boolean, optional
            When it is set to `True` it implies that the object is specified
            with wildcards. Defaults to `False`.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters.
            Defaults to `False`.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        table : `~astropy.table.Table`
            Query results table

        """
        response = self.query_bibcode_async(bibcode, wildcard=wildcard,
                                            cache=cache,
                                            get_query_payload=get_query_payload)

        if get_query_payload:
            return response

        return self._parse_result(response, SimbadBibcodeResult,
                                  verbose=verbose)

    def query_bibcode_async(self, bibcode, *, wildcard=False, cache=True,
                            get_query_payload=False):
        """
        Serves the same function as `query_bibcode`, but
        only collects the response from the Simbad server and returns.

        Parameters
        ----------
        bibcode : str
            the bibcode of the article
        wildcard : boolean, optional
            When it is set to `True` it implies that the object is specified
            with wildcards. Defaults to `False`.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters.
            Defaults to `False`.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        response : `requests.Response`
             Response of the query from the server.

        """
        request_payload = self._args_to_payload(
            bibcode, wildcard=wildcard,
            caller='query_bibcode_async', get_raw=True)

        if get_query_payload:
            return request_payload

        response = self._request("POST", self.SIMBAD_URL, cache=cache,
                                 data=request_payload, timeout=self.TIMEOUT)

        return response

    def query_objectids(self, object_name, *, verbose=False, cache=True,
                        get_query_payload=False):
        """
        Query Simbad with an object name, and return a table of all
        names associated with that object in a `~astropy.table.Table`.

        Parameters
        ----------
        object_name : str
            name of object to be queried
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters.
            Defaults to `False`.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        table : `~astropy.table.Table`
            Query results table

        """
        response = self.query_objectids_async(object_name, cache=cache,
                                              get_query_payload=get_query_payload)
        if get_query_payload:
            return response

        return self._parse_result(response, SimbadObjectIDsResult,
                                  verbose=verbose)

    def query_objectids_async(self, object_name, *, cache=True,
                              get_query_payload=False):
        """
        Serves the same function as `query_objectids`, but
        only collects the response from the Simbad server and returns.

        Parameters
        ----------
        object_name : str
            name of object to be queried
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        response : `requests.Response`
             Response of the query from the server.

        """
        request_payload = dict(script="\n".join(('format object "%IDLIST"',
                                                 'query id %s' % object_name)))

        if get_query_payload:
            return request_payload

        response = self._request("POST", self.SIMBAD_URL, data=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)

        return response

    def list_tables(self, *, get_adql=False):
        """The names and descriptions of the tables in SIMBAD.

        Parameters
        ----------
        get_adql : bool, optional
            Returns the ADQL string instead of querying SIMBAD.

        Returns
        -------
        `~astropy.table.Table`
        """
        query = ("SELECT table_name, description"
                 " FROM TAP_SCHEMA.tables"
                 " WHERE schema_name = 'public'")
        if get_adql:
            return query
        return self.query_tap(query)

    def list_columns(self, *tables: str, keyword=None, get_adql=False):
        """
        Get the list of SIMBAD columns.

        Add tables names to restrict to some tables. Call the function without
        any parameter to get all columns names from all tables. The keyword argument
        looks for columns in the selected Simbad tables that contain the
        given keyword. The keyword search is not case-sensitive.

        Parameters
        ----------
        *tables : str, optional
            Add tables names as strings to restrict to these tables columns.
        keyword : str, optional
            A keyword to look for in column names, table names, or descriptions.
        get_adql : bool, optional
            Returns the ADQL string instead of querying SIMBAD.

        Examples
        --------
        >>> from astroquery.simbad import Simbad
        >>> Simbad.list_columns("ids", "ident") # doctest: +REMOTE_DATA
        <Table length=4>
        table_name column_name datatype ...  unit    ucd
          object      object    object  ... object  object
        ---------- ----------- -------- ... ------ -------
             ident          id  VARCHAR ...        meta.id
             ident      oidref   BIGINT ...
               ids         ids  VARCHAR ...        meta.id
               ids      oidref   BIGINT ...


        >>> from astroquery.simbad import Simbad
        >>> Simbad.list_columns(keyword="filter") # doctest: +REMOTE_DATA
        <Table length=5>
         table_name column_name   datatype  ...  unit           ucd
           object      object      object   ... object         object
        ----------- ----------- ----------- ... ------ ----------------------
             filter description UNICODECHAR ...        meta.note;instr.filter
             filter  filtername     VARCHAR ...                  instr.filter
             filter        unit     VARCHAR ...                     meta.unit
               flux      filter     VARCHAR ...                  instr.filter
        mesDiameter      filter        CHAR ...                  instr.filter

        >>> from astroquery.simbad import Simbad
        >>> Simbad.list_columns("basic", keyword="object") # doctest: +REMOTE_DATA
        <Table length=4>
        table_name column_name datatype ...  unit          ucd
          object      object    object  ... object        object
        ---------- ----------- -------- ... ------ -------------------
             basic     main_id  VARCHAR ...          meta.id;meta.main
             basic   otype_txt  VARCHAR ...                  src.class
             basic         oid   BIGINT ...        meta.record;meta.id
             basic       otype  VARCHAR ...                  src.class
        """
        query = ("SELECT table_name, column_name, datatype, description, unit, ucd"
                 " FROM TAP_SCHEMA.columns"
                 " WHERE table_name NOT LIKE 'TAP_SCHEMA.%'")
        # select the tables
        if len(tables) == 1:
            query += f" AND table_name = '{tables[0]}'"
        elif len(tables) > 1:
            query += f" AND table_name IN {tables}"
        # add the keyword condition
        if keyword is not None:
            condition = f"LIKE LOWERCASE('%{_adql_parameter(keyword)}%')"
            query += (f" AND ( (LOWERCASE(column_name) {condition})"
                      f" OR (LOWERCASE(description) {condition})"
                      f" OR (LOWERCASE(table_name) {condition}))")
        query += " ORDER BY table_name, principal DESC, column_name"
        if get_adql:
            return query
        return self.query_tap(query)

    def list_linked_tables(self, table: str, *, get_adql=False):
        """
        Expose the tables that can be non-obviously linked with the given table.

        This list contains only the links where the column names are not the same in the
        two tables. For example every ``oidref`` column of any table can be joined with
        any other ``oidref``. The same goes for every ``otype`` column even if this is not
        returned by this method.

        Parameters
        ----------
        table : str
            One of SIMBAD's tables name
        get_adql : bool, optional
            Returns the ADQL string instead of querying SIMBAD.

        Returns
        -------
        `~astropy.table.Table`
            The information necessary to join the given table to an other.

        Examples
        --------
        >>> from astroquery.simbad import Simbad
        >>> Simbad.list_linked_tables("otypes") # doctest: +REMOTE_DATA
        <Table length=2>
        from_table from_column target_table target_column
          object      object      object        object
        ---------- ----------- ------------ -------------
          otypedef       otype       otypes         otype
            otypes      oidref        basic           oid
        """
        query = ("SELECT from_table, from_column, target_table, target_column"
                 " FROM TAP_SCHEMA.key_columns JOIN TAP_SCHEMA.keys USING (key_id)"
                 f" WHERE (from_table = '{_adql_parameter(table)}')"
                 f" OR (target_table = '{_adql_parameter(table)}')")
        if get_adql:
            return query
        return self.query_tap(query)

    @lru_cache(256)
    def _cached_query_tap(self, query: str, *, maxrec=10000):
        """Cache version of query TAP

        This private method is called when query_tap is executed without an
        ``uploads`` extra keyword argument. This is a work around because
        `~astropy.table.Table` objects are not hashable and thus cannot
        be used as arguments for a function decorated with lru_cache.

        Parameters
        ----------
        query : str
            A string containing the query written in the
            Astronomical Data Query Language (ADQL).
        maxrec : int, optional
            The number of records to be returned. Its maximum value is 2000000.

        Returns
        -------
        `~astropy.table.Table`
            The response returned by Simbad.
        """
        return self.tap.run_async(query, maxrec=maxrec).to_table()

    def query_tap(self, query: str, *, maxrec=10000, **uploads):
        """
        Query Simbad TAP service.

        Parameters
        ----------
        query : str
            A string containing the query written in the
            Astronomical Data Query Language (ADQL).
        maxrec : int, default: 10000
            The number of records to be returned. Its maximum value is given by
            `~astroquery.simbad.SimbadClass.hardlimit`.
        uploads : `~astropy.table.Table` | `~astropy.io.votable.tree.VOTableFile` | `~pyvo.dal.DALResults`
            Any number of local tables to be used in the *query*. In the *query*, these tables
            are referred as *TAP_UPLOAD.table_alias* where *TAP_UPLOAD* is imposed and *table_alias*
            is the keyword name you chose. The maximum number of lines for the uploaded tables is 200000.

        Returns
        -------
        `~astropy.table.Table`
            The response returned by Simbad.

        Notes
        -----
        A TAP (Table Access Protocol) service allows to query data tables with
        queries written in ADQL (Astronomical Data Query Language), a flavor
        of the more general SQL (Structured Query Language).
        For more documentation about writing ADQL queries, you can read its official
        documentation (`ADQL documentation <https://ivoa.net/documents/ADQL/index.html>`__)
        or the `Simbad ADQL cheat sheet <http://simbad.cds.unistra.fr/simbad/tap/help/adqlHelp.html>`__.
        See also: a `graphic representation of Simbad's tables and their relations
        <http://simbad.cds.unistra.fr/simbad/tap/tapsearch.html>`__.

        See also
        --------
        list_tables : The list of SIMBAD's tables.
        list_columns : SIMBAD's columns list, can be restricted to some tables and some keyword.
        list_linked_tables : Given a table, expose non-obvious possible joins with other tables.

        Examples
        --------

        To see the five oldest papers referenced in Simbad

        >>> from astroquery.simbad import Simbad
        >>> Simbad.query_tap("SELECT top 5 bibcode, title "
        ...                  "FROM ref ORDER BY bibcode") # doctest: +REMOTE_DATA
        <Table length=5>
              bibcode       ...
               object       ...
        ------------------- ...
        1850CDT..1784..227M ...
        1857AN.....45...89S ...
        1861MNRAS..21...68B ...
        1874MNRAS..34...75S ...
        1877AN.....89...13W ...

        Get the type for a list of objects

        >>> from astroquery.simbad import Simbad
        >>> Simbad.query_tap("SELECT main_id, otype"
        ...                  " FROM basic WHERE main_id IN ('m10', 'm13')") # doctest: +REMOTE_DATA
        <Table length=2>
        main_id otype
         object object
        ------- ------
          M  10    GlC
          M  13    GlC

        Upload a table to use in a query

        >>> from astroquery.simbad import Simbad
        >>> from astropy.table import Table
        >>> letters_table = Table([["a", "b", "c"]], names=["alphabet"])
        >>> Simbad.query_tap("SELECT TAP_UPLOAD.my_table_name.* from TAP_UPLOAD.my_table_name",
        ...                  my_table_name=letters_table) # doctest: +REMOTE_DATA
        <Table length=3>
        alphabet
         object
        --------
               a
               b
               c
        """
        if maxrec > Simbad.hardlimit:
            raise ValueError(f"The maximum number of records cannot exceed {Simbad.hardlimit}.")
        if query.count("'") % 2:
            raise ValueError("Query string contains an odd number of single quotes."
                             " Escape the unpaired single quote by doubling it.\n"
                             "ex: 'Barnard's galaxy' -> 'Barnard''s galaxy'.")
        if uploads == {}:
            return self._cached_query_tap(query, maxrec=maxrec)
        return self.tap.run_async(query, maxrec=maxrec, uploads=uploads).to_table()

    def _get_query_header(self, get_raw=False):
        # if get_raw is set then don't fetch as votable
        if get_raw:
            return ""
        row_limit = f"set limit {self.ROW_LIMIT}\n" if self.ROW_LIMIT > 0 else ""
        return f"{row_limit}votable {{{','.join(self.get_votable_fields())}}}\nvotable open"

    def _get_query_footer(self, get_raw=False):
        return "" if get_raw else "votable close"

    @validate_epoch_decorator
    @validate_equinox_decorator
    def _args_to_payload(self, *args, **kwargs):
        """
        Takes the arguments from any of the query functions and returns a
        dictionary that can be used as the data for an HTTP POST request.
        """

        script = ""
        caller = kwargs['caller']
        del kwargs['caller']
        get_raw = kwargs.pop('get_raw', False)
        command = self._function_to_command[caller]

        votable_header = self._get_query_header(get_raw)
        votable_footer = self._get_query_footer(get_raw)

        script = "\n".join([script, votable_header, command])
        using_wildcard = False
        if kwargs.get('wildcard'):
            # necessary to have a space at the beginning and end
            script += " wildcard "
            del kwargs['wildcard']
            using_wildcard = True
        # now append args and kwds as per the caller
        # if caller is query_region_async write coordinates as separate ra dec
        # rename equinox to equi as required by SIMBAD script
        if kwargs.get('equinox'):
            kwargs['equi'] = kwargs['equinox']
            del kwargs['equinox']
        # remove default None from kwargs
        kwargs = {key: value for key, value in kwargs.items() if value is not None}
        # join in the order specified otherwise results in error
        all_keys = ['radius', 'frame', 'equi', 'epoch']
        present_keys = [key for key in all_keys if key in kwargs]
        if caller == 'query_criteria_async':
            present_keys.extend(kwargs)
            # need ampersands to join args
            args_str = '&'.join([str(val) for val in args])
            if args and present_keys:
                args_str += " & "
        else:
            args_str = ' '.join([str(val) for val in args])
        kwargs_str = ' '.join(f"{key}={kwargs[key]}" for key in present_keys)

        # For the record, I feel dirty for writing this wildcard-case hack.
        # This entire function should be refactored when someone has time.
        allargs_str = ' '.join([" ", args_str, kwargs_str, "\n"])
        if using_wildcard:
            allargs_str = allargs_str.lstrip()

        script += allargs_str
        script += votable_footer
        return dict(script=script)

    def _parse_result(self, result, resultclass=SimbadVOTableResult,
                      verbose=False):
        """
        Instantiate a Simbad*Result class and try to parse the
        response with the .table property/method, then return the
        resulting table.  If data is not retrieved or the resulting
        table is empty, return None.  In case of problems, save
        intermediate results for further debugging.
        """
        self.last_response = result
        try:
            content = result.content.decode('utf-8')
            self.last_parsed_result = resultclass(content, verbose=verbose)
            if self.last_parsed_result.data is None:
                return None
            resulttable = self.last_parsed_result.table
            if len(resulttable) == 0:
                return None
        except Exception as ex:
            self.last_table_parse_error = ex
            try:
                self._last_query.remove_cache_file(self.cache_location)
            except OSError:
                # this is allowed: if `cache` was set to False, this
                # won't be needed
                pass
            raise TableParseError("Failed to parse SIMBAD result! The raw "
                                  "response can be found in "
                                  "self.last_response, and the error in "
                                  "self.last_table_parse_error. The attempted"
                                  " parsed result is in "
                                  "self.last_parsed_result.\n "
                                  "Exception: " + str(ex))
        resulttable.errors = self.last_parsed_result.errors
        return resulttable


def _parse_coordinates(coordinates):
    try:
        coordinates = commons.parse_coordinates(coordinates)
        # now c has some subclass of astropy.coordinate
        # get ra, dec and frame
        return _get_frame_coords(coordinates)
    except (u.UnitsError, TypeError):
        raise ValueError("Coordinates not specified correctly")


def _get_frame_coords(coordinates):
    if isiterable(coordinates):
        # deal with vectors differently
        parsed = [_get_frame_coords(cc) for cc in coordinates]
        return ([ra for ra, dec, frame in parsed],
                [dec for ra, dec, frame in parsed],
                [frame for ra, dec, frame in parsed])
    if coordinates.frame.name == 'icrs':
        ra, dec = _to_simbad_format(coordinates.ra, coordinates.dec)
        return (ra, dec, 'ICRS')
    elif coordinates.frame.name == 'galactic':
        lon, lat = (str(coordinates.l.degree), str(coordinates.b.degree))
        if lat[0] not in ['+', '-']:
            lat = '+' + lat
        return (lon, lat, 'GAL')
    elif coordinates.frame.name == 'fk4':
        ra, dec = _to_simbad_format(coordinates.ra, coordinates.dec)
        return (ra, dec, 'FK4')
    elif coordinates.frame.name == 'fk5':
        ra, dec = _to_simbad_format(coordinates.ra, coordinates.dec)
        return (ra, dec, 'FK5')
    else:
        raise ValueError("%s is not a valid coordinate" % coordinates)


def _to_simbad_format(ra, dec):
    # This irrelevantly raises the exception
    # "AttributeError: Angle instance has no attribute 'hour'"
    ra = ra.to_string(u.hour, sep=':')
    dec = dec.to_string(u.degree, sep=':', alwayssign='True')
    return (ra.lstrip(), dec.lstrip())


def _parse_radius(radius):
    try:
        angle = coord.Angle(radius)
        # find the most appropriate unit - d, m or s
        nonzero_indices = [i for (i, val) in enumerate(angle.dms)
                           if int(val) > 0]
        if len(nonzero_indices) > 0:
            index = min(nonzero_indices)
        else:
            index = 2  # use arcseconds when radius smaller than 1 arcsecond
        unit = ('d', 'm', 's')[index]
        if unit == 'd':
            return str(angle.degree) + unit
        if unit == 'm':
            return str(angle.arcmin) + unit
        if unit == 's':
            return str(angle.arcsec) + unit
    except (coord.errors.UnitsError, AttributeError):
        raise ValueError("Radius specified incorrectly")


Simbad = SimbadClass()
