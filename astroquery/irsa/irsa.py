from __future__ import print_function, division

import warnings
import urllib
import urllib2
import tempfile
import string
from xml.etree.ElementTree import ElementTree

from astropy.table import Table
try:
    import astropy.io.vo.table as votable
except ImportError:
    import astropy.io.votable as votable

'''

API from

 http://irsa.ipac.caltech.edu/applications/Gator/GatorAid/irsa/catsearch.html

The URL of the IRSA catalog query service, CatQuery, is

 http://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query

The service accepts the following keywords, which are analogous to the search
fields on the Gator search form:


spatial     Required    Type of spatial query: Cone, Box, Polygon, and NONE

polygon                 Convex polygon of ra dec pairs, separated by comma(,)
                        Required if spatial=polygon

radius                  Cone search radius
                        Optional if spatial=Cone, otherwise ignore it
                        (default 10 arcsec)

radunits                Units of a Cone search: arcsec, arcmin, deg.
                        Optional if spatial=Cone
                        (default='arcsec')

size                    Width of a box in arcsec
                        Required if spatial=Box.

objstr                  Target name or coordinate of the center of a spatial
                        search center. Target names must be resolved by
                        SIMBAD or NED.

                        Required only when spatial=Cone or spatial=Box.

                        Examples: 'M31'
                                  '00 42 44.3 -41 16 08'
                                  '00h42m44.3s -41d16m08s'

catalog     Required    Catalog name in the IRSA database management system.

outfmt      Optional    Defines query's output format.
                        6 - returns a program interface in XML
                        3 - returns a VO Table (XML)
                        2 - returns SVC message
                        1 - returns an ASCII table
                        0 - returns Gator Status Page in HTML (default)

desc        Optional    Short description of a specific catalog, which will
                        appear in the result page.

order       Optional    Results ordered by this column.

constraint  Optional    User defined query constraint(s)
                        Note: The constraint should follow SQL syntax.

onlist      Optional    1 - catalog is visible through Gator web interface
                        (default)

                        0 - catalog has been ingested into IRSA but not yet
                        visible through web interface.

                        This parameter will generally only be set to 0 when
                        users are supporting testing and evaluation of new
                        catalogs at IRSA's request.

If onlist=0, the following parameters are required:

    server              Symbolic DataBase Management Server (DBMS) name

    database            Name of Database.

    ddfile              The data dictionary file is used to get column
                        information for a specific catalog.

    selcols             Target column list with value separated by a comma(,)

                        The input list always overwrites default selections
                        defined by a data dictionary.

    outrows             Number of rows retrieved from database.

                        The retrieved row number outrows is always less than or
                        equal to available to be retrieved rows under the same
                        constraints.
'''

__all__ = ['query_gator_cone', 'query_gator_box', 'query_gator_polygon',
           'query_gator_all_sky', 'print_gator_catalogs',
           'list_gator_catalogs']

GATOR_URL = 'http://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query'
GATOR_LIST_URL = 'http://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-scan?mode=xml'


default_options={
        'outfmt':3
        }# use VO table format

def query_gator_cone(catalog, object, radius, units='arcsec'):
    '''
    IRSA Gator cone search query.

    This function can be used to perform a cone search in the catalogs hosted
    by the NASA/IPAC Infrared Science Archive (IRSA).

    Parameters
    ----------
    catalog : str
        The catalog to be used (see the *Notes* section below).
    object : str
        This string gives the position of the center of the cone or box if
        performing a cone or box search. The string can give coordinates
        in various coordinate systems, or the name of a source that will
        be resolved on the server (see `here
        <http://irsa.ipac.caltech.edu/search_help.html>`_ for more
        details).
    radius : float
        The radius for the cone search.
    units : {'arcsec', 'arcmin', 'deg'}, optional
        The units for the cone search radius. Defaults to 'arcsec'.

    Returns
    -------
    table : `~astropy.table.Table`
        A table containing the results of the query

    Notes
    -----
    The ``catalog`` value to be used can be found with::

        >>> from astroquery.irsa import list_gator_catalogs
        >>> catalogs = list_gator_catalogs()

    which returns a dictionary of available catalogs. Alternatively, one can
    also use::

        >>> from astroquery.irsa import print_gator_catalogs
        >>> print_gator_catalogs()

    to simply print these rather than return a dictionary.
     '''

    # Set basic options
    options = {}
    options['spatial'] = 'Cone'
    options['catalog'] = catalog
    options['outfmt'] = 3  # use VO table format

    options['objstr'] = object

    options['radius'] = radius

    if units not in ['arcsec', 'arcmin', 'deg']:
        raise ValueError("units should be one of arcsec/arcmin/deg")
    options['radunits'] = units

    return _query_gator(options)


