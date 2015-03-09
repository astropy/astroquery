# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Common functions and classes that are required by all query classes.
"""

import re
import warnings
import os
import shutil
import socket

import requests

from astropy.extern.six.moves.urllib_error import URLError
from astropy.extern import six
import astropy.units as u
from astropy import coordinates as coord
from astropy.utils import OrderedDict
import astropy.utils.data as aud
from astropy.io import fits, votable

try:
    from astropy.coordinates import BaseCoordinateFrame
    ICRSCoordGenerator = lambda *args, **kwargs: coord.SkyCoord(*args, frame='icrs', **kwargs)
    GalacticCoordGenerator = lambda *args, **kwargs: coord.SkyCoord(*args, frame='galactic', **kwargs)
    FK5CoordGenerator = lambda *args, **kwargs: coord.SkyCoord(*args, frame='fk5', **kwargs)
    FK4CoordGenerator = lambda *args, **kwargs: coord.SkyCoord(*args, frame='fk4', **kwargs)
    ICRSCoord = coord.SkyCoord
    CoordClasses = (coord.SkyCoord, BaseCoordinateFrame)
except ImportError:
    from astropy.coordinates import SphericalCoordinatesBase as BaseCoordinateFrame
    ICRSCoordGenerator = lambda *args, **kwargs: coord.ICRS(*args, **kwargs)
    GalacticCoordGenerator = lambda *args, **kwargs: coord.Galactic(*args, **kwargs)
    FK5CoordGenerator = lambda *args, **kwargs: coord.FK5(*args, **kwargs)
    FK4CoordGenerator = lambda *args, **kwargs: coord.FK4(*args, **kwargs)
    ICRSCoord = coord.ICRS
    CoordClasses = (coord.SphericalCoordinatesBase,)

from ..exceptions import TimeoutError
from .. import version


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
    timeout : int, quantity_like
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

    if hasattr(timeout, "unit"):
        warnings.warn("Converting timeout to seconds and truncating to integer.")
        timeout = int(timeout.to(u.s).value)

    try:
        if request_type == 'GET':
            response = requests.get(url, params=data, timeout=timeout,
                                    headers=headers, **kwargs)
        elif request_type == 'POST':
            response = requests.post(url, data=data, timeout=timeout,
                                     headers=headers, **kwargs)
        else:
            raise ValueError("request_type must be either 'GET' or 'POST'.")

        response.raise_for_status()

        return response

    except requests.exceptions.Timeout:
            raise TimeoutError("Query timed out, time elapsed {time}s".
                               format(time=timeout))
    except requests.exceptions.RequestException:
            raise Exception("Query failed\n")


def parse_radius(radius):
    """
    Given a radius checks that it is either parsable as an
    `~astropy.coordinates.Angle` or a `~astropy.units.Quantity`
    and returns an `~astropy.coordinates.Angle` object.

    Parameters
    ----------
    radius : str/`~astropy.units.Quantity`
        The radius of a region

    Returns
    -------
    angle : `~astropy.coordinates.Angle`

    Raises
    ------
    astropy.units.UnitsError
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

    if isinstance(unit, six.string_types):
        if hasattr(rad, unit):
            return getattr(rad, unit)
        elif hasattr(rad, unit + 's'):
            return getattr(rad, unit + 's')

    # major hack to deal with <0.3 Angle's not having deg/arcmin/etc equivs.
    if hasattr(rad, 'degree'):
        return (rad.degree * u.degree).to(unit).value
    elif hasattr(rad, 'to'):
        return rad.to(unit).value
    else:
        raise TypeError("Radius is an invalid type.")


def parse_coordinates(coordinates):
    """
    Takes a string or astropy.coordinates object. Checks if the
    string is parsable as an `astropy.coordinates`
    object or is a name that is resolvable. Otherwise asserts
    that the argument is an astropy.coordinates object.

    Parameters
    ----------
    coordinates : str/astropy.coordinates object
        Astronomical coordinate

    Returns
    -------
    a subclass of `astropy.coordinates.BaseCoordinateFrame`

    Raises
    ------
    astropy.units.UnitsError
    TypeError
    """
    if isinstance(coordinates, six.string_types):
        try:
            c = ICRSCoord.from_name(coordinates)
        except coord.name_resolve.NameResolveError:
            try:
                c = ICRSCoordGenerator(coordinates)
                warnings.warn("Coordinate string is being interpreted as an ICRS coordinate.")
            except u.UnitsError:
                warnings.warn("Only ICRS coordinates can be entered as strings\n"
                              "For other systems please use the appropriate "
                              "astropy.coordinates object")
                raise u.UnitsError
    elif isinstance(coordinates, CoordClasses):
        if hasattr(coordinates, 'frame'):
            c = coordinates
        else:
            # Convert the "frame" object into a SkyCoord
            c = coord.SkyCoord(coordinates)
    else:
        raise TypeError("Argument cannot be parsed as a coordinate")
    return c


