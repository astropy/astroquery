
import os

import shutil
import requests
import tarfile
import warnings
import numpy as np
from astropy.table import Table
from astropy import coordinates
from astropy import units as u
from astropy.utils.decorators import deprecated, deprecated_renamed_argument

import pyvo

from astroquery import log
from ..query import BaseQuery, BaseVOQuery
from ..utils import commons, parse_coordinates
from ..exceptions import InvalidQueryError, NoResultsWarning
from . import conf

__all__ = ['Heasarc', 'HeasarcClass']


class HeasarcClass(BaseVOQuery, BaseQuery):
    """Class for accessing HEASARC data with VO protocol using the Xamin backend.


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
        self._meta_info = None
        self._session = None

    @property
    def tap(self):
        """TAP service"""
        if self._tap is None:
            self._tap = pyvo.dal.TAPService(
                f'{self.VO_URL}/tap', session=self._session
            )
            self._session = self._tap._session
        return self._tap

    @property
    def _meta(self):
        """Queries and holds meta-information about the catalogs.

        This is a table that holds useful information such as
        the list of default columns per catalog, the reasonable default
        search radius per table that is appropriate for a mission etc.
        Instead of making a server call for each catalog for that type information,
        we do a single one and then post-process the resulting table.

        These are not meant to be used directly by the user.
        """
        if self._meta_info is None:
            query = (
                "SELECT split_part(name, '.', 1) AS table, "
                "split_part(name, '.', 2) AS par, "
                "CAST(value AS DECIMAL) AS value "
                "FROM metainfo "
                "WHERE (type = 'parameter' and relation = 'order') "
                "OR relation LIKE 'defaultSearchRadius' "
                "ORDER BY value"
            )
            self._meta_info = self.query_tap(query).to_table()
            self._meta_info['value'] = np.array(
                self._meta_info['value'], np.float32)
            self._meta_info = self._meta_info[self._meta_info['value'] > 0]
        return self._meta_info

    def _get_default_columns(self, catalog_name):
        """Get a list of default columns for a catalog

        Parameters
        ----------
        catalog_name : str
            The name of catalog as a str

        Return
        ------
        a list of column names

        """
        meta = self._meta[
            (self._meta['table'] == catalog_name)
            & (self._meta['par'] != '')
        ]
        meta.sort('value')
        defaults = meta['par']
        return list(defaults)

    def get_default_radius(self, catalog_name):
        """Get a mission-appropriate default radius for a catalog

        Parameters
        ----------
        catalog_name : str
            The name of catalog as a str

        Returns
        -------
        The radius as `~astropy.units.Quantity`

        """
        meta = self._meta[
            (self._meta['table'] == catalog_name)
            & (self._meta['par'] == '')
        ]
        radius = np.float32(meta['value'][0]) * u.arcmin
        return radius

    def _set_session(self, session):
        """Set requests.Session to use when querying the data

        Parameters
        ----------
        session : `~requests.Session`
            The requests.Session to use

        """
        if not isinstance(session, requests.Session):
            raise ValueError('session is not a `~requests.Session` instance')

        self._session = session

    def list_catalogs(self, *, master=False, keywords=None):
        """Return a table of all available catalogs with two columns
        (name, description)

        Parameters
        ----------
        master : bool
            Select only master catalogs. Default is False
        keywords : str or list
            a str or a list of str of keywords used as search
            terms for catalogs. Words with a str separated by a space
            are AND'ed, while words in a list are OR'ed

        Returns
        -------
        `~astropy.table.Table` with columns: name, description

        """
        if keywords is not None:
            if not isinstance(keywords, list):
                keywords = [keywords]
            if not all([isinstance(wrd, str) for wrd in keywords]):
                raise ValueError('non-str found in keywords elements')

        # use 'mast' to include both 'master' and 'mastr'
        names, desc = [], []
        for lab, tab in self.tap.tables.items():
            if 'TAP' in lab or (master and 'mast' not in lab):
                continue
            if keywords is not None:
                matched = any(
                    [
                        all([wrd.lower() in f'{lab} {tab.description}'.lower()
                            for wrd in wrds.split()])
                        for wrds in keywords
                    ]
                )
                if not matched:
                    continue
            names.append(lab)
            desc.append(tab.description)
        return Table({'name': names, 'description': desc})

    @deprecated(
        since='0.4.8',
        alternative='list_catalogs',
    )
    def query_mission_list(self, *, cache=True, get_query_payload=False):
        """Returns a list of all available mission catalogs with descriptions.

        This method is deprecated, and is included only for limited
        backward compatibility with the old astroquery.Heasarc that uses
        the Browse interface. Please use `list_catalogs` instead.

        """
        return self.list_catalogs(master=False)

    def list_columns(self, catalog_name, full=False):
        """Return the columns available in catalog_name as a table

        Parameters
        ----------
        catalog_name : str
            The name of catalog as a str
        full : bool
            If True, return all columns, otherwise, return the standard list
            of columns

        Returns
        -------
        result : `~astropy.table.Table`
            A table with columns: name, description, unit

        """
        tables = self.tap.tables
        if catalog_name not in tables.keys():
            msg = (f'{catalog_name} is not available as a public catalog. '
                   'Try passing keywords to `~Heasarc.list_catalogs` to find '
                   'the catalog name')
            raise ValueError(msg)

        default_cols = self._get_default_columns(catalog_name)

        names, desc, unit = [], [], []
        for col in tables[catalog_name].columns:
            if full or col.name in default_cols:
                names.append(col.name)
                desc.append(col.description)
                unit.append(col.unit or '')
        cols = Table({'name': names, 'description': desc, 'unit': unit})

        return cols

    @deprecated(
        since='0.4.8',
        alternative='list_columns',
    )
    def query_mission_cols(self, mission, *, cache=True,
                           get_query_payload=False, **kwargs):
        """Query around a specific object within a given mission catalog

        NOTE: This method is deprecated, and is included only for limited
        backward compatibility with the old astroquery.Heasarc that uses
        the Browse interface. Please use `list_columns` instead.

        Parameters
        ----------
        mission : str
            Mission catalog (short name) to search from
        fields : str, optional
            Return format for columns from the server available options:
            * Standard      : Return default catalog columns
            * All (default) : Return all catalog columns
            * <custom>      : User defined csv list of columns to be returned
        cache : bool, optional
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.
        All other parameters have no effect

        """
        fields = kwargs.get('fields', 'All')
        full = fields != 'Standard'
        cols = self.list_columns(mission, full=full)
        cols = [col.upper() for col in cols['name'] if '__' not in col]
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
        self._saved_query = query
        return self.tap.search(query, language='ADQL', maxrec=maxrec)

    @deprecated_renamed_argument(
        ('mission', 'fields', 'resultmax', 'entry', 'coordsys', 'equinox',
         'displaymode', 'action', 'sortvar', 'cache'),
        ('catalog', 'columns', 'maxrec', None, None, None,
         None, None, None, None),
        since=['0.4.8']*10,
        arg_in_kwargs=(False, True, True, True, True, True,
                       True, True, True, False)
    )
    def query_region(self, position=None, catalog=None, radius=None, *,
                     spatial='cone', width=None, polygon=None, add_offset=False,
                     get_query_payload=False, columns=None, cache=False,
                     verbose=False, maxrec=None,
                     **kwargs):
        """Queries the HEASARC TAP server around a coordinate and returns a
        `~astropy.table.Table` object.

        Parameters
        ----------
        position : str, `astropy.coordinates` object
            Gives the position of the center of the cone or box if performing
            a cone or box search. Required if spatial is ``'cone'`` or
            ``'box'``. Ignored if spatial is ``'polygon'`` or ``'all-sky'``.
        catalog : str
            The catalog to query. To list the available catalogs, use
            :meth:`~astroquery.heasarc.HeasarcClass.list_catalogs`.
        spatial : str
            Type of spatial query: ``'cone'``, ``'box'``, ``'polygon'``, and
            ``'all-sky'``. Defaults to ``'cone'``.
        radius : str or `~astropy.units.Quantity` object, [optional for
            spatial == ``'cone'``].
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. If None, a default value
            appropriate for the selected catalog is used. To see the default
            radius for the catalog, see
            `get_default_radius`.
        width : str, `~astropy.units.Quantity` object [Required for
            spatial == ``'box'``.]
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `astropy.units`
            may also be used.
        polygon : list, [Required for spatial is ``'polygon'``]
            A list of ``(ra, dec)`` pairs (as tuples), in decimal degrees,
            outlining the polygon to search in. It can also be a list of
            `astropy.coordinates` object or strings that can be parsed by
            `astropy.coordinates.ICRS`.
        add_offset: bool
            If True and spatial=='cone', add a search_offset column that
            indicates the separation (in arcmin) between the requested
            coordinate and the entry coordinates in the catalog. Default is False.
        get_query_payload : bool, optional
            If `True` then returns the generated ADQL query as str.
            Defaults to `False`.
        columns : str, optional
            Target column list with value separated by a comma(,).
            Use * for all the columns. The default is to return a subset
            of the columns that are generally the most useful.
        verbose : bool, optional
            If False, suppress vo warnings.
        maxrec : int, optional
            Maximum number of records


        Returns
        -------
        table : A `~astropy.table.Table` object.
        """
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()

        if catalog is None:
            raise InvalidQueryError("catalog name is required! Use 'xray' "
                                    "to search the master X-ray catalog")

        if columns is None:
            columns = ', '.join(self._get_default_columns(catalog))
            if '__row' not in columns:
                columns += ',__row'

        if spatial.lower() == 'all-sky':
            where = ''
        elif spatial.lower() == 'polygon':
            try:
                coords_list = [parse_coordinates(coord).icrs
                               for coord in polygon]
            except TypeError:
                try:
                    coords_list = [coordinates.SkyCoord(*coord).icrs
                                   for coord in polygon]
                except u.UnitTypeError:
                    warnings.warn("Polygon endpoints are being interpreted as "
                                  "RA/Dec pairs specified in decimal degree "
                                  "units.")
                    coords_list = [
                        coordinates.SkyCoord(*coord, unit='deg').icrs
                        for coord in polygon
                    ]

            coords_str = [f'{coord.ra.deg},{coord.dec.deg}'
                          for coord in coords_list]
            where = (" WHERE CONTAINS(POINT('ICRS',ra,dec),"
                     f"POLYGON('ICRS',{','.join(coords_str)}))=1")
        else:
            coords_icrs = parse_coordinates(position).icrs
            ra, dec = coords_icrs.ra.deg, coords_icrs.dec.deg

            if spatial.lower() == 'cone':
                if radius is None:
                    radius = self.get_default_radius(catalog)
                elif isinstance(radius, str):
                    radius = coordinates.Angle(radius)
                where = (" WHERE CONTAINS(POINT('ICRS',ra,dec),CIRCLE("
                         f"'ICRS',{ra},{dec},{radius.to(u.deg).value}))=1")
                # add search_offset for the case of cone
                if add_offset:
                    columns += (",DISTANCE(POINT('ICRS',ra,dec), "
                                f"POINT('ICRS',{ra},{dec})) as search_offset")
            elif spatial.lower() == 'box':
                if isinstance(width, str):
                    width = coordinates.Angle(width)
                where = (" WHERE CONTAINS(POINT('ICRS',ra,dec),"
                         f"BOX('ICRS',{ra},{dec},{width.to(u.deg).value},"
                         f"{width.to(u.deg).value}))=1")
            else:
                raise ValueError("Unrecognized spatial query type. Must be one"
                                 " of 'cone', 'box', 'polygon', or 'all-sky'.")

        adql = f'SELECT {columns} FROM {catalog}{where}'

        if get_query_payload:
            return adql
        response = self.query_tap(query=adql, maxrec=maxrec)

        # save the response in case we want to use it later
        self._last_result = response
        self._last_catalog_name = catalog

        table = response.to_table()
        if add_offset:
            table['search_offset'].unit = u.arcmin
        if len(table) == 0:
            warnings.warn(
                NoResultsWarning("No matching rows were found in the query.")
            )
        return table

    @deprecated(
        since='0.4.8',
        alternative='query_region'
    )
    def query_object(self, object_name, mission, *,
                     cache=True, get_query_payload=False,
                     **kwargs):
        """Query around a specific object within a given mission catalog

        Parameters
        ----------
        object_name : str
            Object to query around. To set search radius use the 'radius'
            parameter.
        mission : str
            Mission catalog to search from
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.
        **kwargs :
            see `~astroquery.heasarc.HeasarcClass._args_to_payload` for list
            of additional parameters that can be used to refine search query.

        """
        pos = coordinates.SkyCoord.from_name(object_name)
        return self.query_region(pos, catalog=mission, spatial='cone',
                                 get_query_payload=get_query_payload)

    def locate_data(self, query_result=None, catalog_name=None):
        """Get links to data products
        Use vo/datalinks to query the data products for some query_results.

        Parameters
        ----------
        query_result : `astropy.table.Table`, optional
            A table that contain the search results. Typically as
            returned by query_region. If None, use the table from the
            most recent query_region call.
        catalog_name : str
            The catalog name for the which the query_result belongs to.
            If None, use the one from the most recent query_region call.

        Returns
        -------
        table : A `~astropy.table.Table` object.
        """
        if query_result is None:
            if (
                not hasattr(self, '_last_result')
                or self._last_result is None
            ):
                raise ValueError('query_result is None, and none '
                                 'found from a previous search')
            else:
                query_result = self._last_result

        if not isinstance(query_result, Table):
            raise TypeError('query_result need to be an astropy.table.Table')

        # make sure we have a column __row
        if '__row' not in query_result.colnames:
            raise ValueError('No __row column found in query_result. '
                             'query_result needs to be the output of '
                             'query_region or a subset.')

        if catalog_name is None:
            catalog_name = self._last_catalog_name
        if not (
            isinstance(catalog_name, str)
            and catalog_name in self.tap.tables.keys()
        ):
            raise ValueError(f'Unknown catalog name: {catalog_name}')

        # datalink url
        dlink_url = f'{self.VO_URL}/datalink/{catalog_name}'

        query = pyvo.dal.adhoc.DatalinkQuery(
            baseurl=dlink_url,
            id=query_result['__row'],
            session=self._session
        )
        dl_result = query.execute().to_table()
        dl_result = dl_result[dl_result['content_type'] == 'directory']
        dl_result = dl_result[['ID', 'access_url', 'content_length']]

        # add sciserver and s3 columns
        newcol = [
            f"/FTP/{row.split('FTP/')[1]}".replace('//', '/')
            if 'FTP' in row else ''
            for row in dl_result['access_url']
        ]
        dl_result.add_column(newcol, name='sciserver', index=2)
        newcol = [f"s3://{self.S3_BUCKET}/{row[5:]}" if row != '' else ''
                  for row in dl_result['sciserver']]
        dl_result.add_column(newcol, name='aws', index=3)

        return dl_result

    def enable_cloud(self, provider='aws', profile=None):
        """
        Enable downloading public files from the cloud.
        Requires the boto3 library to function.

        Parameters
        ----------
        provider : str
            Which cloud data provider to use. Currently, only 'aws' is
            supported.
        profile : str
            Profile to use to identify yourself to the cloud provider
            (usually in ~/.aws/config).
        """

        try:
            import boto3
            import botocore
        except ImportError:
            raise ImportError(
                'The cloud feature requires the boto3 package. '
                'Install it first.'
            )

        if profile is None:
            log.info('Enabling anonymous cloud data access ...')
            config = botocore.client.Config(
                signature_version=botocore.UNSIGNED)
            self.s3_resource = boto3.resource('s3', config=config)

        elif isinstance(profile, bool) and not profile:
            # profile is False, use system env credentials
            self.s3_resource = boto3.resource('s3')

        else:
            log.info(f'Enabling cloud data access with profile: {profile} ...')
            session = boto3.session.Session(profile_name=profile)
            self.s3_resource = session.resource(service_name='s3')

        self.s3_client = self.s3_resource.meta.client

    def download_data(self, links, host='heasarc', location='.'):
        """Download data products in links with a choice of getting the
        data from either the heasarc server, sciserver, or the cloud in AWS.


        Parameters
        ----------
        links : `astropy.table.Table`
            The result from locate_data
        host : str
            The data host. The options are: heasarc (default), sciserver, aws.
            If host == 'sciserver', data is copied from the local mounted
            data drive.
            If host == 'aws', data is downloaded from Amazon S3 Open
            Data Repository.
        location : str
            local folder where the downloaded file will be saved.
            Default is current working directory

        Note that ff you are downloading large datasets (more 10 10GB),
        from the main heasarc server, it is recommended that you split
        it up, so that if the downloaded is interrupted, you do not need
        to start again.
        """

        if len(links) == 0:
            raise ValueError('Input links table is empty')

        if host not in ['heasarc', 'sciserver', 'aws']:
            raise ValueError('host has to be one of heasarc, sciserver, aws')

        host_column = 'access_url' if host == 'heasarc' else host
        if host_column not in links.colnames:
            raise ValueError(
                f'No {host_column} column found in the table. Call '
                '`~locate_data` first'
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
        Users should be using `~self.download_data` instead

        Parameters
        ----------
        links : `astropy.table.Table`
            The result from locate_data
        location : str
            local folder where the downloaded file will be saved.
            Default is current working directory

        """
        # The limit comes from the size of the string in the POST request
        if 'content_length' in links.columns:
            size = links['content_length'].sum() / 2**30
            if size > 10:
                warnings.warn(
                    f"The size of the requested file is large {size:.3f} GB. "
                    "If the download is interrupted, you may need to start "
                    "again. Consider downloading the data in chunks."
                )

        file_list = [f"/FTP/{link.split('FTP/')[1]}"
                     for link in links['access_url']]
        params = {
            'files': f'>{"&&>".join(file_list)}&&',
            'filter': ''
        }

        # get local_filepath name
        local_filepath = f'{location}/heasarc-data.tar'
        iname = 1
        while os.path.exists(local_filepath):
            local_filepath = f'{location}/heasarc-data.{iname}.tar'
            iname += 1

        log.info(f'Downloading to {local_filepath} ...')
        self._download_file(self.TAR_URL, local_filepath,
                            timeout=self.timeout,
                            continuation=False, cache=False, method="POST",
                            head_safe=False, data=params, verbose=False)

        # if all good and we have a tar file untar it
        if tarfile.is_tarfile(local_filepath):
            log.info(f'Untar {local_filepath} to {location} ...')
            tfile = tarfile.TarFile(local_filepath)
            tfile.extractall(path=location, filter="fully_trusted")
            tfile.close()
            os.remove(local_filepath)
        else:
            raise ValueError(
                'An error occurred when downloading the data. Retry again.'
            )

    def _copy_sciserver(self, links, location='.'):
        """Copy data from the local archive on sciserver

        Do not call directly.
        Users should be using `~self.download_data` instead

        """
        if not os.path.exists('/FTP/'):
            raise FileNotFoundError(
                'No data archive found. This should be run on Sciserver '
                'with the data drive mounted.'
            )

        # make sure the output folder exits
        os.makedirs(location, exist_ok=True)

        for link in links['sciserver']:
            link = str(link)
            log.info(f'Copying to {link} from the data drive ...')
            if not os.path.exists(link):
                raise ValueError(
                    f'No data found in {link}. '
                    'Make sure you are running this on Sciserver. '
                    'If you think data is missing, please contact the '
                    'Heasarc Help desk'
                )
            if os.path.isdir(link):
                download_dir = os.path.basename(link.strip('/'))
                shutil.copytree(link, f'{location}/{download_dir}')
            else:
                shutil.copy(link, location)

    def _download_s3(self, links, location='.'):
        """Download data from AWS S3
        Assuming open access.

        Do not call directly.
        Users should be using `~self.download_data` instead

        """
        keys_list = [link for link in links['aws']]
        if not hasattr(self, 's3_resource'):
            # all the data is public for now; no profile is needed
            self.enable_cloud(provider='aws', profile=None)

        def _s3_tree_download(client, bucket_name, path, local):
            """Download nested keys from s3"""
            response = client.list_objects_v2(Bucket=bucket_name, Prefix=path)
            content = response.get('Contents', [])
            for obj in content:
                key = obj['Key']
                path2 = '/'.join(path.strip('/').split('/')[:-1])
                dest = os.path.join(local, key[len(path2)+1:])
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                client.download_file(bucket_name, key, dest)

        # loop through the requested links
        for key in keys_list:
            log.info(f'downloading {key}')
            path = key.replace(f's3://{self.S3_BUCKET}/', '')
            _s3_tree_download(self.s3_client, self.S3_BUCKET, path, location)


Heasarc = HeasarcClass()
