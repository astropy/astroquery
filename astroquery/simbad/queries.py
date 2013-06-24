# Licensed under a 3-clause BSD style license - see LICENSE.rst

import urllib
import urllib2
from .parameters import ValidatedAttribute
from . import parameters
from .result import SimbadResult
from .simbad_votable import VoTableDef
#---------------------------- move to a separate core.py-------------------------------------------------
# TODO  
# Still need to test all the implementations. None have been tried out yet!
# Also yet to implement _parse_result and improve validate functions

import re
from ..exceptions import TimeoutError
from ..query import BaseQuery
from ..utils.class_or_instance import class_or_instance
import astropy.units as u
import astropy.utils.data as aud
import astropy.coordinates as coord
from . import SIMBAD_SERVER 
__all__ = ['QueryId',
            'QueryAroundId',
            'QueryCat',
            'QueryCoord',
            'QueryBibobj',
            'QueryMulti',
            'Simbad'
            ]

# add this to a top level common utils?
def send_request(url, data, timeout):
    try:
        response = requests.post(url, data=data, timeout=timeout)
        return response
    except requests.exceptions.Timeout:
            raise TimeoutError("Query timed out, time elapsed {time}s".
                               format(time=timeout))
    except requests.exceptions.RequestException:
            raise Exception("Query failed\n")
        

class Simbad(BaseQuery): 
    SIMBAD_URL = 'http://' + SIMBAD_SERVER() + '/simbad/sim-script' 
    WILDCARDS = {
                 '*' : 'Any string of characters (including an empty one)',
                 '?' : 'Any character (exactly one character)',
                 '[abc]' : ('Exactly one character taken in the list. '
                            'Can also be defined by a range of characters: [A-Z]'
                            ),
                 '[^0-9]' : 'Any (one) character not in the list.'
                 
                 }
    
     # query around not included since this is a subcase of query_region
    _function_to_command = {
                            'query_object_async' : 'query id',
                            'query_region_async' : 'query coo',
                            'query_catalog_async' : 'query cat',
                            'query_bibcode_async' : 'query bibcode',
                            'query_bibobj_async' : 'query bibobj'
                            }
    
    # make this configurable
    # also find a way to fetch the votable fields table from <http://simbad.u-strasbg.fr/simbad/sim-help?Page=sim-fscript#VotableFields>
    # tried something for this in this ipython nb <http://nbviewer.ipython.org/5851110>
    VOTABLE_FIELDS = [main_id, coordinates] 
    
    
    ROW_LIMIT = 0 # make this configurable. (0 sets to maximum)
    
    
     @class_or_instance
     def query_object(self, object_name, wildcard=None):
         result = self.query_object_async(object_name, wilcard=wildcard)
         return self._parse_result(result)
     
     @class_or_instance
     def query_object_async(self, object_name, wildcard=None):
         request_payload = self._args_to_payload(object_name, wildcard=wildcard, caller='query_object_async')
         response = send_request(SIMBAD_URL, data=request_payload)
         return result
     
     @class_or_instance
     def query_region(self, coordinates, radius=None, frame=None, equinox=None, epoch=None):
         # if the identifier is given rather than the coordinates, convert to coordinates
         result = self.query_region(coordinates, radius=radius, frame=frame, 
                                    equinox=equinox, epoch=epoch)
         return self.parse_result(result)
     
     @class_or_instance
     def query_region_async(self, coordinates, radius=None, frame=None, equinox=None, epoch=None):
         request_payload = self._args_to_payload(coordinates, radius=radius, frame=frame, 
                                                 equinox=equinox, epoch=epoch, caller='query_region_async')
         response =  send_request(SIMBAD_URL, data=request_payload)
         return response
     
     @class_or_instance
     def query_catalog(self, catalog):
         result = self.query_catalog_async(catalog)
         return self._parse_result(result)
     
     @class_or_instance
     def query_catalog_async(self, catalog):
         request_payload = self._args_to_payload(catalog, caller='query_catalog_async')
         response = send_request(SIMBAD_URL, data=request_payload)
         return response
     
     @class_or_instance
     def query_bibobj(self, bibcode):
         result = self.query_bibobj_async(bibcode)
         return self._parse_result(result)
     
     @class_or_instance
     def query_bibobj_async(self, bibcode):
         request_payload = self._args_to_payload(bibcode, caller='query_bibobj_async')
         response = send_request(SIMBAD_URL, data=request_payload)
         return response
     
     @class_or_instance
     def query_bibcode(self, bibcode, wildcard=None):
         result = self.query_bibcode_async(bibcode, wildcard=wildcard)
         return self._parse_result(result)
     
     @class_or_instance
     def query_bibcode_async(self, bibcode, wildcard=None):
         request_payload = self._args_to_payload(bibcode, wildcard=wildcard, caller='query_bibcode_async' )
         response = send_request(SIMBAD_URL, data=request_payload)
         return response
     
     @class_or_instance
     def list_catalogs(self):
         pass
     
     @class_or_instance
     @_validate_epoch
     @_validate_equinox
     def _args_to_payload(self, *args, **kwargs):
         script=""
         caller = kwargs[caller]
         del kwargs[caller]
         command = self._function_to_command[caller]
         votable_fields = ','.join(Simbad.VOTABLE_FIELDS)
         votable_def = "votable {" + votable_fields + "}"
         votable_open = "votable open"
         votable_close = "votable close"
         if Simbad.ROW_LIMIT:
             script = "set limit "+str(Simbad.ROW_LIMIT)
         script = "\n".join([script, votable_def, votable_open, command])
         if kwargs.get('wildcard'):
             script += " wildcard" #necessary to have a space at the beginning
             del kwargs['wildcard']
         # now append args and kwds as per the caller
         # if caller is query_region_async write coordinates as separate ra dec
         if caller == 'query_region_async':
             coordinates = args[0]
             del args[0]
             ra, dec, frame = _parse_coordinates(coordinates)
             args = [ra, dec]
             kwargs['frame'] = frame
             if kwargs.get('radius'):
                 kwargs['radius'] = _parse_radius(kwargs['radius'])
        args_str = ' '.join([str(val) for val in args])
        # remove default None from kwargs
        # be compatible with python3
        for key in list(kwargs.keys()):
            if not kwargs[key]:
                del kwargs[key]
        kwargs_str = ' '.join("{key}={value}".format(key=key, value=value) for key,value in kwargs.items())
        script += ' '.join([" ", args_str, kwargs_str, "\n"]) 
        script += votable_close
        return dict(script=script)
    
     @class_or_instance
     def _parse_result(self, result):
         pass


  
