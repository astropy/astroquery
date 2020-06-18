# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import copy
import io
import re
import warnings

import astropy.coordinates as coord
import astropy.units as u
import astropy.units.cds as cds
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import ascii
from astropy.io.votable import parse_single_table
from astropy.table import QTable
from astropy.utils import deprecated, deprecated_renamed_argument
from astropy.utils.exceptions import AstropyWarning

from ..exceptions import (InputWarning, InvalidQueryError, NoResultsWarning,
                          RemoteServiceError)
from ..query import BaseQuery
from ..utils import async_to_sync, commons
from ..utils.class_or_instance import class_or_instance
from . import conf

__all__ = ["NasaExoplanetArchive", "NasaExoplanetArchiveClass"]


UNIT_MAPPER = {
    "--": None,
    "BJD": None,  # TODO: optionally supprot mapping columns to Time objects
    "BKJD": None,  # TODO: optionally supprot mapping columns to Time objects
    "D_L": u.pc,
    "D_S": u.pc,
    "Earth flux": None,  # TODO: Include Earth insolation units
    "Fearth": None,  # TODO: Include Earth insolation units
    "M_E": u.M_earth,
    "M_J": u.M_jupiter,
    "R_Earth": u.R_earth,
    "R_Sun": u.R_sun,
    "Rstar": u.R_sun,
    "a_perp": u.au,
    "arc-sec/year": u.arcsec / u.yr,
    "cm/s**2": u.dex(u.dm / u.s ** 2),
    "days": u.day,
    "degrees": u.deg,
    "dexincgs": u.dex(u.cm / u.s ** 2),
    "hours": u.hr,
    "hrs": u.hr,
    "kelvin": u.K,
    "logLsun": u.dex(u.L_sun),
    "mags": u.mag,
    "microas": u.uas,
    "perc": u.percent,
    "pi_E": None,
    "pi_EE": None,
    "pi_EN": None,
    "pi_rel": None,
    "ppm": cds.ppm,
    "seconds": u.s,
    "solarradius": u.R_sun,
}
CONVERTERS = dict(koi_quarters=[ascii.convert_numpy(np.str)])
OBJECT_TABLES = {"exoplanets": "pl_", "compositepars": "fpl_", "exomultpars": "mpl_"}


class InvalidTableError(InvalidQueryError):
    """Exception thrown if the given table is not recognized by the Exoplanet Archive Servers"""

    pass


