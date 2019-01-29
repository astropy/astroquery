# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
from six import BytesIO
from astropy.table import Table
from astropy.io import fits
from astropy import coordinates
from astropy import units as u
from ..query import BaseQuery
from ..utils import commons
from ..utils import async_to_sync
from ..exceptions import InvalidQueryError
from . import conf

__all__ = ['Heasarc', 'HeasarcClass']


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

    def query_async(self, request_payload, cache=True, url=conf.server):
        """
        Submit a query based on a given request_payload. This allows detailed
        control of the query to be submitted.
        """
        response = self._request('GET', url, params=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        return response

    def query_mission_list(self, cache=True, get_query_payload=False):
        """
        Returns a list of all available mission tables with descriptions
        """
        request_payload = self._args_to_payload(
            Entry='none',
            mission='xxx',
            displaymode='BatchDisplay'
        )

        if get_query_payload:
            return request_payload

        # Parse the results specially (it's ascii format, not fits)
        response = self.query_async(
            request_payload,
            url=conf.mission_server,
            cache=cache
        )
        data = BytesIO(response.content)
        table = Table.read(data, format='ascii.fixed_width_two_line',
                           delimiter='+', header_start=1, position_line=2,
                           data_start=3, data_end=-1)
        return table

    def query_mission_cols(self, mission, cache=True, get_query_payload=False,
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
        All other parameters have no effect
        """
        # Query fails if nothing is found, so set search radius very large and
        # only take a single value (all we care about is the column names)
        kwargs['resultmax'] = 1

        # By default, return all column names
        fields = kwargs.get('fields', None)
        if fields is None:
            kwargs['fields'] = 'All'

        response = self.query_region_async(position='0.0 0.0', mission=mission,
                                           radius='361 degree', cache=cache,
                                           get_query_payload=get_query_payload,
                                           **kwargs)

        # Return payload if requested
        if get_query_payload:
            return response

        return self._parse_result(response).colnames

    def query_object_async(self, object_name, mission,
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

    def query_region_async(self, position, mission, radius,
                           cache=True, get_query_payload=False,
                           **kwargs):
        """
        Query around specific set of coordinates within a given mission
        catalog. Method first converts the supplied coordinates into the FK5
        reference frame and searches for sources from there. Because of this,
        returned offset coordinates may look different than the ones supplied.

        Parameters
        ----------
        position : `astropy.coordinates` or str
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
        **kwargs :
            see `~astroquery.heasarc.HeasarcClass._args_to_payload` for list
            of additional parameters that can be used to refine search query
        """
        # Convert the coordinates to FK5
        c = commons.parse_coordinates(position).transform_to(coordinates.FK5)
        kwargs['coordsys'] = 'fk5'
        kwargs['equinox'] = 2000

        # Generate the request
        request_payload = self._args_to_payload(
            mission=mission,
            entry="{},{}".format(c.ra.degree, c.dec.degree),
            radius=u.Quantity(radius),
            **kwargs
        )

        # Return payload if requested
        if get_query_payload:
            return request_payload

        # Submit the request
        return self.query_async(request_payload, cache=cache)

    def _fallback(self, content):
        """
        Blank columns which have to be converted to float or in fail so
        lets fix that by replacing with -1's
        """

        data = BytesIO(content)
        header = fits.getheader(data, 1)  # Get header for column info
        colstart = [y for x, y in header.items() if "TBCOL" in x]
        collens = [int(float(y[1:]))
                   for x, y in header.items() if "TFORM" in x]
        new_table = []

        old_table = content.split("END")[-1].strip()
        for line in old_table.split("\n"):
            newline = []
            for n, tup in enumerate(zip(colstart, collens), start=1):
                cstart, clen = tup
                part = line[cstart - 1:cstart + clen]
                newline.append(part)
                if len(part.strip()) == 0:
                    if header["TFORM%i" % n][0] in ["F", "I"]:
                        # extra space is required to sperate column
                        newline[-1] = "-1".rjust(clen) + " "
            new_table.append("".join(newline))

        data = BytesIO(content.replace(old_table, "\n".join(new_table)))
        return Table.read(data, hdu=1)

    def _parse_result(self, response, verbose=False):
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

        try:
            data = BytesIO(response.content)
            table = Table.read(data, hdu=1)
            return table
        except ValueError:
            return self._fallback(response.content)

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
        # Define the basic query for this object
        request_payload = dict(
            tablehead=('name=BATCHRETRIEVALCATALOG_2.0 {}'
                       .format(kwargs.get('mission'))),
            Entry=kwargs.get('entry', 'none'),
            Action=kwargs.get('action', 'Query'),
            displaymode=kwargs.get('displaymode', 'FitsDisplay')
        )

        # Fill in optional information for refined queries

        # Handle queries involving coordinates
        coordsys = kwargs.get('coordsys', 'fk5')
        if coordsys.lower() == 'fk5':
            request_payload['Coordinates'] = 'Equatorial: R.A. Dec'

        elif coordsys.lower() == 'fk4':
            request_payload['Coordinates'] = 'Equatorial: R.A. Dec'
            request_payload['equinox'] = 1950

        elif coordsys.lower() == 'equatorial':
            request_payload['Coordinates'] = 'Equatorial: R.A. Dec'

            equinox = kwargs.get('equinox', None)
            if equinox is not None:
                request_payload['Equinox'] = str(equinox)

        elif coordsys.lower() == 'galactic':
            request_payload['Coordinates'] = 'Galactic: LII BII'

        else:
            raise ValueError("'coordsys' parameter must be one of {!s}"
                             .format(self.coord_systems))

        # Specify which table columns are to be returned
        fields = kwargs.get('fields', None)
        if fields is not None:
            if fields.lower() == 'standard':
                request_payload['Fields'] = 'Standard'
            elif fields.lower() == 'all':
                request_payload['Fields'] = 'All'
            else:
                request_payload['varon'] = fields.lower().split(',')

        # Set search radius (arcmin)
        radius = kwargs.get('radius', None)
        if radius is not None:
            request_payload['Radius'] = "{}".format(radius.to(u.arcmin))

        # Maximum number of results to be returned
        resultmax = kwargs.get('resultmax', None)
        if resultmax is not None:
            request_payload['ResultMax'] = int(resultmax)

        # Set variable for sorting results
        sortvar = kwargs.get('sortvar', None)
        if sortvar is not None:
            request_payload['sortvar'] = sortvar.lower()

        return request_payload


Heasarc = HeasarcClass()