def _parse_coordinates(coordinates):
    # SGAL, ECL not supported by astropy.coordinates yet?
    # check if it is an identifier rather than coordinates
    if isinstance(coordinates, basestring):
        try:
            c = coord.ICRSCoordinates.from_name(coordinates)
        except coord.name_resolve.NameResolveError:
            #check if they are coordinates expressed as a string
            # otherwise UnitsException will be raised
            c = coord.ICRSCoordinates(coordinates, unit=(None, None))
     else:
         # it must be an astropy.coordinates coordinate object
         assert isinstance(coordinates, coord.SphericalCoordinatesBase)
         c = coordinates
    # now c has some subclass of astropy.coordinate
    # get ra, dec and frame
    return _get_frame_coords(c)
    #get ra and dec
    
      
def _get_frame_coords(c):
    if isinstance(c, coord.ICRSCoordinates):
        ra = _to_simbad_format(c.ra)
        dec = _to_simbad_format(c.dec)
        return (ra, dec, 'ICRS')
    if isinstance(c, coord.GalacticCoordinates):
        ra = _to_simbad_format(c.latangle)
        dec = _to_simbad_format(c.lonangle)
        return 'GAL'
    if isinstance(c, coord.FK4Coordinates):
        ra = _to_simbad_format(c.ra)
        dec = _to_simbad_format(c.dec)
        return 'FK4'
    if isinstance(c, coord.FK5Coordinates):
        ra = _to_simbad_format(c.ra)
        dec = _to_simbad_format(c.dec)
        return 'FK5'       

def _to_simbad_format(coordinate):
    tup = coordinate.hms
    h, m, s = int(tup[0]), int(tup[1]), tup[2]
    return ":".join(h, m, s)

# could use the code in IrsaDust here.
# keep common utilities for parsing coordinates, angles, etc at top level?
def _parse_radius(radius):
    # do something smarter for choosing 'd', 'm' or 's'
    if isinstance(radius, basestring):
        value = coord.Angle(radius).degrees
        return str(value) + 'd'
    value = radius.to(u.degree).value
    return str(value) +'d'

def _validate_epoch(func):
    
    def wrapper(*args, **kwargs):
        if kwargs.get('epoch'):
            value = kwargs['epoch']
            p = re.compile('^[JB]\d+[.]?\d+$', re.IGNORECASE)
            assert p.match(value) is not None
        return func(*args, **kwargs)
    return wrapper

def _validate_equinox(func):
    
    def wrapper(*args, **kwargs):
        if kwargs.get('equinox'):
            value = kwargs['equinox']
            try:
                float(value)
        return func(*args, **kwargs)
    return wrapper



