# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
HEASARC
====


Module to query the NASA High Energy Archive HEASARC.
"""

import os
from typing import Union
import shutil
import tarfile
import warnings
from io import StringIO, BytesIO
from astropy.table import Table
from astropy.io import fits
from astropy import coordinates
from astropy import units as u

import pyvo

from astroquery import log
from ..query import BaseQuery
from ..utils import commons, async_to_sync, parse_coordinates
from ..exceptions import InvalidQueryError, NoResultsWarning
from . import conf

__all__ = ['Heasarc', 'HeasarcClass', 'HeasarcXaminClass', 'Xamin']


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


@async_to_sync
class HeasarcXaminClass(BaseQuery):
    """Class for accessing HEASARC data using XAMIN.

    Example Usage:
    ...

    """

    # we can move url to Config later
    VO_URL = conf.VO_URL
    TAR_URL = conf.TAR_URL
    S3_BUCKET = conf.S3_BUCKET
    timeout = conf.timeout

    def __init__(self):
        """Initialize some basic useful variables"""
        super().__init__()
        self._tap = None

        self._datalink = None
        self._session = None

    @property
    def tap(self):
        """TAP service"""
        if self._tap is None:
            self._tap = pyvo.dal.TAPService(f'{self.VO_URL}/tap', session=self._session)
            self._session = self._tap._session
        return self._tap

    def tables(self, master=False):
        """Return a dictionay of all available table in the
        form {name: description}

        Parameters
        ----------
        master: bool
            Select only master tables. Default is False

        Return
        ------
        `~astropy.table.Table` with columns: name, description

        """

        # use 'mast' to include both 'master' and 'mastr'
        names, desc = [], []
        for lab, tab in self.tap.tables.items():
            if 'TAP' in lab or (master and 'mast' not in lab):
                continue
            names.append(lab)
            desc.append(tab.description)
        return Table({'name': names, 'description':desc})


    def columns(self, table_name, full=False):
        """Return a dictionay of the columns available in table_name

        Parameters
        ----------
        table_name: str
            The name of table as a str
        full: bool
            If True, return the full list of columns as a vo
            TableParam objects. May be useful to check units etc.
            If False, return a `~astropy.table.Table` (name, description)
            for each table column.

        """
        tables = self.tap.tables
        if table_name not in tables.keys():
            msg = f'{table_name} is not available as a public table. '
            msg += 'The list of tables can be accessed in Heasarc.tables()'
            raise ValueError(msg)

        if full:
            cols = tables[table_name].columns
        else:
            names, desc = [], []
            for col in tables[table_name].columns:
                names.append(col.name)
                desc.append(col.description)
            cols = Table({'name': names, 'description':desc})

        return cols

    def query_tap(self, query, *, maxrec=None):
        """
        Send query to HEASARC's Xamin TAP using ADQL.
        Results in `~pyvo.dal.TAPResults` format.
        result.to_table gives `~astropy.table.Table` format.

        Parameters
        ----------
        query : str
            ADQL query to be executed
        maxrec : int
            maximum number of records to return

        Returns
        -------
        result : `~pyvo.dal.TAPResults`
            TAP query result.
        result.to_table : `~astropy.table.Table`
            TAP query result as `~astropy.table.Table`
        result.to_qtable : `~astropy.table.QTable`
            TAP query result as `~astropy.table.QTable`

        """
        log.debug(f'TAP query: {query}')
        return self.tap.search(query, language='ADQL', maxrec=maxrec)

    def query_region(self, position=None, *, table=None, spatial='cone',
                     radius=1 * u.arcmin, width=None, polygon=None,
                     get_query_payload=False, columns=None,
                     verbose=False, maxrec=None):
        """
        Queries the HEASARC TAP server around a coordinate and returns a `~astropy.table.Table` object.

        Parameters
        ----------
        position : str, `astropy.coordinates` object
            Gives the position of the center of the cone or box if performing a cone or box search.
            Required if spatial is ``'cone'`` or ``'box'``. Ignored if spatial is ``'polygon'`` or
            ``'all-sky'``.
        table : str
            The table to query. To list the available tables, use
            :meth:`~astroquery.heasarc.HeasarcXaminClass.tables`.
        spatial : str
            Type of spatial query: ``'cone'``, ``'box'``, ``'polygon'``, and
            ``'all-sky'``. Defaults to ``'cone'``.
        radius : str or `~astropy.units.Quantity` object, [optional for spatial == ``'cone'``]
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 1 arcmin.
        width : str, `~astropy.units.Quantity` object [Required for spatial == ``'box'``.]
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `astropy.units`
            may also be used.
        polygon : list, [Required for spatial is ``'polygon'``]
            A list of ``(ra, dec)`` pairs (as tuples), in decimal degrees,
            outlining the polygon to search in. It can also be a list of
            `astropy.coordinates` object or strings that can be parsed by
            `astropy.coordinates.ICRS`.
        get_query_payload : bool, optional
            If `True` then returns the generated ADQL query as str.
            Defaults to `False`.
        columns : str, optional
            Target column list with value separated by a comma(,)
        verbose : bool, optional
            If False, supress vo warnings.
        maxrec : int, optional
            Maximum number of records


        Returns
        -------
        table : A `~astropy.table.Table` object.
        """
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()

        if table is None:
            raise InvalidQueryError("table name is required! Use 'xray' "
                                    "to search the master X-ray table")

        if columns is None:
            columns = '*'

        adql = f'SELECT {columns} FROM {table}'

        if spatial.lower() == 'all-sky':
            where = ''
        elif spatial.lower() == 'polygon':
            try:
                coords_list = [parse_coordinates(coord).icrs for coord in polygon]
            except TypeError:
                # to handle the input cases that worked before
                try:
                    coords_list = [coordinates.SkyCoord(*coord).icrs for coord in polygon]
                except u.UnitTypeError:
                    warnings.warn("Polygon endpoints are being interpreted as "
                                  "RA/Dec pairs specified in decimal degree units.")
                    coords_list = [coordinates.SkyCoord(*coord, unit='deg').icrs for coord in polygon]

            coords_str = [f'{coord.ra.deg},{coord.dec.deg}' for coord in coords_list]
            where = (" WHERE CONTAINS(POINT('ICRS',ra,dec),"
                     f"POLYGON('ICRS',{','.join(coords_str)}))=1")
        else:
            coords_icrs = parse_coordinates(position).icrs
            ra, dec = coords_icrs.ra.deg, coords_icrs.dec.deg

            if spatial.lower() == 'cone':
                if isinstance(radius, str):
                    radius = coordinates.Angle(radius)
                where = (" WHERE CONTAINS(POINT('ICRS',ra,dec),"
                         f"CIRCLE('ICRS',{ra},{dec},{radius.to(u.deg).value}))=1")
            elif spatial.lower() == 'box':
                if isinstance(width, str):
                    width = coordinates.Angle(width)
                where = (" WHERE CONTAINS(POINT('ICRS',ra,dec),"
                         f"BOX('ICRS',{ra},{dec},{width.to(u.deg).value},{width.to(u.deg).value}))=1")
            else:
                raise ValueError("Unrecognized spatial query type. Must be one of "
                                 "'cone', 'box', 'polygon', or 'all-sky'.")

        adql += where

        if get_query_payload:
            return adql
        response = self.query_tap(query=adql, maxrec=maxrec)

        # save the response in case we want to use it later
        self._query_result = response
        self._tablename = table

        return response.to_table()

    def get_links(self, query_result=None, tablename=None):
        """Get links to data products
        Use vo/datalinks to query the data products for some query_results.

        Parameters
        ----------
        query_result : `astropy.table.Table`, optional
            A table that contain the search resutls. Typically as
            returned by query_region. If None, use the table from the
            most recent query_region call.
        tablename : str
            The table name for the which the query_result belongs to.
            If None, use the one from the most recent query_region call.

        Returns
        -------
        table : A `~astropy.table.Table` object.
        """
        if query_result is None:
            if not hasattr(self, '_query_result') or self._query_result is None:
                raise ValueError('query_result is None, and none '
                                 'found from a previous search')
            else:
                query_result = self._query_result

        if not isinstance(query_result, Table):
            raise TypeError('query_result need to be an astropy.table.Table')

        # make sure we have a column __row
        if '__row' not in query_result.colnames:
            raise ValueError('No __row column found in query_result. '
                             'This may not be standard results table.')

        if tablename is None:
            tablename = self._tablename
        if not (isinstance(tablename, str) and tablename in self.tap.tables.keys()):
            raise ValueError(f'Unknown table name: {tablename}')

        # datalink url
        dlink_url = f'{self.VO_URL}/datalink/{tablename}'

        query = pyvo.dal.adhoc.DatalinkQuery(
            baseurl=dlink_url,
            id=query_result['__row'],
            session=self._session
        )
        dl_result = query.execute().to_table()
        dl_result = dl_result[dl_result['content_type'] == 'directory']
        dl_result = dl_result[['ID', 'access_url', 'content_length']]

        # add sciserver and s3 columns
        newcol = [f"/FTP/{row.split('FTP/')[1]}".replace('//', '/')
                  for row in dl_result['access_url']]
        dl_result.add_column(newcol, name='sciserver', index=2)
        newcol = [f"s3://{self.S3_BUCKET}/{row[5:]}" for row in dl_result['sciserver']]
        dl_result.add_column(newcol, name='aws', index=3)

        return dl_result

    def enable_cloud(self, provider='aws', profile=None):
        """
        Enable downloading public files from the cloud.
        Requires the boto3 library to function.

        Parameters
        ----------
        provider : str
            Which cloud data provider to use. Currently, only 'aws' is supported
        profile : str
            Profile to use to identify yourself to the cloud provider (usually in ~/.aws/config).
        """

        try:
            import boto3
            import botocore
        except ImportError:
            raise ImportError('The cloud feature requires the boto3 package. Install it first.')

        if profile is None:
            log.info('Enabling annonymous cloud data access ...')
            config = botocore.client.Config(signature_version=botocore.UNSIGNED)
            self.s3_resource = boto3.resource('s3', config=config)
        else:
            log.info('Enabling cloud data access with profile: {profile} ...')
            session = boto3.session.Session(profile_name=profile)
            self.s3_resource = session.resource(service_name='s3')
            s3_resource.meta.client

        self.s3_client = self.s3_resource.meta.client
        self.bkt = self.s3_resource.Bucket(self.S3_BUCKET)


    def download_data(self, links, host='heasarc', location='.'):
        """Download data products in links with a choice of getting the
        data from either the heasarc server, sciserver, or the cloud in AWS.


        Parameters
        ----------
        links : `astropy.table.Table`
            The result from get_links
        host : str
            The data host. The options are: heasarc (defaul), sciserver, aws.
            If host == 'sciserver', data is copied from the local mounted data drive.
            If host == 'aws', data is downloaded from Amazon S3 Open Data Repository.
        location : str
            local folder where the downloaded file will be saved.
            Default is current working directory

        Note
        ----
        Downloading more than ~10 observations from the HEASARC will likely fail.
        If you have more than 10 links, group them and make several requests.
        """

        if len(links) == 0:
            raise ValueError('Input links table is empty')

        if host not in ['heasarc', 'sciserver', 'aws']:
            raise ValueError('host has to be one of heasarc, sciserver, aws ')

        host_column = 'access_url' if host == 'heasarc' else host
        if not host_column in links.colnames:
            raise ValueError(
                f'No {host_column} column found in the table. Call ~get_links first'
            )

        if host == 'heasarc':

            log.info('Downloading data from the HEASARC ...')
            self._download_heasarc(links, location)

        elif host == 'sciserver':

            log.info('Copying data on Sciserver ...')
            self._copy_sciserver(links, location)

        elif host == 'aws':

            log.info('Downloading data AWS S3 ...')
            self._download_s3(links, location)


    def _download_heasarc(self, links, location='.'):
        """Download data from the heasarc main server using xamin's tar servlet

        Do not call directly.
        Users should be using ~self.download_data instead

        """
        max_download = 10
        if len(links) > max_download:
            raise ValueError(
                'Too many links requested for download. Consider splitting the list '
                f'into smaller chunks {max_download} links each'
            )

        file_list = [f"/FTP/{link.split('FTP/')[1]}"
                     for link in links['access_url']]
        params = {
            'files': f'>{"&&>".join(file_list)}&&',
            'filter': ''
        }

        # get local_filepath name
        local_filepath = f'{location}/xamin.tar'
        iname = 1
        while os.path.exists(local_filepath):
            local_filepath = f'{location}/xamin.{iname}.tar'
            iname += 1

        log.info(f'Downloading to {local_filepath} ...')
        self._download_file(self.TAR_URL, local_filepath,
                            timeout=self.timeout,
                            continuation=False, cache=False, method="POST",
                            head_safe=False, params=params)

        # if all good and we have a tar file untar it
        if tarfile.is_tarfile(local_filepath):
            log.info(f'Untar {local_filepath} to {location} ...')
            tfile = tarfile.TarFile(local_filepath)
            tfile.extractall(path=location)
            os.remove(local_filepath)
        else:
            raise ValueError('An error ocurred when downloading the data. Retry again.')


    def _copy_sciserver(self, links, location='.'):
        """Copy data from the local archive on sciserver

        Do not call directly.
        Users should be using ~self.download_data instead

        """
        if not os.path.exists('/FTP/'):
            raise FileNotFoundError(
                'No data archive found. This should be run on Sciserver '
                'with the data drive mounted.'
            )

        if not os.path.exists(location):
            os.mkdir(location)

        for link in links['sciserver']:
            log.info(f'Copying to {link} from the data drive ...')
            if not os.path.exists(link):
                raise ValueError(
                    f'No data found in {link}. '
                    'Make sure you are running this on Sciserver. '
                    'If you think data is missing, please contact the Heasarc Help desk'
                )
            if os.path.isdir(link):
                shutil.copytree(link, location)
            else:
                shutil.copy(link, location)


    def _download_s3(self, links, locaiton='.'):
        """Download data from AWS S3
        Assuming open access.

        Do not call directly.
        Users should be using ~self.download_data instead

        """
        keys_list = [link for link in links['aws']]
        if not hasattr(self, 's3_resource'):
            # all the data is public for now; no profile is needed
            self.enable_cloud(provider='aws', profile=None)

        def _s3_download_dir(client, bkt, path, local):
            """call bkt.download_file several times to download a directory"""
            paginator = client.get_paginator('list_objects')
            for result in paginator.paginate(Bucket=self.S3_BUCKET,
                                             Delimiter='/', Prefix=path):
                pref = result.get('CommonPrefixes', None)
                if pref is not None:
                    for subdir in pref:
                        # loop over subdirectories
                        new_path = subdir['Prefix']
                        base = path.strip('/').split('/')[-1]
                        new_base = new_path.strip('/').split('/')[-1]
                        new_local = f"{local}/{base}/{new_base}"
                        _s3_download_dir(client, bkt, new_path, new_local)

                content = result.get('Contents', [])
                for file in content:
                    key = file.get('Key')
                    dest = os.path.join(local, key.split('/')[-1])
                    destdir = os.path.dirname(dest)
                    if not os.path.exists(destdir):
                        os.makedirs(destdir)
                    if not key.endswith('/'):
                        bkt.download_file(key, dest)

        for key in keys_list:
            print(f'downloading {key}')
            path = key.replace(f's3://{self.S3_BUCKET}/', '')
            _s3_download_dir(self.s3_client, self.bkt, path, locaiton)


Xamin = HeasarcXaminClass()
Heasarc = HeasarcClass()
