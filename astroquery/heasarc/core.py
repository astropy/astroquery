# Licensed under a 3-clause BSD style license - see LICENSE.rst

from typing import Union
import warnings
from io import StringIO, BytesIO
from astropy.table import Table
from astropy.io import fits
from astropy import coordinates
from astropy import units as u
from ..query import BaseQuery
from ..utils import commons
from ..utils import async_to_sync
from ..exceptions import InvalidQueryError, NoResultsWarning
from . import conf

__all__ = ['Heasarc', 'HeasarcClass']


def Table_read(*args, **kwargs):
    if commons.ASTROPY_LT_5_1:
        return Table.read(*args, **kwargs)
    else:
        return Table.read(*args, **kwargs, unit_parse_strict='silent')


@async_to_sync
class HeasarcClass(BaseQuery):

    """
    HEASARC query class.

    For a list of available HEASARC mission tables, visit:
        https://heasarc.gsfc.nasa.gov/cgi-bin/W3Browse/w3catindex.pl
    """

    URL = conf.server
    TIMEOUT = conf.timeout
    coord_systems = ['fk5', 'fk4', 'equatorial', 'galactic']

    def query_async(self, request_payload, *, cache=True, url=None):
        """
        Submit a query based on a given request_payload. This allows detailed
        control of the query to be submitted.

        cache (bool) defaults to True. If set overrides global caching behavior.
        See :ref:`caching documentation <astroquery_cache>`.
        """

        if url is None:
            url = conf.server

        response = self._request('GET', url, params=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        return response

    def query_mission_list(self, *, cache=True, get_query_payload=False):
        """
        Returns a list of all available mission tables with descriptions

        cache (bool) defaults to True. If set overrides global caching behavior.
        See :ref:`caching documentation <astroquery_cache>`.
        """
        request_payload = self._args_to_payload(
            entry='none',
            mission='xxx',
            displaymode='BatchDisplay'
        )

        if get_query_payload:
            return request_payload

        # Parse the results specially (it's ascii format, not fits)
        response = self.query_async(
            request_payload,
            url=conf.server,
            cache=cache
        )
        data_str = response.text
        data_str = data_str.replace('Table xxx does not seem to exist!\n\n\n\nAvailable tables:\n', '')
        table = Table.read(data_str, format='ascii.fixed_width_two_line',
                           delimiter='+', header_start=1, position_line=2,
                           data_start=3, data_end=-1)
        return table

    def query_mission_cols(self, mission, *, cache=True, get_query_payload=False,
                           **kwargs):
        """
        Returns a list containing the names of columns that can be returned for
        a given mission table. By default all column names are returned.

        Parameters
        ----------
        mission : str
            Mission table (short name) to search from
        fields : str, optional
            Return format for columns from the server available options:
            * Standard      : Return default table columns
            * All (default) : Return all table columns
            * <custom>      : User defined csv list of columns to be returned
        cache : bool, optional
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.
        All other parameters have no effect
        """

        response = self.query_region_async(position=coordinates.SkyCoord(10, 10, unit='deg', frame='fk5'),
                                           mission=mission,
                                           radius='361 degree',
                                           cache=cache,
                                           get_query_payload=get_query_payload,
                                           resultsmax=1,
                                           fields='All')

        # Return payload if requested
        if get_query_payload:
            return response

        return self._parse_result(response).colnames

    def query_object_async(self, object_name, mission, *,
                           cache=True, get_query_payload=False,
                           **kwargs):
        """
        Query around a specific object within a given mission catalog

        Parameters
        ----------
        object_name : str
            Object to query around. To set search radius use the 'radius'
            parameter.
        mission : str
            Mission table to search from
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.
        **kwargs :
            see `~astroquery.heasarc.HeasarcClass._args_to_payload` for list
            of additional parameters that can be used to refine search query
        """
        request_payload = self._args_to_payload(
            mission=mission,
            entry=object_name,
            **kwargs
        )

        # Return payload if requested
        if get_query_payload:
            return request_payload

        return self.query_async(request_payload, cache=cache)

    def query_region_async(self, position: Union[coordinates.SkyCoord, str],
                           mission, radius, *, cache=True, get_query_payload=False,
                           **kwargs):
        """
        Query around specific set of coordinates within a given mission
        catalog. Method first converts the supplied coordinates into the FK5
        reference frame and searches for sources from there. Because of this,
        returned offset coordinates may look different than the ones supplied.

        Parameters
        ----------
        position : `astropy.coordinates.SkyCoord` or str
            The position around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as a string.
            (adapted from nrao module)
        mission : str
            Mission table to search from
        radius :
            Astropy Quantity object, or a string that can be parsed into one.
            e.g., '1 degree' or 1*u.degree.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.
        **kwargs :
            see `~astroquery.heasarc.HeasarcClass._args_to_payload` for list
            of additional parameters that can be used to refine search query
        """
        # Convert the coordinates to FK5
        c = commons.parse_coordinates(position).transform_to(coordinates.FK5)
        kwargs['coordsys'] = 'fk5'
        kwargs['equinox'] = 2000

        # Generate the request
        # Fixed string representation of coordinates ensures that request payload
        # does not depend on python/astropy version for the same input coordinates
        request_payload = self._args_to_payload(
            mission=mission,
            entry=f"{c.ra.degree:.10f},{c.dec.degree:.10f}",
            radius=u.Quantity(radius),
            **kwargs
        )

        # Return payload if requested
        if get_query_payload:
            return request_payload

        # Submit the request
        return self.query_async(request_payload, cache=cache)

    def _old_w3query_fallback(self, content):
        # old w3query (such as that used in ISDC) return very strange fits, with all ints

        fits_content = fits.open(BytesIO(content))

        for col in fits_content[1].columns:
            if col.disp is not None:
                col.format = col.disp
            else:
                col.format = str(col.format).replace("I", "A")

        tmp_out = BytesIO()
        fits_content.writeto(tmp_out)
        tmp_out.seek(0)

        return Table_read(tmp_out)

    def _fallback(self, text):
        """
        Blank columns which have to be converted to float or in fail so
        lets fix that by replacing with -1's
        """

        data = StringIO(text)
        header = fits.getheader(data, 1)  # Get header for column info
        colstart = [y for x, y in header.items() if "TBCOL" in x]
        collens = [int(float(y[1:]))
                   for x, y in header.items() if "TFORM" in x]

        new_table = []

        old_table = text.split("END")[-1].strip()
        for line in old_table.split("\n"):
            newline = []
            for n, tup in enumerate(zip(colstart, collens), start=1):
                cstart, clen = tup
                part = line[cstart - 1:cstart + clen]
                newline.append(part)
                if len(part.strip()) == 0:
                    if header["TFORM%i" % n][0] in ["F", "I"]:
                        # extra space is required to separate column
                        newline[-1] = "-1".rjust(clen) + " "
            new_table.append("".join(newline))

        data = StringIO(text.replace(old_table, "\n".join(new_table)))

        return Table_read(data, hdu=1)

    def _blank_table_fallback(self, data):
        """
        In late 2022, we started seeing examples where the null result came
        back as a FITS file with an ImageHDU and no BinTableHDU.
        """
        with fits.open(data) as fh:
            comments = fh[1].header['COMMENT']
        emptytable = Table()
        emptytable.meta['COMMENT'] = comments
        warnings.warn(NoResultsWarning("No matching rows were found in the query."))
        return emptytable

    def _parse_result(self, response, *, verbose=False):
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()

        if "BATCH_RETRIEVAL_MSG ERROR:" in response.text:
            raise InvalidQueryError("One or more inputs is not recognized by HEASARC. "
                                    "Check that the object name is in GRB, SIMBAD+Sesame, or "
                                    "NED format and that the mission name is as listed in "
                                    "query_mission_list().")
        elif "Software error:" in response.text:
            raise InvalidQueryError("Unspecified error from HEASARC database. "
                                    "\nCheck error message: \n{!s}".format(response.text))
        elif "NO MATCHING ROWS" in response.text:
            warnings.warn(NoResultsWarning("No matching rows were found in the query."))
            return Table()

        if "XTENSION= 'IMAGE   '" in response.text:
            data = BytesIO(response.content)
            return self._blank_table_fallback(data)

        try:
            data = BytesIO(response.content)
            return Table_read(data, hdu=1)
        except ValueError:
            try:
                return self._fallback(response.text)
            except Exception:
                return self._old_w3query_fallback(response.content)

    def _args_to_payload(self, **kwargs):
        """
        Generates the payload based on user supplied arguments

        Parameters
        ----------
        mission : str
            Mission table to query
        entry : str, optional
            Object or position for center of query. A blank value will return
            all entries in the mission table. Acceptable formats:
            * Object name : Name of object, e.g. 'Crab'
            * Coordinates : X,Y coordinates, either as 'degrees,degrees' or
              'hh mm ss,dd mm ss'
        fields : str, optional
            Return format for columns from the server available options:
            * Standard (default) : Return default table columns
            * All                : Return all table columns
            * <custom>           : User defined csv list of columns to be
              returned
        radius : float (arcmin), optional
            Astropy Quantity object, or a string that can be parsed into one.
            e.g., '1 degree' or 1*u.degree.
        coordsys: str, optional
            If 'entry' is a set of coordinates, this specifies the coordinate
            system used to interpret them. By default, equatorial coordinates
            are assumed. Possible values:
            * 'fk5' <default> (FK5 J2000 equatorial coordinates)
            * 'fk4'           (FK4 B1950 equatorial coordinates)
            * 'equatorial'    (equatorial coordinates, `equinox` param
              determines epoch)
            * 'galactic'      (Galactic coordinates)
        equinox : int, optional
            Epoch by which to interpret supplied equatorial coordinates
            (defaults to 2000, ignored if `coordsys` is not 'equatorial')
        resultmax : int, optional
            Set maximum query results to be returned
        sortvar : str, optional
            Set the name of the column by which to sort the results. By default
            the results are sorted by distance from queried object/position

        displaymode : str, optional
            Return format from server. Since the user does not interact with
            this directly, it's best to leave this alone
        action : str, optional
            Type of action to be taken (defaults to 'Query')
        """
        # User-facing parameters are lower case, while parameters as passed to the
        # HEASARC service are capitalized according to the HEASARC requirements.
        # The necessary transformations are done in this function.

        # Define the basic query for this object
        mission = kwargs.pop('mission')

        request_payload = dict(
            tablehead=('name=BATCHRETRIEVALCATALOG_2.0 {}'
                       .format(mission)),
            Entry=kwargs.pop('entry', 'none'),
            Action=kwargs.pop('action', 'Query'),
            displaymode=kwargs.pop('displaymode', 'FitsDisplay'),
            resultsmax=kwargs.pop('resultsmax', '10')
        )

        # Fill in optional information for refined queries

        # Handle queries involving coordinates
        coordsys = kwargs.pop('coordsys', 'fk5')
        equinox = kwargs.pop('equinox', None)

        if coordsys.lower() == 'fk5':
            request_payload['Coordinates'] = 'Equatorial: R.A. Dec'

        elif coordsys.lower() == 'fk4':
            request_payload['Coordinates'] = 'Equatorial: R.A. Dec'
            request_payload['equinox'] = 1950

        elif coordsys.lower() == 'equatorial':
            request_payload['Coordinates'] = 'Equatorial: R.A. Dec'

            if equinox is not None:
                request_payload['Equinox'] = str(equinox)

        elif coordsys.lower() == 'galactic':
            request_payload['Coordinates'] = 'Galactic: LII BII'

        else:
            raise ValueError("'coordsys' parameter must be one of {!s}"
                             .format(self.coord_systems))

        # Specify which table columns are to be returned
        fields = kwargs.pop('fields', None)
        if fields is not None:
            if fields.lower() == 'standard':
                request_payload['Fields'] = 'Standard'
            elif fields.lower() == 'all':
                request_payload['Fields'] = 'All'
            else:
                request_payload['varon'] = fields.lower().split(',')

        # Set search radius (arcmin)
        radius = kwargs.pop('radius', None)
        if radius is not None:
            request_payload['Radius'] = "{}".format(u.Quantity(radius).to(u.arcmin))

        # Maximum number of results to be returned
        resultmax = kwargs.pop('resultmax', None)
        if resultmax is not None:
            request_payload['ResultMax'] = int(resultmax)

        # Set variable for sorting results
        sortvar = kwargs.pop('sortvar', None)
        if sortvar is not None:
            request_payload['sortvar'] = sortvar.lower()

        # Time range variable
        _time = kwargs.pop('time', None)
        if _time is not None:
            request_payload['Time'] = _time

        if len(kwargs) > 0:
            mission_fields = [k.lower() for k in self.query_mission_cols(mission=mission)]

            for k, v in kwargs.items():
                if k.lower() in mission_fields:
                    request_payload['bparam_' + k.lower()] = v
                else:
                    raise ValueError(f"unknown parameter '{k}' provided, must be one of {mission_fields}")

        return request_payload


Heasarc = HeasarcClass()