#--------------------------------------------------------upto here (core.py)-----------        

class _Query(object):
    def execute(self, votabledef=None, limit=None, pedantic=False, mirror=None):
        """ Execute the query, returning a :class:`SimbadResult` object.

        Parameters
        ----------
        votabledef: string or :class:`VoTableDef`, optional
            Definition object for the output.

        limit: int, optional
            Limits the number of rows returned. None sets the limit to 
            SIMBAD's server maximum.

        pedantic: bool, optional
            The value to pass to the votable parser for the *pedantic* 
            parameters.
        """

        return execute_query(self, votabledef=votabledef, limit=limit,
                pedantic=pedantic, mirror=mirror)


@ValidatedAttribute('wildcard', parameters._ScriptParameterWildcard)
class QueryId(_Query):
    """ Query by identifier.

    Parameters
    ----------
    identifier: string
        The identifier to query for.

    wildcard: bool, optional
        If True, specifies that `identifier` should be understood as an 
        expression with wildcards.

    """

    __command = 'query id '

    def __init__(self, identifier, wildcard=None):
        self.identifier = identifier
        self.wildcard = wildcard

    def __str__(self):
        return self.__command + (self.wildcard and 'wildcard ' or '') + \
                                                    str(self.identifier) + '\n'

    def __repr__(self):
        return '{%s(identifier=%s, wildcard=%s)}' % (self.__class__.__name__,
                            repr(self.identifier), repr(self.wildcard.value))


#class QueryBasic(_Query):
#    """ Basic Query
#
#    Parameters
#    ----------
#    anything : string
#        The identifier, coordinate, or bibcode to search for
#    """
#
#    __command = 'query basic '
#
#    def __init__(self, qstring):
#        self.Ident = qstring
#
#    def __str__(self):
#        return self.__command + str(self.Ident) + '\n'
#
#    def __repr__(self):
#        return '{%s(Ident=%s)}' % (self.__class__.__name__,
#                            repr(self.Ident))

@ValidatedAttribute('radius', parameters._ScriptParameterRadius)
class QueryAroundId(_Query):
    """ Query around identifier.

    Parameters
    ----------
    identifier: string
        The identifier around wich to query.

    radius: string, optional
        The value of the cone search radius. The value must be suffixed by
        'd' (degrees), 'm' (arcminutes) or 's' (arcseconds).
        If set to None the default value will be used.

    """

    __command = 'query around '

    def __init__(self, identifier, radius=None):
        self.identifier = identifier
        self.radius = radius

    def __str__(self):
        s = self.__command + str(self.identifier)
        if self.radius:
            s += ' radius=%s' % self.radius
        return s + '\n'

    def __repr__(self):
        return '{%s(identifier=%s, radius=%s)}' % (self.__class__.__name__,
                            repr(self.identifier), repr(self.radius.value))


class QueryCat(_Query):
    """ Query for a whole catalog.

    Parameters
    ----------

    catalog: string
        The catalog identifier, for example 'm', 'ngc'.

    """

    __command = 'query cat '

    def __init__(self, catalog):
        self.catalog = catalog

    def __str__(self):
        return self.__command + str(self.catalog) + '\n'

    def __repr__(self):
        return '{%s(catalog=%s)}' % (self.__class__.__name__,
                                                        repr(self.catalog))


@ValidatedAttribute('radius', parameters._ScriptParameterRadius)
@ValidatedAttribute('frame', parameters._ScriptParameterFrame)
@ValidatedAttribute('equinox', parameters._ScriptParameterEquinox)
@ValidatedAttribute('epoch', parameters._ScriptParameterEpoch)
class QueryCoord(_Query):
    """ Query by coordinates.

    Parameters
    ----------
    ra: string
        Right ascension, for example '+12 30'.

    dec: string
        Declination, for example '-20 17'.

    radius: string, optional
        The value of the cone search radius. The value must be suffixed by
        'd' (degrees), 'm' (arcminutes) or 's' (arcseconds).
        If set to None the default value will be used.

    frame: string, optional
        Frame of input coordinates.

    equinox: string optional
        Equinox of input coordinates.

    epoch:  string, optional
        Epoch of input coordinates.

    """

    __command = 'query coo '

    def __init__(self, ra, dec, radius=None, frame=None, equinox=None,
                                                                epoch=None):
        self.ra = ra
        self.dec = dec
        self.radius = radius
        self.frame = frame
        self.equinox = equinox
        self.epoch = epoch

    def __str__(self):
        s = self.__command + str(self.ra) + ' ' + str(self.dec)
        for item in ('radius', 'frame', 'equinox', 'epoch'):
            if getattr(self, item):
                s += ' %s=%s' % (item, str(getattr(self, item)))
        return s + '\n'

    def __repr__(self):
        return '{%s(ra=%s, dec=%s, radius=%s, frame=%s, equinox=%s, ' \
                    'epoch=%s)}' % \
                    (self.__class__.__name__, repr(self.ra), repr(self.dec),
                    repr(self.radius), repr(self.frame), repr(self.equinox),
                    repr(self.epoch))


