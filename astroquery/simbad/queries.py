# Licensed under a 3-clause BSD style license - see LICENSE.rst

import urllib
import urllib2
from .parameters import ValidatedAttribute
from . import parameters
from .result import SimbadResult
from .simbad_votable import VoTableDef

__all__ = ['QueryId',
            'QueryAroundId',
            'QueryCat',
            'QueryCoord',
            'QueryBibobj',
            'QueryMulti',
            ]


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

