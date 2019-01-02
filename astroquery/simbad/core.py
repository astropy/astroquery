# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Simbad query class for accessing the Simbad Service
"""
from __future__ import print_function
import copy
import re
import json
import os
from collections import namedtuple
import warnings
import astropy.units as u
from astropy.utils.data import get_pkg_data_filename
import astropy.coordinates as coord
from astropy.table import Table
import astropy.io.votable as votable
from six import BytesIO
from ..query import BaseQuery
from ..utils import commons
from ..exceptions import TableParseError, LargeQueryWarning
from . import conf
from ..utils.process_asyncs import async_to_sync

__all__ = ['Simbad', 'SimbadClass']


def validate_epoch(value):
    p = re.compile(r'^[JB]\d+[.]?\d+$', re.IGNORECASE)
    if p.match(value) is None:
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


def strip_field(f, keep_filters=False):
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
    if '(' in f:
        root = f[:f.find('(')]
        if (root in ('ra', 'dec', 'otype', 'id', 'coo', 'bibcodelist') or
                not keep_filters):
            return root

    # the overall else (default option)
    return f


error_regex = re.compile(r'(?ms)\[(?P<line>\d+)\]\s?(?P<msg>.+?)(\[|\Z)')
SimbadError = namedtuple('SimbadError', ('line', 'msg'))
VersionInfo = namedtuple('VersionInfo', ('major', 'minor', 'micro', 'patch'))


class SimbadResult(object):
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
                          (error.line, error.msg))

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
        super(SimbadVOTableResult, self).__init__(txt, verbose=verbose)

    @property
    def table(self):
        if self.__table is None:
            self.bytes = BytesIO(self.data.encode('utf8'))
            tbl = votable.parse_single_table(self.bytes, pedantic=False)
            self.__table = tbl.to_table()
            self.__table.convert_bytestring_to_unicode()
        return self.__table


bibcode_regex = re.compile(r'query\s+bibcode\s+(wildcard)?\s+([\w]*)')


class SimbadBibcodeResult(SimbadResult):
    """Bibliography-type Simbad result"""
    @property
    def table(self):
        bibcode_match = bibcode_regex.search(self.script)
        splitter = bibcode_match.group(2)
        ref_list = [splitter + ref for ref in self.data.split(splitter)][1:]
        max_len = max([len(r) for r in ref_list])
        table = Table(names=['References'], dtype=['S%i' % max_len])
        for ref in ref_list:
            table.add_row([ref])
        return table


class SimbadObjectIDsResult(SimbadResult):
    """Object identifier list Simbad result"""
    @property
    def table(self):
        max_len = max([len(i) for i in self.data.splitlines()])
        table = Table(names=['ID'], dtype=['S%i' % max_len])
        for id in self.data.splitlines():
            table.add_row([id.strip()])
        return table


@async_to_sync
class SimbadClass(BaseQuery):
    """
    The class for querying the Simbad web service.

    Note that SIMBAD suggests submitting no more than 6 queries per second; if
    you submit more than that, your IP may be temporarily blacklisted
    (http://simbad.u-strasbg.fr/simbad/sim-help?Page=sim-url)

    """
    SIMBAD_URL = 'http://' + conf.server + '/simbad/sim-script'
    TIMEOUT = conf.timeout
    WILDCARDS = {
        '*': 'Any string of characters (including an empty one)',
        '?': 'Any character (exactly one character)',
        '[abc]': ('Exactly one character taken in the list. '
                  'Can also be defined by a range of characters: [A-Z]'
                  ),
        '[^0-9]': 'Any (one) character not in the list.'}

    _ORDERED_WILDCARDS = ['*', '?', '[abc]', '[^0-9]']

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
    # <http://simbad.u-strasbg.fr/simbad/sim-help?Page=sim-fscript#VotableFields>
    # tried something for this in this ipython nb
    # <http://nbviewer.ipython.org/5851110>
    _VOTABLE_FIELDS = ['main_id', 'coordinates']

    def __init__(self):
        super(SimbadClass, self).__init__()
        self._VOTABLE_FIELDS = copy.copy(self._VOTABLE_FIELDS)

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
        for key in self._ORDERED_WILDCARDS:
            print("{key} : {value}\n".format(key=key,
                                             value=self.WILDCARDS[key]))
        return

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
        for field in list(sorted(fields_dict.keys())):
            print("{}".format(field))
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
            fields_dict = json.load(f)
            fields_dict = dict(
                ((strip_field(ff), fields_dict[ff])
                 for ff in fields_dict))

        for field in args:
            sf = strip_field(field)
            if sf not in fields_dict:
                raise KeyError("{field}: no such field".format(field=field))
            else:
                self._VOTABLE_FIELDS.append(field)

    def remove_votable_fields(self, *args, **kwargs):
        """
        Removes the specified field names from ``SimbadClass._VOTABLE_FIELDS``

        Parameters
        ----------
        list of field_names to be removed
        strip_params: bool
            If true, strip the specified keywords before removing them:
            e.g., ra(foo) would remove ra(bar) if this is True
        """
        strip_params = kwargs.pop('strip_params', False)

        if strip_params:
            sargs = [strip_field(a) for a in args]
            sfields = [strip_field(a) for a in self._VOTABLE_FIELDS]
        else:
            sargs = args
            sfields = self._VOTABLE_FIELDS
        absent_fields = set(sargs) - set(sfields)

        for b, f in list(zip(sfields, self._VOTABLE_FIELDS)):
            if b in sargs:
                self._VOTABLE_FIELDS.remove(f)

        for field in absent_fields:
            warnings.warn("{field}: this field is not set".format(field=field))

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

    def query_criteria_async(self, *args, **kwargs):
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
            Cache the query?

        Returns
        -------
        response : `requests.Response`
            Response of the query from the server
        """
        cache = kwargs.pop('cache', True)

        request_payload = self._args_to_payload(caller='query_criteria_async',
                                                *args, **kwargs)
        response = self._request("POST", self.SIMBAD_URL, data=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        return response

    def query_object(self, object_name, wildcard=False, verbose=False,
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

    def query_object_async(self, object_name, wildcard=False, cache=True,
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

    def query_objects(self, object_names, wildcard=False, verbose=False,
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

    def query_objects_async(self, object_names, wildcard=False, cache=True,
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

        Returns
        -------
        response : `requests.Response`
            Response of the query from the server
        """
        return self.query_object_async('\n'.join(object_names),
                                       wildcard=wildcard, cache=cache,
                                       get_query_payload=get_query_payload)

    def query_region_async(self, coordinates, radius=2*u.arcmin,
                           equinox=2000.0, epoch='J2000', cache=True,
                           get_query_payload=False):
        """
        Serves the same function as `query_region`, but
        only collects the response from the Simbad server and returns.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            the identifier or coordinates around which to query.
        radius : str or `~astropy.units.Quantity`, optional
            the radius of the region. If missing, set to default
            value of 2 arcmin.
        equinox : float, optional
            the equinox of the coordinates. If missing set to
            default 2000.0.
        epoch : str, optional
            the epoch of the input coordinates. Must be specified as
            [J|B] <epoch>. If missing, set to default J2000.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters.
            Defaults to `False`.

        Returns
        -------
        response : `requests.Response`
             Response of the query from the server.
        """

        equinox = validate_equinox(equinox)
        epoch = validate_epoch(epoch)

        base_query_str = "query coo {ra} {dec} radius={rad} frame={frame} equi={equinox}"

        if radius is None:
            radius = 2*u.arcmin

        header = self._get_query_header()
        footer = self._get_query_footer()

        ra, dec, frame = _parse_coordinates(coordinates)

        # handle the vector case
        if isinstance(ra, list):
            vector = True

            if len(ra) > 10000:
                warnings.warn("For very large queries, you may receive a "
                              "timeout error.  SIMBAD suggests splitting "
                              "queries with >10000 entries into multiple "
                              "threads", LargeQueryWarning)

            if len(set(frame)) > 1:
                raise ValueError("Coordinates have different frames")
            else:
                frame = set(frame).pop()

            if vector and _has_length(radius) and len(radius) == len(ra):
                # all good, continue
                pass
            elif vector and _has_length(radius) and len(radius) != len(ra):
                raise ValueError("Mismatch between radii and coordinates")
            elif vector and not _has_length(radius):
                radius = [_parse_radius(radius)] * len(ra)

            if vector:
                query_str = "\n".join([base_query_str
                                      .format(ra=ra_, dec=dec_, rad=rad_,
                                              frame=frame, equinox=equinox)
                                      for ra_, dec_, rad_ in zip(ra, dec, radius)])

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

    def query_catalog(self, catalog, verbose=False, cache=True,
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

    def query_catalog_async(self, catalog, cache=True, get_query_payload=False):
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

    def query_bibobj(self, bibcode, verbose=False, get_query_payload=False):
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

    def query_bibobj_async(self, bibcode, cache=True, get_query_payload=False):
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

        Returns
        -------
        response : `requests.Response`
             Response of the query from the server.

        """
        request_payload = self._args_to_payload(
            bibcode, caller='query_bibobj_async')

        if get_query_payload:
            return request_payload

        response = self._request("POST", self.SIMBAD_URL, data=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        return response

    def query_bibcode(self, bibcode, wildcard=False, verbose=False,
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

    def query_bibcode_async(self, bibcode, wildcard=False, cache=True,
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

    def query_objectids(self, object_name, verbose=False, cache=True,
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

    def query_objectids_async(self, object_name, cache=True,
                              get_query_payload=False):
        """
        Serves the same function as `query_objectids`, but
        only collects the response from the Simbad server and returns.

        Parameters
        ----------
        object_name : str
            name of object to be queried

        Returns
        -------
        response : `requests.Response`
             Response of the query from the server.

        """
        request_payload = dict(script="\n".join(('format object "%IDLIST"',
                                                 'query id %s' % object_name)))
        response = self._request("POST", self.SIMBAD_URL, data=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        return response

    def _get_query_header(self, get_raw=False):
        votable_fields = ','.join(self.get_votable_fields())
        # if get_raw is set then don't fetch as votable
        if get_raw:
            return ""
        votable_def = "votable {" + votable_fields + "}"
        votable_open = "votable open"
        return "\n".join([votable_def, votable_open])

    def _get_query_footer(self, get_raw=False):
        if get_raw:
            return ""
        votable_close = "votable close"

        return votable_close

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

        if self.ROW_LIMIT > 0:
            script = "set limit " + str(self.ROW_LIMIT)
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
        # be compatible with python3
        for key in list(kwargs):
            if not kwargs[key]:
                del kwargs[key]
        # join in the order specified otherwise results in error
        all_keys = ['radius', 'frame', 'equi', 'epoch']
        present_keys = [key for key in all_keys if key in kwargs]
        if caller == 'query_criteria_async':
            for k in kwargs:
                present_keys.append(k)
            # need ampersands to join args
            args_str = '&'.join([str(val) for val in args])
            if len(args) > 0 and len(present_keys) > 0:
                args_str += " & "
        else:
            args_str = ' '.join([str(val) for val in args])
        kwargs_str = ' '.join("{key}={value}".format(key=key,
                                                     value=kwargs[key])
                              for key in present_keys)

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
            content = result.text
            self.last_parsed_result = resultclass(content, verbose=verbose)
            if self.last_parsed_result.data is None:
                return None
            resulttable = self.last_parsed_result.table
            if len(resulttable) == 0:
                return None
        except Exception as ex:
            self.last_table_parse_error = ex
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
        c = commons.parse_coordinates(coordinates)
        # now c has some subclass of astropy.coordinate
        # get ra, dec and frame
        return _get_frame_coords(c)
    except (u.UnitsError, TypeError):
        raise ValueError("Coordinates not specified correctly")


def _has_length(x):
    # some objects have '__len__' attributes but have no len()
    try:
        len(x)
        return True
    except (TypeError, AttributeError):
        return False


def _get_frame_coords(c):
    if _has_length(c):
        # deal with vectors differently
        parsed = [_get_frame_coords(cc) for cc in c]
        return ([ra for ra, dec, frame in parsed],
                [dec for ra, dec, frame in parsed],
                [frame for ra, dec, frame in parsed])
    if c.frame.name == 'icrs':
        ra, dec = _to_simbad_format(c.ra, c.dec)
        return (ra, dec, 'ICRS')
    elif c.frame.name == 'galactic':
        lon, lat = (str(c.l.degree), str(c.b.degree))
        if lat[0] not in ['+', '-']:
            lat = '+' + lat
        return (lon, lat, 'GAL')
    elif c.frame.name == 'fk4':
        ra, dec = _to_simbad_format(c.ra, c.dec)
        return (ra, dec, 'FK4')
    elif c.frame.name == 'fk5':
        ra, dec = _to_simbad_format(c.ra, c.dec)
        return (ra, dec, 'FK5')
    else:
        raise ValueError("%s is not a valid coordinate" % c)


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
