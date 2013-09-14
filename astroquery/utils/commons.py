# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Common functions and classes that are required by all query classes.
"""

import re
import sys
import requests
import warnings

import astropy.units as u
from astropy import coordinates as coord
from astropy.utils import OrderedDict
import astropy.io.votable as votable

from ..exceptions import TimeoutError
from .. import version

PY3 = sys.version_info[0] >= 3

if PY3:
    basestring = (str, bytes)
__all__ = ['send_request',
           'parse_coordinates',
           'parse_radius',
           'TableList',
           'suppress_vo_warnings',
           'validate_email']


def send_request(url, data, timeout, request_type='POST', headers={},
                 **kwargs):
    """
    A utility function that post HTTP requests to remote server
    and returns the HTTP response.

    Parameters
    ----------
    url : str
        The URL of the remote server
    data : dict
        A dictionary representing the payload to be posted via the HTTP request
    timeout : int
        Time limit for establishing successful connection with remote server
    request_type : str
        options are 'POST' (default) and 'GET'. Determines whether to perform
        an HTTP POST or an HTTP GET request
    headers : dict
        POST or GET headers.  user-agent will be set to
        astropy:astroquery.version

    Returns
    -------
    response : `requests.Response`
        Response object returned by the remote server
    """
    headers['User-Agent'] = 'astropy:astroquery.{vers}'.format(vers=version.version)
    try:
        if request_type == 'GET':
            response = requests.get(url, params=data, timeout=timeout,
                                    headers=headers, **kwargs)
            return response
        elif request_type == 'POST':
            response = requests.post(url, data=data, timeout=timeout,
                                     headers=headers, **kwargs)
            return response
        else:
            raise ValueError("request_type must be either 'GET' or 'POST'.")
    except requests.exceptions.Timeout:
            raise TimeoutError("Query timed out, time elapsed {time}s".
                               format(time=timeout))
    except requests.exceptions.RequestException:
            raise Exception("Query failed\n")


def parse_radius(radius):
    """
    Given a radius checks that it is either parsable as an
    `astropy.coordinates.angle` or an `astropy.units.Quantity`
    and returns an `astropy.coordinates.Angle` object

    Parameters
    ----------
    radius : str/astropy.units.Quantity
        The radius of a region

    Returns
    -------
    `astropy.coordinates.Angle` object

    Raises
    ------
    astropy.units.UnitsException
    astropy.coordinates.errors.UnitsError
    AttributeError
    """
    try:
        return coord.Angle(radius)
    except coord.errors.UnitsError:
        # astropy <0.3 compatibility: Angle can't be instantiated with a unit object
        return coord.Angle(radius.to(u.degree), unit=u.degree)


def radius_to_unit(radius, unit='degree'):
    """
    Helper function: Parse a radius, then return its value in degrees

    Parameters
    ----------
    radius : str/astropy.units.Quantity
        The radius of a region

    Returns
    -------
    Floating point scalar value of radius in degrees
    """
    rad = parse_radius(radius)
    # This is a hack to deal with astropy pre/post PR#1006
    if hasattr(rad,str(unit)):
        return getattr(rad,str(unit))
    elif hasattr(rad,str(unit)+'s'):
        return getattr(rad,str(unit)+'s')
    # major hack to deal with <0.3 Angle's not having deg/arcmin/etc equivs.
    elif hasattr(rad,'degree'):
        return (rad.degree * u.degree).to(unit).value
    elif hasattr(rad,'to'):
        return rad.to(unit).value
    else:
        raise TypeError("Radius is an invalid type.")


def parse_coordinates(coordinates):
    """
    Takes a string or astropy.coordinates object. Checks if the
    string is parsable as an astropy.coordinates.ICRSCoordinates
    object or is a name that is resolvable. Otherwise asserts
    that the argument is an astropy.coordinates object.

    Parameters
    ----------
    coordinates : str/astropy.coordinates object
        Astronomical coordinate

    Returns
    -------
    a subclass of `astropy.coordinates.SphericalCoordinatesBase`

    Raises
    ------
    astropy.units.UnitsException
    TypeError
    """
    if isinstance(coordinates, basestring):
        try:
            c = coord.ICRSCoordinates.from_name(coordinates)
        except coord.name_resolve.NameResolveError:
            try:
                c = coord.ICRSCoordinates(coordinates)
                warnings.warn("Coordinate string is being interpreted as an ICRS coordinate.")
            except u.UnitsException:
                warnings.warn("Only ICRS coordinates can be entered as strings\n"
                              "For other systems please use the appropriate "
                              "astropy.coordinates object")
                raise u.UnitsException
    elif isinstance(coordinates, coord.SphericalCoordinatesBase):
        c = coordinates
    else:
        raise TypeError("Argument cannot be parsed as a coordinate")
    return c


class TableList(list):

    """
    A class that inherits from `list` but included some pretty printing methods
    for an OrderedDict of `astropy.table.Table` objects.

    HINT: To access the tables by # instead of by table ID:
    >>> t = TableList([('a',1),('b',2)])
    >>> t[1]
    2
    >>> t['b']
    2
    """
    def __init__(self, inp):
        if not isinstance(inp, OrderedDict):
            try:
                inp = OrderedDict(inp)
            except TypeError,ValueError:
                raise ValueError("Input to TableList must be an OrderedDict or list of (k,v) pairs")
        
        self._dict = inp
        super(TableList,self).__init__(inp.values())

    def __getitem__(self, key):
        if isinstance(key, int):
            # get the value in the (key,value) pair
            return super(TableList,self).__getitem__(key)
        elif key in self._dict:
            return self._dict[key]
        else:
            raise TypeError("TableLists can only be indexed with the named keys and integers.")

    def __setitem__(self, value):
        raise TypeError("TableList is immutable.")

    def __getslice__(self, slice):
        return self.values()[slice]

    def keys(self):
        return self._dict.keys()

    def values(self):
        return self._dict.values()

    def __repr__(self):
        """
        Overrides the `OrderedDict.__repr__` method to return a simple summary
        of the `TableList` object.
        """

        return self.format_table_list()

        # This information is often unhelpful
        # total_rows = sum(len(self.__getitem__(t)) for t in self.keys())
        # info_str = "<TableList with {keylen} table(s) and {total_rows} total row(s)>".format(keylen=len(list(self.keys())),
        #                                                                                    total_rows=total_rows)

        # return info_str

    def format_table_list(self):
        """
        Prints the names of all `astropy.table.Table` objects, with their
        respective number of row and columns, contained in the
        `TableList` instance.
        """
        ntables = len(list(self.keys()))
        if ntables == 0:
            return "Empty TableList"

        header_str = "TableList with {keylen} tables:".format(keylen=ntables)
        body_str = "\n".join(["\t'{t_number}:{t_name}' with {ncol} column(s) and {nrow} row(s) ".
                              format(t_number=t_number,
                                     t_name=t_name,
                                     nrow=len(self[t_number]),
                                     ncol=len(self[t_number].colnames))
                              for t_number,t_name in enumerate(self.keys())])
        return "\n".join([header_str, body_str])

    def print_table_list(self):
        print(self.format_table_list())

    def pprint(self, **kwargs):
        """ Helper function to make API more similar to astropy.Tables """
        if kwargs != {}:
            warnings.warn("TableList is a container of astropy.Tables.")
        self.print_table_list()



def suppress_vo_warnings():
    """ Suppresses all warnings of the class `astropy.io.votable.exceptions.VOWarning."""
    warnings.filterwarnings("ignore", category=votable.exceptions.VOWarning)


def validate_email(email):
    """
    E-mail address validation.  Uses validate_email if available, else a simple
    regex that will let through some invalid e-mails but will catch the most
    common violators.
    """
    try:
        import validate_email
        return validate_email.validate_email(email)
    except ImportError:
        return bool(re.compile('^\S+@\S+\.\S+$').match(email))