class QueryBibobj(_Query):
    """ Query by bibcode objects. Used to fetch objects contained in the 
    given article.

    Parameters
    ----------
    bibcode: string
        The bibcode of the article.

    """

    __command = 'query bibobj '

    def __init__(self, bibcode):
        self.bibcode = bibcode

    def __str__(self):
        return self.__command + str(self.bibcode) + '\n'

    def __repr__(self):
        return '{%s(bibcode=%s)}' % (self.__class__.__name__,
                                                            repr(self.bibcode))


@ValidatedAttribute('radius', parameters._ScriptParameterRadius)
@ValidatedAttribute('frame', parameters._ScriptParameterFrame)
@ValidatedAttribute('epoch', parameters._ScriptParameterEpoch)
@ValidatedAttribute('equinox', parameters._ScriptParameterEquinox)
class QueryMulti(_Query):
    __command_ids = ('radius', 'frame', 'epoch', 'equinox')

    def __init__(self, queries=None, radius=None, frame=None, epoch=None,
                                                                equinox=None):
        """ A type of Query used to aggregate the values of multiple simple 
        queries into a single result.

        Parameters
        ----------
        queries: iterable of Query objects
            The list of Query objects to aggregate results for.

        radius: string, optional
            The value of the cone search radius. The value must be suffixed by
            'd' (degrees), 'm' (arcminutes) or 's' (arcseconds).
            If set to None the default value will be used.

        frame: string, optional
            Frame of input coordinates.

        equinox: string optional
            Equinox of input coordinates.

        epoch:  string, optional
            Epoch of input coordinates.

        .. note:: Each of the *radius*, *frame*, *equinox* et *epoch* arguments
                    acts as a default value for the whole MultiQuery object.
                    Individual queries may override these.
        """

        self.queries = []
        self.radius = radius
        self.frame = frame
        self.epoch = epoch
        self.equinox = equinox
        if queries is not None:
            if (isinstance(queries, _Query) and not isinstance(queries,
                    QueryMulti)):
                self.queries.append(queries)
            elif iter(queries):
                for query in queries:
                    if isinstance(query,_Query):
                        self.queries.append(query)
                    else:
                        raise ValueError("Queries must be simbad.Query instances")
                        #self.queries.append(BasicQuery(query))
            elif isinstance(queries, QueryMulti):
                for query in queries.queries:
                    self.queries.append(query)

    @property
    def __commands(self):
        """ The list of commands which are not None for this script.
        """
        return tuple([x for x in self.__command_ids if getattr(self, x)])

    @property
    def _header(self):
        s = ''
        for comm in self.__commands:
            s += 'set %s %s\n' % (comm, str(getattr(self, comm)))
        return s

    @property
    def __queries_string(self):
        s = ''
        for query in self.queries:
            s += str(query)
        return s

    def __str__(self):
        return self._header + self.__queries_string

    def __repr__(self):
        return repr(self.queries)


def execute_query(query, votabledef, limit, pedantic, mirror=None):
    limit2 = parameters._ScriptParameterRowLimit(limit)

    if votabledef is None:
        # votabledef is None, use the module level default one
        from . import votabledef as vodefault
        if isinstance(vodefault, VoTableDef):
            votabledef = vodefault
        else:
            votabledef = VoTableDef(vodefault)
    elif not isinstance(votabledef, VoTableDef):
        votabledef = VoTableDef(votabledef)

    # Create the 'script' string
    script = ''
    if limit is not None:
        script += 'set limit %s\n' % str(limit2)
    if isinstance(query, QueryMulti):
        script += query._header
    script += votabledef.def_str
    script += votabledef.open_str
    script += str(query)
    script += votabledef.close_str
    script = urllib.quote(script)
    
    from . import SIMBAD_SERVER 
    server = (SIMBAD_SERVER() if mirror is None else mirror)
    req_str = 'http://' + server + '/simbad/sim-script?script=' + script
    response = urllib2.urlopen(req_str)
    result = b''.join(response.readlines())
    result = result.decode('utf-8')
    if not result:
        raise TypeError
    return SimbadResult(result, pedantic=pedantic)