@async_to_sync
class NasaExoplanetArchiveClass(BaseQuery):
    """
    The interface for querying the NASA Exoplanet Archive API

    A full discussion of the available tables and query syntax is available on `the documentation
    page <https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html>`_.
    """

    URL = conf.url
    TIMEOUT = conf.timeout
    CACHE = conf.cache

    @class_or_instance
    def query_criteria_async(self, table, get_query_payload=False, cache=None, **criteria):
        """
        Search a table given a set of criteria or return the full table

        The syntax for these queries is described on the Exoplanet Archive API documentation page
        [1]_. In particular, the most commonly used criteria will be ``select`` and ``where``.

        Parameters
        ----------
        table : str
            The name of the table to query. A list of the tables on the Exoplanet Archive can be
            found on the documentation page [1]_.
        get_query_payload : bool, optional
            Just return the dict of HTTP request parameters. Defaults to ``False``.
        cache : bool, optional
            Should the request result be cached? This can be useful for large repeated queries,
            but since the data in the archive is updated regularly, this defaults to ``False``.
        **criteria
            The filtering criteria to apply. These are described in detail in the archive
            documentation [1]_, but some examples include ``select="*"`` to return all columns of
            the queried table or ``where=pl_name='K2-18 b'`` to filter a specific column.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.

        References
        ----------

        .. [1] `NASA Exoplanet Archive API Documentation
           <https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html>`_
        """
        table = table.lower()

        # Deal with lists of columns instead of comma separated strings
        criteria = copy.copy(criteria)
        if "select" in criteria:
            select = criteria["select"]
            if not isinstance(select, str):
                select = ",".join(select)
            criteria["select"] = select

        # We prefer to work with IPAC format so that we get units, but everything it should work
        # with the other options too
        criteria["format"] = criteria.get("format", "ipac")
        if "json" in criteria["format"].lower():
            raise InvalidQueryError("The 'json' format is not supported")

        # Build the query
        request_payload = dict(table=table, **criteria)
        if get_query_payload:
            return request_payload

        # Use the default cache setting if one was not provided
        if cache is None:
            cache = self.CACHE

        # Execute the request
        response = self._request(
            "GET", self.URL, params=request_payload, timeout=self.TIMEOUT, cache=cache,
        )
        response.requested_format = criteria["format"]

        return response

    @class_or_instance
    def query_region_async(self, table, coordinates, radius, *, get_query_payload=False, cache=None,
                           **criteria):
        """
        Filter a table using a cone search around specified coordinates

        Parameters
        ----------
        table : str
            The name of the table to query. A list of the tables on the Exoplanet Archive can be
            found on the documentation page [1]_.
        coordinates : str or `~astropy.coordinates`
            The coordinates around which to query.
        radius : str or `~astropy.units.Quantity`
            The radius of the cone search. Assumed to be have units of degrees if not provided as
            a ``Quantity``.
        get_query_payload : bool, optional
            Just return the dict of HTTP request parameters. Defaults to ``False``.
        cache : bool, optional
            Should the request result be cached? This can be useful for large repeated queries,
            but since the data in the archive is updated regularly, this defaults to ``False``.
        **criteria
            Any other filtering criteria to apply. These are described in detail in the archive
            documentation [1]_, but some examples include ``select="*"`` to return all columns of
            the queried table or ``where=pl_name='K2-18 b'`` to filter a specific column.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.

        References
        ----------

        .. [1] `NASA Exoplanet Archive API Documentation
           <https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html>`_
        """
        coordinates = commons.parse_coordinates(coordinates)

        # if radius is just a number we assume degrees
        if isinstance(radius, (int, float)):
            radius = radius * u.deg
        radius = coord.Angle(radius)

        criteria["ra"] = coordinates.ra.deg
        criteria["dec"] = coordinates.dec.deg
        criteria["radius"] = "{0} degree".format(radius.deg)

        return self.query_criteria_async(
            table, get_query_payload=get_query_payload, cache=cache, **criteria,
        )

    @class_or_instance
    def query_object_async(self, object_name, *, table="exoplanets", get_query_payload=False,
                           cache=None, regularize=True, **criteria):
        """
        Search the global tables for information about a confirmed planet or planet host

        The tables available to this query are the following (more information can be found on
        the archive's documentation page [1]_):

        - ``exoplanets``: This table contains parameters derived from a single, published
          reference that are designated as the archive's default parameter set.
        - ``compositepars``: This table contains a full set of parameters compiled from multiple,
          published references.
        - ``exomultpars``: This table includes all sets of planet and stellar parameters for
          confirmed planets and hosts in the archive.

        Parameters
        ----------
        object_name : str
            The name of the planet or star.  If ``regularize`` is ``True``, an attempt will be made
            to regularize this name using the ``aliastable`` table.
        table : [``"exoplanets"``, ``"compositepars"``, or ``"exomultpars"``], optional
            The table to query, must be one of the supported tables: ``"exoplanets"``,
            ``"compositepars"``, or ``"exomultpars"``. Defaults to ``"exoplanets"``.
        get_query_payload : bool, optional
            Just return the dict of HTTP request parameters. Defaults to ``False``.
        cache : bool, optional
            Should the request result be cached? This can be useful for large repeated queries,
            but since the data in the archive is updated regularly, this defaults to ``False``.
        regularize : bool, optional
            If ``True``, the ``aliastable`` will be used to regularize the target name.
        **criteria
            Any other filtering criteria to apply. Values provided using the ``where`` keyword will
            be ignored.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.

        References
        ----------

        .. [1] `NASA Exoplanet Archive API Documentation
           <https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html>`_
        """
        prefix = OBJECT_TABLES.get(table, None)
        if prefix is None:
            raise InvalidQueryError(
                "Invalid table '{0}'. The allowed options are: {1}".format(
                    table, OBJECT_TABLES.keys()
                )
            )

        if regularize:
            object_name = self._regularize_object_name(object_name)

        if "where" in criteria:
            warnings.warn(
                "Any filters using the 'where' argument are ignored in ``query_object``",
                InputWarning,
            )
        criteria["where"] = "{0}hostname='{1}' OR {0}name='{1}'".format(prefix, object_name.strip())

        return self.query_criteria_async(
            table, get_query_payload=get_query_payload, cache=cache, **criteria,
        )

    @class_or_instance
    def query_aliases(self, object_name, *, cache=None):
        """
        Search for aliases for a given confirmed planet or planet host

        Parameters
        ----------
        object_name : str
            The name of a planet or star to regularize using the ``aliastable`` table.
        cache : bool, optional
            Should the request result be cached? This can be useful for large repeated queries,
            but since the data in the archive is updated regularly, this defaults to ``False``.

        Returns
        -------
        response : list
            A list of aliases found for the object name. The default name will be listed first.
        """
        return list(
            self.query_criteria(
                "aliastable", objname=object_name.strip(), cache=cache, format="csv"
            )["aliasdis"]
        )

    @class_or_instance
    def _regularize_object_name(self, object_name):
        """Regularize the name of a planet or planet host using the ``aliastable`` table"""
        try:
            aliases = self.query_aliases(object_name, cache=False)
        except RemoteServiceError:
            aliases = []
        if aliases:
            return aliases[0]
        warnings.warn("No aliases found for name: '{0}'".format(object_name), NoResultsWarning)
        return object_name

    def _handle_error(self, text):
        """
        Parse the response from a request to see if it failed

        Parameters
        ----------
        text : str
            The decoded body of the response.

        Raises
        ------
        InvalidColumnError :
            If ``select`` included an invalid column.
        InvalidTableError :
            If the queried ``table`` does not exist.
        RemoteServiceError :
            If anything else went wrong.
        """
        # Error messages will always be formatted starting with the word "ERROR"
        if not text.startswith("ERROR"):
            return

        # Some errors have the form:
        #   Error type: ...
        #   Message: ...
        # so we'll parse those to try to provide some reasonable feedback to the user
        error_type = None
        error_message = None
        for line in text.replace("<br>", "").splitlines():
            match = re.search(r"Error Type:\s(.+)$", line)
            if match:
                error_type = match.group(1).strip()
                continue

            match = re.search(r"Message:\s(.+)$", line)
            if match:
                error_message = match.group(1).strip()
                continue

        # If we hit this condition, that means that we weren't able to parse the error so we'll
        # just throw the full response
        if error_type is None or error_message is None:
            raise RemoteServiceError(text)

        # A useful special is if a column name is unrecognized. This has the format
        #   Error type: SystemError
        #   Message: ... "NAME_OF_COLUMN": invalid identifier ...
        if error_type.startswith("SystemError"):
            match = re.search(r'"(.*)": invalid identifier', error_message)
            if match:
                raise InvalidQueryError(
                    (
                        "'{0}' is an invalid identifier. This error can be caused by invalid "
                        "column names, missing quotes, or other syntax errors"
                    ).format(match.group(1).lower())
                )

        elif error_type.startswith("UserError"):
            # Another important one is when the table is not recognized. This has the format:
            #   Error type: UserError - "table" parameter
            #   Message: ... "NAME_OF_TABLE" is not a valid table.
            match = re.search(r'"(.*)" is not a valid table', error_message)
            if match:
                raise InvalidTableError("'{0}' is not a valid table".format(match.group(1).lower()))

            raise InvalidQueryError("{0}\n{1}".format(error_type, error_message))

        # Finally just return the full error message if we got here
        message = "\n".join(line for line in (error_type, error_message) if line is not None)
        raise RemoteServiceError(message)

    def _fix_units(self, data):
        """
        Fix any undefined units using a set of hacks

        Parameters
        ----------
        data : `~astropy.table.Table`
            The original data table without units.

        Returns
        -------
        new_data : `~astropy.table.QTable` or `~astropy.table.Table`
            The original ``data`` table with units applied where possible.
        """

        # To deal with masked data and quantities properly, we need to construct the QTable
        # manually so we'll loop over the columns and process each one independently
        column_names = list(data.columns)
        column_data = []
        column_masks = dict()
        for col in column_names:
            unit = data[col].unit
            unit = UNIT_MAPPER.get(str(unit), unit)
            if isinstance(unit, u.UnrecognizedUnit):
                unit_str = str(unit).lower()
                if unit_str == "earth" and "prad" in col:
                    unit = u.R_earth
                elif unit_str == "solar" and "radius" in col.lower():
                    unit = u.R_sun
                elif unit_str == "solar" and "mass" in col.lower():
                    unit = u.M_sun
                elif (
                    col.startswith("mlmag")
                    or col.startswith("mlext")
                    or col.startswith("mlcol")
                    or col.startswith("mlred")
                ):
                    unit = u.mag

                else:  # pragma: nocover
                    warnings.warn("Unrecognized unit: '{0}'".format(unit), AstropyWarning)

            # Here we're figuring out out if the column is masked because this doesn't
            # play nice with quantities so we need to keep track of the mask separately.
            try:
                column_masks[col] = data[col].mask
            except AttributeError:
                pass
            else:
                data[col].mask[:] = False

            # Deal with strings consistently
            if data[col].dtype == np.object:
                data[col] = data[col].astype(str)

            data[col].unit = unit
            column_data.append(data[col])

        # Build the new `QTable` and copy over the data masks if there are any
        result = QTable(column_data, names=column_names, masked=len(column_masks) > 0)
        for key, mask in column_masks.items():
            result[key].mask = mask

        return result

    def _parse_result(self, response, verbose=False):
        """
        Parse the result of a `~requests.Response` object and return an `~astropy.table.Table`

        Parameters
        ----------
        response : `~requests.Response`
            The response from the server.
        verbose : bool
            Currently has no effect.

        Returns
        -------
        data : `~astropy.table.Table` or `~astropy.table.QTable`
        """

        # Extract the decoded body of the response
        text = response.text

        # Raise an exception if anything went wrong
        self._handle_error(text)

        # Parse the requested format to figure out how to parse the returned data
        fmt = response.requested_format.lower()
        if "ascii" in fmt or "ipac" in fmt:
            data = ascii.read(text, format="ipac", fast_reader=False, converters=CONVERTERS)
        elif "csv" in fmt:
            data = ascii.read(text, format="csv", fast_reader=False, converters=CONVERTERS)
        elif "bar" in fmt or "pipe" in fmt:
            data = ascii.read(text, fast_reader=False, delimiter="|", converters=CONVERTERS)
        elif "xml" in fmt or "table" in fmt:
            data = parse_single_table(io.BytesIO(response.content)).to_table()
        else:
            data = ascii.read(text, fast_reader=False, converters=CONVERTERS)

        # Fix any undefined units
        data = self._fix_units(data)

        # For backwards compatibility, add a `sky_coord` column with the coordinates of the object
        # if possible
        if "ra" in data.columns and "dec" in data.columns:
            data["sky_coord"] = SkyCoord(ra=data["ra"], dec=data["dec"], unit=u.deg)

        if not data:
            warnings.warn("Query returned no results.", NoResultsWarning)

        return data

    def _handle_all_columns_argument(self, **kwargs):
        """
        Deal with the ``all_columns`` argument that was exposed by earlier versions

        This method will warn users about this deprecated argument and update the query syntax
        to use ``select='*'``.
        """
        # We also have to manually pop these arguments from the dict because
        # `deprecated_renamed_argument` doesn't do that for some reason for all supported astropy
        # versions (v3.1 was beheaving as expected)
        kwargs.pop("show_progress", None)
        kwargs.pop("table_path", None)

        # Deal with `all_columns` properly
        if kwargs.pop("all_columns", None):
            kwargs["select"] = kwargs.get("select", "*")

        return kwargs

    @deprecated(since="v0.4.1", alternative="query_object")
    @deprecated_renamed_argument(["show_progress", "table_path"],
                                 [None, None], "v0.4.1", arg_in_kwargs=True)
    def query_planet(self, planet_name, cache=None, regularize=True, **criteria):
        """
        Search the ``exoplanets`` table for a confirmed planet

        Parameters
        ----------
        planet_name : str
            The name of a confirmed planet. If ``regularize`` is ``True``, an attempt will be made
            to regularize this name using the ``aliastable`` table.
        cache : bool, optional
            Should the request result be cached? This can be useful for large repeated queries,
            but since the data in the archive is updated regularly, this defaults to ``False``.
        regularize : bool, optional
            If ``True``, the ``aliastable`` will be used to regularize the target name.
        **criteria
            Any other filtering criteria to apply. Values provided using the ``where`` keyword will
            be ignored.
        """
        if regularize:
            planet_name = self._regularize_object_name(planet_name)
        criteria = self._handle_all_columns_argument(**criteria)
        criteria["where"] = "pl_name='{0}'".format(planet_name.strip())
        return self.query_criteria("exoplanets", cache=cache, **criteria)

    @deprecated(since="v0.4.1", alternative="query_object")
    @deprecated_renamed_argument(["show_progress", "table_path"],
                                 [None, None], "v0.4.1", arg_in_kwargs=True)
    def query_star(self, host_name, cache=None, regularize=True, **criteria):
        """
        Search the ``exoplanets`` table for a confirmed planet host

        Parameters
        ----------
        host_name : str
            The name of a confirmed planet host. If ``regularize`` is ``True``, an attempt will be
            made to regularize this name using the ``aliastable`` table.
        cache : bool, optional
            Should the request result be cached? This can be useful for large repeated queries,
            but since the data in the archive is updated regularly, this defaults to ``False``.
        regularize : bool, optional
            If ``True``, the ``aliastable`` will be used to regularize the target name.
        **criteria
            Any other filtering criteria to apply. Values provided using the ``where`` keyword will
            be ignored.
        """
        if regularize:
            host_name = self._regularize_object_name(host_name)
        criteria = self._handle_all_columns_argument(**criteria)
        criteria["where"] = "pl_hostname='{0}'".format(host_name.strip())
        return self.query_criteria("exoplanets", cache=cache, **criteria)


NasaExoplanetArchive = NasaExoplanetArchiveClass()
