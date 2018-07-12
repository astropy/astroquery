# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst

from ..query import BaseQuery
from ..utils import commons
from ..utils import async_to_sync

from . import conf

from .output_format import OutputFormat
from .properties_constraint import PropertiesConstraint

import os
from astropy import units as u

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
    Query the `CDS MOC Service`_

    The `CDS MOC Service`_ allows the user to retrieve all the data sets (with their
    meta datas) having sources in a specific region. This region can be a `regions.CircleSkyRegion`, a
    `regions.PolygonSkyRegion` or a `mocpy.moc.MOC` object.

    This astroquery module implements two methods:

    * A :meth:`~astroquery.cds.CdsClass.query_region` method allowing the user to retrieve the data sets having at least
      one source in a specific region.
    * A :meth:`~astroquery.cds.CdsClass.query_object` method allowing the user to search for data sets having a specific
      set of meta datas.

    Examples
    --------

    :ref:`This example <query_cone_search>` query the `CDS MOC Service`_ with
    :meth:`~astroquery.cds.CdsClass.query_region`.
    :ref:`This one <query_on_meta_data>` query the `CDS MOC Service`_ with
    :meth:`~astroquery.cds.CdsClass.query_object`.

    .. _CDS MOC Service:
        http://alasky.unistra.fr/MocServer/query
    """
    URL = conf.server
    TIMEOUT = conf.timeout

    def __init__(self):
        super(CdsClass, self).__init__()
        self.path_moc_file = None

    def query_region(self, region=None, get_query_payload=False, verbose=False, **kwargs):
        """
        Query the `CDS MOC Service`_ with a region.

        Parameters
        ----------
        region : ``regions.CircleSkyRegion``/``regions.PolygonSkyRegion``/``mocpy.moc.MOC``
            The region in which we want the CDS datasets to have at least one source.
            Can be one of the following types:

            * ``regions.CircleSkyRegion`` : defines an astropy cone region.
            * ``cds.RegionType.Polygon`` : defines an astropy polygon region.
            * ``mocpy.moc.MOC`` : defines a MOC from the MOCPy library. See the `MOCPy's documentation
            <https://mocpy.readthedocs.io/en/latest/>`__ for how instantiating a MOC object.

        get_query_payload : bool, optional
            If True, returns a dictionary of the query payload instead of the parsed http response.
        verbose : bool, optional
        intersect : str, optional
            This parameter can take only three different values:

            - ``overlaps`` (default). The matching data sets are those overlapping the MOC region.
            - ``covers``. The matching data sets are those covering the MOC region.
            - ``encloses``. The matching data sets are those enclosing the MOC region.
        max_rec : int, optional
            Maximum number of data sets to return. By default, there is no upper limit i.e. all the matching data sets
            are returned.
        TODO : should return all the records by default. The return of only ids is redondant with meta_var=['ID'] so
        TODO : should be removed. number of dataset is easy to get in python afterwards so should be removed to.
        TODO : mocpy.moc.MOC object is good to have. So just put a bool arg : moc_return. If true returns a mocpy MOC
        TODO : object, otherwise returns an astropy.table containing all the meta datas by default or only those
        TODO : specified in meta_var.
        output_format : ``astroquery.cds.ReturnFormat``
            Format of the `CDS MOC service`_'s response that will be given to the user.
            The possible ``output_format`` values and their effects on the response are :

            -  ``cds.ReturnFormat.id`` (default). The output is a ID list of the matching
               data sets
            -  ``cds.ReturnFormat.record``. The output is a dictionary of
               :class:`astroquery.cds.Dataset <astroquery.cds.Dataset>` objects indexed by their ID
            -  ``cds.ReturnFormat.number``. :meth:`~astroquery.cds.CdsClass.query_region` returns the number of
               matched data sets
            -  ``cds.ReturnFormat.moc``. The output is a ``mocpy.MOC`` object corresponding
               to the union of the MOCs of the selected data sets
            -  ``cds.ReturnFormat.i_moc``. The output is a ``mocpy.MOC`` object
               corresponding to the intersection of the MOCs of the selected data
               sets
        case_sensitive : bool, optional
        meta_var : [str], optional
            List of the meta data that the user wants to retrieve, e.g. ['ID', 'moc_sky_fraction'].
            Only if ``output_format`` is set to ``cds.ReturnFormat.record``.
        TODO : move the filtering on meta datas in query_object (astroquery.cds' objects are datasets).
        meta_data : str
            Algebraic expression on meta_var for filtering data sets.
            See this :ref:`example <query_on_meta_data>`

        Returns
        -------
        result : depends on the value of ``output_format``. See its definition
            The parsed HTTP response emitted from the `CDS MOC Service`_.

        Examples
        --------
        :ref:`query_cone_search`

        :ref:`query_on_meta_data`
        """
        response = self.query_region_async(region, get_query_payload, **kwargs)
        if get_query_payload:
            return response

        result = self._parse_result(response, verbose)

        return result

    def query_region_async(self, region, get_query_payload, **kwargs):
        """
        Performs the `CDS MOC Service`_ query.

        Parameters
        ----------
        region : ``regions.CircleSkyRegion``/``regions.PolygonSkyRegion``/``mocpy.moc.MOC``
            The region on which the MOCServer will be queried.
        get_query_payload : bool
            If True, returns a dictionary in the form of a dictionary.
        **kwargs
             Arbitrary keyword arguments.

        Returns
        -------
        response : `~requests.Response`:
            The HTTP response from the `CDS MOC Service`_
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
            # The user ask for querying on a ``
            with open(self.path_moc_file, 'rb') as f:
                params_d.update({'files': {'moc': f.read()}})
                response = self._request(**params_d)

        return response

    def _args_to_payload(self, **kwargs):
        """
        Convert ``kwargs`` keyword arguments to a dictionary of payload.

        Parameters
        ----------
        kwargs
            Arbitrary keyword arguments. The same as those defined in the docstring of
            :meth:`~astroquery.cds.CdsClass.query_object`.

        Returns
        -------
        request_payload : dict{str : str}
            The payloads submitted to the `CDS MOC service`_
        """
        request_payload = dict()
        intersect = kwargs.get('intersect', 'overlaps')
        if intersect == 'encloses':
            intersect = 'enclosed'

        request_payload.update({'intersect': intersect})
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
            meta_data_constrain = PropertiesConstraint(kwargs['meta_data'])
            request_payload.update(meta_data_constrain.request_payload)

        # Output format payload
        from sys import maxsize
        self.output_format = OutputFormat(output_format=kwargs.get('output_format', cds.ReturnFormat.id),
                                          field_l=kwargs.get('meta_var', list()),
                                          moc_order=kwargs.get('moc_order', maxsize),
                                          case_sensitive=kwargs.get('case_sensitive', True),
                                          max_rec=kwargs.get('max_rec', None))
        request_payload.update(self.output_format.request_payload)

        return request_payload

    def _parse_result(self, response, verbose=False):
        """
        Parsing of the ``response`` following :param:`output_format`.

        Parameters
        ----------
        response : `~requests.Response`
            The HTTP response from the `CDS MOC service`_.
        verbose : bool, optional
            False by default.
        Returns
        -------
        result : depends on :param:`output_format`
            The result that is returned by the :meth:`~astroquery.cds.CdsClass.query_region` method
        """
        if not verbose:
            commons.suppress_vo_warnings()

        json_result = response.json()
        if self.output_format.format is cds.ReturnFormat.record:
            from .dataset import Dataset

            # The user will get a dictionary of Dataset objects indexed by their ID names.
            # The http response is a list of dict. Each dict represents one data set. Each dict is a list
            # of (meta-data name, value in str)

            # 1 : all the meta-data values from the data sets returned by the CDS are cast to floats if possible
            result = [dict([md_name, CdsClass._cast_to_float(md_val)]
                           for md_name, md_val in data_set.items())
                      for data_set in json_result]
            # 2 : a final dictionary of Dataset objects indexed by their ID names is created
            result_tmp = {}
            for data_set in result:
                data_set_id = data_set['ID']
                result_tmp[data_set_id] = Dataset(
                    **dict([md_name, CdsClass._remove_duplicate(data_set.get(md_name))]
                           for md_name in (data_set.keys() - set('ID')))
                )

            result = result_tmp
        elif self.output_format.format is cds.ReturnFormat.number:
            # The user will get the number of matching data sets
            result = int(json_result['number'])
        elif self.output_format.format is cds.ReturnFormat.moc or \
                self.output_format.format is cds.ReturnFormat.i_moc:
            # The user will get a mocpy.MOC object that he can manipulate through the
            # mocpy API https://github.com/cds-astro/mocpy
            empty_order_removed_d = {}
            for order, ipix_l in json_result.items():
                if len(ipix_l) > 0:
                    empty_order_removed_d.update({order: ipix_l})

            result = MOC.from_json(empty_order_removed_d)
        else:
            # The user will get a list of the matched data sets ID names
            result = json_result

        return result

    @staticmethod
    def _cast_to_float(value):
        """
        Cast ``value`` to a float if possible

        Parameters
        ----------
        value : str
            string to cast

        Returns
        -------
        value : float
            If castable
        value : str
            The original passed string value if not castable
        """
        try:
            return float(value)
        except (ValueError, TypeError):
            return value

    @staticmethod
    def _remove_duplicate(value_l):
        """
        Remove doubles in a list

        Parameters
        ----------
        value_l : list
            input list to remove doubles

        Returns
        -------
        value_l : list
            list with no doubles
        """
        if isinstance(value_l, list):
            value_l = list(set(value_l))
            if len(value_l) == 1:
                return value_l[0]

        return value_l

    class ReturnFormat:
        """
        Output format enumeration for :meth:`~astroquery.cds.CdsClass.query_region`
        """
        id = 1
        record = 2
        number = 3
        moc = 4
        i_moc = 5
        return_format_size = 6

    class ServiceType:
        """
        Service type enumeration for :meth:`~astroquery.cds.Dataset.search`
        """
        cs = 'cs'
        tap = 'tap'
        ssa = 'ssa'
        sia = 'sia'


cds = CdsClass()
