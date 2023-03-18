# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Common functions and classes that are required by all query classes.
"""

import re
import warnings
import os
import shutil
import socket
from io import BytesIO, StringIO
from urllib.error import URLError

import astropy.units as u
from collections import OrderedDict
from astropy.utils import minversion
import astropy.utils.data as aud
from astropy.io import fits, votable

from astropy.coordinates import BaseCoordinateFrame, SkyCoord

from ..exceptions import TimeoutError, InputWarning


CoordClasses = (SkyCoord, BaseCoordinateFrame)


__all__ = ['parse_coordinates',
           'TableList',
           'suppress_vo_warnings',
           'validate_email',
           'ASTROPY_LT_4_3',
           'ASTROPY_LT_5_0',
           'ASTROPY_LT_5_1']

ASTROPY_LT_4_3 = not minversion('astropy', '4.3')
ASTROPY_LT_5_0 = not minversion('astropy', '5.0')

ASTROPY_LT_5_1 = not minversion('astropy', '5.1')


def parse_coordinates(coordinates):
    """
    Takes a string or astropy.coordinates object. Checks if the
    string is parsable as an `astropy.coordinates`
    object or is a name that is resolvable. Otherwise asserts
    that the argument is an astropy.coordinates object.

    Parameters
    ----------
    coordinates : str or `astropy.coordinates` object
        Astronomical coordinate

    Returns
    -------
    coordinates : a subclass of `astropy.coordinates.BaseCoordinateFrame`


    Raises
    ------
    astropy.units.UnitsError
    TypeError
    """
    if isinstance(coordinates, str):
        try:
            c = SkyCoord(coordinates, frame="icrs")
            warnings.warn("Coordinate string is being interpreted as an "
                          "ICRS coordinate.", InputWarning)

        except u.UnitsError:
            warnings.warn("Only ICRS coordinates can be entered as "
                          "strings.\n For other systems please use the "
                          "appropriate astropy.coordinates object.", InputWarning)
            raise u.UnitsError
        except ValueError as err:
            if ((ASTROPY_LT_5_0 and isinstance(err.args[1], u.UnitsError))
                    or (not ASTROPY_LT_5_0 and isinstance(err.__context__, u.UnitsError))):
                try:
                    c = SkyCoord(coordinates, unit="deg", frame="icrs")
                    warnings.warn("Coordinate string is being interpreted as an "
                                  "ICRS coordinate provided in degrees.", InputWarning)

                except ValueError:
                    c = SkyCoord.from_name(coordinates, frame="icrs")
            else:
                c = SkyCoord.from_name(coordinates, frame="icrs")

    elif isinstance(coordinates, CoordClasses):
        if hasattr(coordinates, 'frame'):
            c = coordinates
        else:
            # Convert the "frame" object into a SkyCoord
            c = SkyCoord(coordinates)
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
        raise ValueError("API Error: RA cannot be converted to hour "
                         "or hourangle.")
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
            try:
                inp = OrderedDict(inp)
            except (TypeError, ValueError):
                raise ValueError("Input to TableList must be an OrderedDict "
                                 "or list of (k,v) pairs")

        self._dict = inp
        super().__init__(inp.values())

    def __getitem__(self, key):
        if isinstance(key, int):
            # get the value in the (key,value) pair
            return super().__getitem__(key)
        elif key in self._dict:
            return self._dict[key]
        else:
            raise TypeError("TableLists can only be indexed with the "
                            "named keys and integers.")

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
        body_str = "\n".join(["\t'{t_number}:{t_name}' with {ncol} column(s) "
                              "and {nrow} row(s) "
                              .format(t_number=t_number, t_name=t_name,
                                      nrow=len(self[t_number]),
                                      ncol=len(self[t_number].colnames))
                              for t_number, t_name in enumerate(self.keys())])
        return "\n".join([header_str, body_str])

    def print_table_list(self):
        print(self.format_table_list())

    def pprint(self, **kwargs):
        """ Helper function to make API more similar to astropy.Tables """
        if kwargs != {}:
            warnings.warn("TableList is a container of astropy.Tables.", InputWarning)
        self.print_table_list()


def _is_coordinate(coordinates):
    """
    Returns `True` if coordinates can be parsed via `astropy.coordinates`
    and `False` otherwise.

    Parameters
    ----------
    coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `astropy.coordinates` module.

    Returns
    -------
    bool
    """
    if hasattr(coordinates, 'fk5'):
        # its coordinate-like enough
        return True
    try:
        SkyCoord(coordinates, frame="icrs")
        return True
    except ValueError:
        return False


def suppress_vo_warnings():
    """
    Suppresses all warnings of the class
    `astropy.io.votable.exceptions.VOWarning`.
    """
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
        return bool(re.compile(r'^\S+@\S+\.\S+$').match(email))


class FileContainer:
    """
    A File Object container, meant to offer lazy access to downloaded FITS
    files.
    """

    def __init__(self, target, **kwargs):
        kwargs.setdefault('cache', True)
        self._target = target
        self._timeout = kwargs.get('remote_timeout', aud.conf.remote_timeout)
        if (os.path.splitext(target)[1] == '.fits' and not
                ('encoding' in kwargs and kwargs['encoding'] == 'binary')):
            warnings.warn("FITS files must be read as binaries; error is "
                          "likely.", InputWarning)
        self._readable_object = get_readable_fileobj(target, **kwargs)

    def get_fits(self):
        """
        Assuming the contained file is a FITS file, read it
        and return the file parsed as FITS HDUList
        """
        filedata = self.get_string()

        if len(filedata) == 0:
            raise TypeError("The file retrieved was empty.")

        self._fits = fits.HDUList.fromstring(filedata)

        return self._fits

    def save_fits(self, savepath, *, link_cache='hard'):
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
        self.get_fits()
        target_key = str(self._target)

        target = aud.download_file(target_key, cache=True, sources=[])

        if link_cache == 'hard':
            try:
                os.link(target, savepath)
            except (OSError, AttributeError):
                shutil.copy(target, savepath)
        elif link_cache == 'sym':
            try:
                os.symlink(target, savepath)
            except AttributeError:
                raise OSError('Creating symlinks is not possible on this OS.')
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
        try:
            return BytesIO(s)
        except TypeError:
            return StringIO(s)

    def __repr__(self):
        if hasattr(self, '_fits'):
            return f"Downloaded FITS file: {self._fits!r}"
        else:
            return f"Downloaded object from URL {self._target} with ID {id(self._readable_object)}"


def get_readable_fileobj(*args, **kwargs):
    """
    Overload astropy's get_readable_fileobj so that we can safely monkeypatch
    it in astroquery without affecting astropy core functionality
    """
    return aud.get_readable_fileobj(*args, **kwargs)


def parse_votable(content):
    """
    Parse a votable in string format
    """
    tables = votable.parse(BytesIO(content), verify='warn')
    return tables
