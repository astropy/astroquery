# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst

from ..query import BaseQuery
from ..utils import commons
from ..utils import async_to_sync

from . import conf

import os
from astropy import units as u
from astropy.table import Table
from copy import copy

try:
    from mocpy import MOC
except ImportError:
    raise ImportError("Could not import mocpy, which is a requirement for the CDS service."
                      "Please refer to https://mocpy.readthedocs.io/en/latest/install.html for how to install it.")

try:
    from regions import CircleSkyRegion, PolygonSkyRegion
except ImportError:
    raise ImportError("Could not import astropy-regions, which is a requirement for the CDS service."
                      "Please refer to http://astropy-regions.readthedocs.io/en/latest/installation.html for how to"
                      "install it.")

__all__ = ['cds', 'CdsClass']


@async_to_sync
class CdsClass(BaseQuery):
    """
    Query the `CDS MOCServer <http://alasky.unistra.fr/MocServer/query>`_

    The `CDS MOCServer <http://alasky.unistra.fr/MocServer/query>`_ allows the user to retrieve all the data sets (with
    their meta-datas) having sources in a specific region. This region can be a `regions.CircleSkyRegion`, a
    `regions.PolygonSkyRegion` or a `mocpy.MOC` object.

    This astroquery module implements a unique method:

    * A :meth:`~astroquery.cds.CdsClass.query_region` method allowing the user to retrieve the data sets having at least
      one source in a specific region.

    """
    URL = conf.server
    TIMEOUT = conf.timeout

    def __init__(self):
        super(CdsClass, self).__init__()
        self.path_moc_file = None
        self.return_moc = False

    def query_region(self, region=None, get_query_payload=False, verbose=False, **kwargs):
        """
        Query the `CDS MOCServer <http://alasky.unistra.fr/MocServer/query>`_ with a region. Returns the data-sets
        having at least one source in the region.

        Parameters
        ----------
        region : `regions.CircleSkyRegion`, `regions.PolygonSkyRegion` or `mocpy.MOC`
            The region to query the MOCServer with.
            Can be one of the following types:

            * ``regions.CircleSkyRegion`` : defines an astropy cone region.
            * ``regions.PolygonSkyRegion`` : defines an astropy polygon region.
            * ``mocpy.moc.MOC`` : defines a MOC from the MOCPy library. See the `MOCPy's documentation
              <https://mocpy.readthedocs.io/en/latest/>`__ for how to instantiate a MOC object.

        intersect : str, optional
            This parameter can take only three different values:

            - ``overlaps`` (default). Returned data-sets are those overlapping the MOC region.
            - ``covers``. Returned data-sets are those covering the MOC region.
            - ``encloses``. Returned data-sets are those enclosing the MOC region.
        max_rec : int, optional
            Maximum number of data-sets to return. By default, there is no upper limit.
        return_moc : bool, optional
            Specifies if we want a `mocpy.MOC` object in return. This MOC corresponds to the union of the MOCs of all
            the matching datasets. By default it is set to False and :meth:`~astroquery.cds.CdsClass.query_region`
            returns an `astropy.table.Table` object.
        max_norder : int, optional
            Has sense only if ``return_moc`` is set to True. Specifies the maximum precision order of the returned MOC.
        fields : [str], optional
            Has sense only if ``return_moc`` is set to False. Specifies which meta datas to retrieve. The returned
            `astropy.table.Table` table will only contain the column names given in ``fields``.

            Specifying the fields we want to retrieve allows the request to be faster because of the reduced chunk of
            data moving from the MOCServer to the client.

            Some meta-datas as ``obs_collection`` or ``data_ucd`` do not keep a constant type throughout all the
            MOCServer's data-sets and this lead to problems because `astropy.table.Table` supposes a column to have an
            unique type. When we encounter this problem for a specific meta-data, we remove its corresponding column
            from the returned astropy table.
        meta_data : str, optional
            Algebraic expression on meta-datas for filtering the data-sets at the server side.
        get_query_payload : bool, optional
            If True, returns a dictionary of the query payload instead of the parsed response.
        verbose : bool, optional

        Returns
        -------
        response : `astropy.table.Table` or `mocpy.MOC`
            By default an astropy table of the data-sets matching the query. If ``return_moc`` is set to True, it gives
            a MOC object corresponding to the union of the MOCs from all the matched data-sets.
        """
        response = self.query_region_async(region, get_query_payload, **kwargs)
        if get_query_payload:
            return response

        result = self._parse_result(response, verbose)

        return result

    def query_region_async(self, region, get_query_payload, **kwargs):
        """
        Performs the `CDS MOCServer <http://alasky.unistra.fr/MocServer/query>`_ query.

        Parameters
        ----------
        region : `regions.CircleSkyRegion`, `regions.PolygonSkyRegion` or `mocpy.MOC`
            The region to query the MOCServer with.
        get_query_payload : bool
            If True, returns a dictionary of the query payload instead of the parsed response.
        **kwargs
             Arbitrary keyword arguments.

        Returns
        -------
        response : `~requests.Response`:
            The HTTP response from the `CDS MOCServer <http://alasky.unistra.fr/MocServer/query>`_.
        """
        request_payload = self._args_to_payload(region=region, **kwargs)
        if get_query_payload:
            return request_payload

        params_d = {
            'method': 'GET',
            'url': self.URL,
            'timeout': self.TIMEOUT,
            'data': kwargs.get('data', None),
            'cache': False,
            'params': request_payload,
        }

        if not self.path_moc_file:
            response = self._request(**params_d)
        else:
            # The user ask for querying on a MOC region.
            with open(self.path_moc_file, 'rb') as f:
                params_d.update({'files': {'moc': f.read()}})
                response = self._request(**params_d)

        return response

    def _args_to_payload(self, **kwargs):
        """
        Convert the keyword arguments to a payload.

        Parameters
        ----------
        kwargs
            Arbitrary keyword arguments. The same as those defined in the docstring of
            :meth:`~astroquery.cds.CdsClass.query_object`.

        Returns
        -------
        request_payload : dict
            The payload submitted to the MOCServer.
        """
        request_payload = dict()
        intersect = kwargs.get('intersect', 'overlaps')
        if intersect == 'encloses':
            intersect = 'enclosed'

        request_payload.update({'intersect': intersect,
                                'casesensitive': 'true',
                                'fmt': 'json',
                                'get': 'record',
                                })

        self.return_moc = kwargs.get('return_moc', False)
        # Region Type
        region = kwargs['region']
        if isinstance(region, MOC):
            self.path_moc_file = os.path.join(os.getcwd(), 'moc.fits')
            region.write(format='fits', write_to_file=True, path=self.path_moc_file)
            # add the moc region payload to the request payload
        elif isinstance(region, CircleSkyRegion):
            # add the cone region payload to the request payload
            request_payload.update({
                'DEC': str(region.center.dec.to(u.deg).value),
                'RA': str(region.center.ra.to(u.deg).value),
                'SR': str(region.radius.to(u.deg).value),
            })
        elif isinstance(region, PolygonSkyRegion):
            # add the polygon region payload to the request payload
            polygon_payload = "Polygon"
            vertices = region.vertices
            for i in range(len(vertices.ra)):
                polygon_payload += ' ' + str(vertices.ra[i].to(u.deg).value) + \
                                   ' ' + str(vertices.dec[i].to(u.deg).value)
                request_payload.update({'stc': polygon_payload})
        else:
            if region is not None:
                raise ValueError('`region` belongs to none of the following types: `regions.CircleSkyRegion`,'
                                 '`regions.PolygonSkyRegion` or `mocpy.MOC`')

        if 'meta_data' in kwargs:
            request_payload.update({'expr': kwargs['meta_data']})

        if 'fields' in kwargs:
            fields = kwargs['fields']
            field_l = list(fields) if not isinstance(fields, list) else copy(fields)
            # The CDS MOC service responds badly to record queries which do not ask
            # for the ID field. To prevent that, we add it to the list of requested fields
            field_l.append('ID')
            field_l = list(set(field_l))
            fields_str = str(field_l[0])
            for field in field_l[1:]:
                fields_str += ', '
                fields_str += field

            request_payload.update({"fields": fields_str})

        if 'max_rec' in kwargs:
            max_rec = kwargs['max_rec']
            request_payload.update({'MAXREC': str(max_rec)})

        if self.return_moc:
            request_payload.update({'get': 'moc'})
            if 'max_norder' in kwargs:
                request_payload.update({'order': kwargs['max_norder']})
            else:
                request_payload.update({'order': 'max'})

        return request_payload

    def _parse_result(self, response, verbose=False):
        """
        Parsing of the response returned by the MOCServer.

        Parameters
        ----------
        response : `~requests.Response`
            The HTTP response returned by the MOCServer.
        verbose : bool, optional
            False by default.

        Returns
        -------
        result : `astropy.table.Table` or `mocpy.MOC`
            By default an astropy table of the data-sets matching the query. If ``return_moc`` is set to True, it gives
            a MOC object corresponding to the union of the MOCs from all the matched data-sets.
        """
        if not verbose:
            commons.suppress_vo_warnings()

        result = response.json()

        if not self.return_moc:
            """
            The user will get `astropy.table.Table` object whose columns refer to the returned data-set meta-datas.
            """
            # cast the data-sets meta-datas values to their correct Python type.
            typed_result = []
            for d in result:
                typed_d = {k: self._cast_to_float(v) for k, v in d.items()}
                typed_result.append(typed_d)

            # looping over all the record's keys to find all the existing keys
            column_names_l = []
            for d in typed_result:
                column_names_l.extend(d.keys())

            # remove all the doubles
            column_names_l = list(set(column_names_l))
            # init a dict mapping all the meta-data's name to an empty list
            table_d = {key: [] for key in column_names_l}
            type_d = {key: None for key in column_names_l}
            mask_column_d = {key: True for key in column_names_l}

            # fill the dict with the value of each returned data-set one by one.
            for d in typed_result:
                row_table_d = {key: '-' for key in column_names_l}
                row_table_d.update(d)

                row_table_d = {k: _ for k, _ in row_table_d.items() if mask_column_d[k]}

                for k, v in row_table_d.items():
                    table_d[k].append(v)
                    current_type = type(v)
                    if type_d[k] and type_d[k] != current_type and current_type == list:
                        mask_column_d[k] = False
                    type_d[k] = current_type

            table_d = {k: _ for k, _ in table_d.items() if mask_column_d[k]}

            # return an `astropy.table.Table` object created from table_d
            return Table(table_d)

        """
        The user will get `mocpy.MOC` object.
        """
        # remove
        empty_order_removed_d = {}
        for order, ipix_l in result.items():
            if len(ipix_l) > 0:
                empty_order_removed_d.update({order: ipix_l})

        # return a `mocpy.MOC` object. See https://github.com/cds-astro/mocpy and the MOCPy's doc
        return MOC.from_json(empty_order_removed_d)

    @staticmethod
    def _cast_to_float(value):
        """
        Cast ``value`` to a float if possible.

        Parameters
        ----------
        value : str
            string to cast

        Returns
        -------
        value : float or str
            A float if it can be casted so otherwise the initial string.
        """
        try:
            return float(value)
        except (ValueError, TypeError):
            return value


cds = CdsClass()