def query_gator_box(catalog, object, size):
    '''
    IRSA Gator box search query.

    This function can be used to perform a box search in the catalogs hosted
    by the NASA/IPAC Infrared Science Archive (IRSA).

    Parameters
    ----------
    catalog : str
        The catalog to be used (see the *Notes* section below).
    object : str
        This string gives the position of the center of the cone or box if
        performing a cone or box search. The string can give coordinates
        in various coordinate systems, or the name of a source that will
        be resolved on the server (see `here
        <http://irsa.ipac.caltech.edu/search_help.html>`_ for more
        details). Required if spatial is 'Cone' or 'Box'.
    size : float
        The size of the box to search in arcseconds.

    Returns
    -------
    table : `~astropy.table.Table`
        A table containing the results of the query

    Notes
    -----
    The ``catalog`` value to be used can be found with::

        >>> from astroquery.irsa import list_gator_catalogs
        >>> catalogs = list_gator_catalogs()

    which returns a dictionary of available catalogs. Alternatively, one can
    also use::

        >>> from astroquery.irsa import print_gator_catalogs
        >>> print_gator_catalogs()

    to simply print these rather than return a dictionary.
    '''

    # Set basic options
    options = {}
    options['spatial'] = 'Box'
    options['catalog'] = catalog
    options['outfmt'] = 3  # use VO table format

    options['objstr'] = object

    options['size'] = size

    return _query_gator(options)


def query_gator_polygon(catalog, polygon):
    '''
    IRSA Gator polygon search query.

    This function can be used to perform a polygon search in the catalogs hosted
    by the NASA/IPAC Infrared Science Archive (IRSA).

    Parameters
    ----------
    catalog : str
        The catalog to used (see the *Notes* section below).
    polygon : list
        A list of ``(ra, dec)`` pairs (as tuples), in decimal degrees,
        outlinining the polygon to search in.

    Returns
    -------
    table : `~astropy.table.Table`
        A table containing the results of the query

    Notes
    -----
    The ``catalog`` value to be used can be found with::

        >>> from astroquery.irsa import list_gator_catalogs
        >>> catalogs = list_gator_catalogs()

    which returns a dictionary of available catalogs. Alternatively, one can
    also use::

        >>> from astroquery.irsa import print_gator_catalogs
        >>> print_gator_catalogs()

    to simply print these rather than return a dictionary.
     '''

    # Set basic options
    options = {}
    options['spatial'] = 'Polygon'
    options['catalog'] = catalog
    options['outfmt'] = 3  # use VO table format

    pairs = []
    for pair in polygon:
        if pair[1] > 0:
            pairs.append(str(pair[0]) + '+' + str(pair[1]))
        else:
            pairs.append(str(pair[0]) + str(pair[1]))
    options['polygon'] = string.join(pairs, ',')

    return _query_gator(options)


def query_gator_all_sky(catalog):
    '''
    IRSA Gator all-sky search query.

    This function can be used to perform an all-sky search in the catalogs hosted
    by the NASA/IPAC Infrared Science Archive (IRSA).

    Parameters
    ----------
    catalog : str
        The catalog to used (see the *Notes* section below).

    Returns
    -------
    table : `~astropy.table.Table`
        A table containing the results of the query

    Notes
    -----
    The ``catalog`` value to be used can be found with::

        >>> from astroquery.irsa import list_gator_catalogs
        >>> catalogs = list_gator_catalogs()

    which returns a dictionary of available catalogs. Alternatively, one can
    also use::

        >>> from astroquery.irsa import print_gator_catalogs
        >>> print_gator_catalogs()

    to simply print these rather than return a dictionary.
     '''

    # Set basic options
    options = {}
    options['spatial'] = 'NONE'
    options['catalog'] = catalog
    options['outfmt'] = 3  # use VO table format

    return _query_gator(options)


def _query_gator(options, debug=False):

    # Construct query URL
    url = GATOR_URL + "?" + \
          string.join(["%s=%s" % (x, urllib.quote_plus(str(options[x]))) for x in options], "&")
    if debug:
        print(url)

    # Request page
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    result = response.read()

    # Check if results were returned
    if 'The catalog is not on the list' in result:
        raise Exception("Catalog not found")

    # Check that object name was not malformed
    if 'Either wrong or missing coordinate/object name' in result:
        raise Exception("Malformed coordinate/object name")

    # Check that the results are not of length zero
    if len(result) == 0:
        raise Exception("The IRSA server sent back an empty reply")

    # Write table to temporary file
    output = tempfile.NamedTemporaryFile()
    output.write(result)
    output.flush()

    # Read it in using the astropy VO table reader
    try:
        firsttable = votable.parse(output.name, pedantic=False).get_first_table()
        array = firsttable.array
    except Exception as ex:
        print("Failed to parse votable!  Returning output file instead.")
        print(ex)
        return open(output.name,'r')

    # Convert to astropy.table.Table instance
    table = array.to_table()

    # Check if table is empty
    if len(table) == 0:
        warnings.warn("Query returned no results, so the table will be empty")

    # Remove temporary file
    output.close()

    return table


def print_gator_catalogs():
    '''
    Display a table of the catalogs in the IRSA Gator tool.
    '''
    catalogs = list_gator_catalogs()
    for catname in catalogs:
        print("%30s  %s" % (catname, catalogs[catname]))


def list_gator_catalogs():
    '''
    Return a dictionary of the catalogs in the IRSA Gator tool.

    Returns
    -------
    catalogs : dict
        A dictionary of catalogs where the key indicates the catalog name to
        be used in query functions, and the value is the verbose description
        of the catalog.
    '''

    req = urllib2.Request(GATOR_LIST_URL)
    response = urllib2.urlopen(req)

    tree = ElementTree()

    catalogs = {}
    for catalog in tree.parse(response).findall('catalog'):
        catname = catalog.find('catname').text
        desc = catalog.find('desc').text
        catalogs[catname] = desc

    return catalogs