def coord_to_radec(coordinate):
    """
    Wrapper to turn any astropy coordinate into FK5 RA in Hours and FK5 Dec in
    degrees

    This is a hack / temporary wrapper to deal with the unstable astropy API
    (it may be wise to remove this hack since it's not clear that the old
    coordinate API can even do transforms)
    """
    C = coordinate.transform_to('fk5')
    if hasattr(C.ra, 'hour'):
        ra = C.ra.hour
    elif hasattr(C.ra, 'hourangle'):
        ra = C.ra.hourangle
    else:
        raise Exception("API Error: RA cannot be converted to hour or hourangle.")
    dec = C.dec.degree
    return ra, dec


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
            # py3 doesn't let you catch 2 types of errors.
            errmsg = "Input to TableList must be an OrderedDict or list of (k,v) pairs"
            try:
                inp = OrderedDict(inp)
            except (TypeError, ValueError):
                raise ValueError("Input to TableList must be an OrderedDict or list of (k,v) pairs")

        self._dict = inp
        super(TableList, self).__init__(inp.values())

    def __getitem__(self, key):
        if isinstance(key, int):
            # get the value in the (key,value) pair
            return super(TableList, self).__getitem__(key)
        elif key in self._dict:
            return self._dict[key]
        else:
            raise TypeError("TableLists can only be indexed with the named keys and integers.")

    def __setitem__(self, value):
        raise TypeError("TableList is immutable.")

    def __getslice__(self, slice):
        return list(self.values())[slice]

    def keys(self):
        return list(self._dict.keys())

    def values(self):
        return list(self._dict.values())

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
                              for t_number, t_name in enumerate(self.keys())])
        return "\n".join([header_str, body_str])

    def print_table_list(self):
        print(self.format_table_list())

    def pprint(self, **kwargs):
        """ Helper function to make API more similar to astropy.Tables """
        if kwargs != {}:
            warnings.warn("TableList is a container of astropy.Tables.")
        self.print_table_list()


def _is_coordinate(coordinates):
    """
    Returns `True` if coordinates can be parsed via `astropy.coordinates`
    and `False` otherwise.

    Parameters
    ----------
    coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the appropriate
            `astropy.coordinates` object. ICRS coordinates may also be entered as strings
            as specified in the `astropy.coordinates` module.

    Returns
    -------
    bool
    """
    if hasattr(coordinates, 'fk5'):
        # its coordinate-like enough
        return True
    try:
        ICRSCoordGenerator(coordinates)
        return True
    except ValueError:
        return False


def suppress_vo_warnings():
    """Suppresses all warnings of the class `astropy.io.votable.exceptions.VOWarning`."""
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


class FileContainer(object):
    """
    A File Object container, meant to offer lazy access to downloaded FITS
    files.
    """

    def __init__(self, target, **kwargs):
        kwargs.setdefault('cache', True)
        self._target = target
        self._timeout = kwargs.get('remote_timeout', aud.REMOTE_TIMEOUT())
        if (os.path.splitext(target)[1] == '.fits' and not
                ('encoding' in kwargs and kwargs['encoding'] == 'binary')):
            warnings.warn("FITS files must be read as binaries; error is likely.")
        self._readable_object = get_readable_fileobj(target, **kwargs)

    def get_fits(self):
        """
        Assuming the contained file is a FITS file, read it
        and return the file parsed as FITS HDUList
        """
        filedata = self.get_string()

        self._fits = fits.HDUList.fromstring(filedata)

        return self._fits

    def save_fits(self, savepath, link_cache='hard'):
        """
        Save a FITS file to savepath

        Parameters
        ----------
        savepath : str
            The full path to a FITS filename, e.g. "file.fits", or
            "/path/to/file.fits".
        link_cache : 'hard', 'sym', or False
            Try to create a hard or symbolic link to the astropy cached file?
            If the system is unable to create a hardlink, the file will be
            copied to the target location.
        """
        from warnings import warn

        self.get_fits()

        try:
            dldir, urlmapfn = aud._get_download_cache_locs()
        except (IOError, OSError) as e:
            msg = 'Remote data cache could not be accessed due to '
            estr = '' if len(e.args) < 1 else (': ' + str(e))
            warn(aud.CacheMissingWarning(msg + e.__class__.__name__ + estr))

        with aud._open_shelve(urlmapfn, True) as url2hash:
            if str(self._target) in url2hash:
                target = url2hash[str(self._target)]
            else:
                raise IOError("Cached file not found / does not exist.")

        if link_cache == 'hard':
            try:
                os.link(target, savepath)
            except (IOError, OSError) as e:
                shutil.copy(target, savepath)
        elif link_cache == 'sym':
            os.symlink(target, savepath)
        else:
            shutil.copy(target, savepath)

    def get_string(self):
        """
        Download the file as a string
        """
        if not hasattr(self, '_string'):
            try:
                with self._readable_object as f:
                    data = f.read()
                    self._string = data
            except URLError as e:
                if isinstance(e.reason, socket.timeout):
                    raise TimeoutError("Query timed out, time elapsed {t}s".
                                       format(t=self._timeout))
                else:
                    raise e

        return self._string

    def get_stringio(self):
        """
        Return the file as an io.StringIO object
        """
        s = self.get_string()
        # TODO: replace with six.BytesIO
        try:
            return six.BytesIO(s)
        except TypeError:
            return six.StringIO(s)

    def __repr__(self):
        if hasattr(self, '_fits'):
            return "Downloaded FITS file: " + self._fits.__repr__()
        else:
            return "Downloaded object from URL {} with ID {}".format(self._target, id(self._readable_object))


def get_readable_fileobj(*args, **kwargs):
    """
    Overload astropy's get_readable_fileobj so that we can safely monkeypatch
    it in astroquery without affecting astropy core functionality
    """
    return aud.get_readable_fileobj(*args, **kwargs)
