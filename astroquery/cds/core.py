#!/usr/bin/env python
# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst

from ..query import BaseQuery
from ..utils import commons
from ..utils import async_to_sync

from . import conf
from .dataset import Dataset

from .output_format import OutputFormat

from enum import Enum

__all__ = ['cds', 'CdsClass']


@async_to_sync
class CdsClass(BaseQuery):
    """
    Query the `CDS MOC Service`_

    The `CDS MOC Service`_ allows the user to retrieve all the data sets (and possibly their
    meta data) having observations in a specific region. This region can be a Cone
    a Polygon or a ``mocpy.MOC`` object. It is also possible to filter data sets along
    a constrained set of meta data.

    Examples
    --------

    :ref:`This example <query_cone_search>` explains a basic usage

    :ref:`This one <query_on_meta_data>` shows a more complex query involving filtering data sets
    with a set of meta data.

    .. _CDS MOC Service:
        http://alasky.unistra.fr/MocServer/query

    """

    URL = conf.server
    TIMEOUT = conf.timeout

    def query_region(self, region_type, get_query_payload=False, verbose=False, **kwargs):
        """
        Query the `CDS MOC Service`_ with a region

        Parameters
        ----------
        region_type : ``astroquery.cds.RegionType``
            The type of the region. Can take one of the following values:

            * ``cds.RegionType.Cone`` : the region is a cone
            * ``cds.RegionType.Polygon`` : the region is a polygon
            * ``cds.RegionType.Moc`` : the region is defined as MOC
            * ``cds.RegionType.AllSky`` : no region i.e. all the ~20000 data sets will be selected (useful
              for filtering data sets with a set of meta data. See ``meta_var`` parameter definition).

        get_query_payload : bool, optional
            If True, returns a dictionary of the query payload instead of the parsed http response
        verbose : bool, optional
        center : `astropy.coordinates.SkyCoord <astropy.coordinates.SkyCoord>`
            The center position of the cone region. Only if ``region_type`` is set to cds.RegionType.Cone
        radius : `astropy.coordinates.Angle <astropy.coordinates.Angle>`
            The radius of the cone region. Only if ``region_type`` is set to cds.RegionType.Cone
        vertices : [`astropy.coordinates.SkyCoord <astropy.coordinates.SkyCoord>`]
            The positions defining the polygon region. Only if ``region_type`` is set to cds.RegionType.Polygon
        filename : str
            The local path to a fits file describing the MOC. Only if ``region_type`` is set to
            cds.RegionType.Moc. This param is not compatible with ``url`` and ``moc``.
        url : str
            An url to a fits file describing the MOC. Only if ``region_type`` is set to
            cds.RegionType.Moc. This param is not compatible with ``filename`` and ``moc``.
        moc : mocpy.MOC class
            The mocpy.MOC object defining the MOC region. Only if ``region_type`` is set to
            cds.RegionType.Moc. This param is not compatible with ``filename`` and ``url``.
        intersect : str, optional
            This parameter can take only three different values:

            - ``overlaps`` (default). The matching data sets are those overlapping the MOC region.
            - ``covers``. The matching data sets are those covering the MOC region.
            - ``enclosed``. The matching data sets are those enclosing the MOC region.
        max_rec : int, optional
            Maximum number of data sets to return. By default, there is no upper limit i.e. all the matching data sets
            are returned.
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
            See this :ref:`example <query_on_meta_data>`
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

        response = self.query_region_async(region_type, get_query_payload, **kwargs)
        if get_query_payload:
            return response

        result = self._parse_result(response, verbose)

        return result

    def query_region_async(self, region_type, get_query_payload, **kwargs):
        """
        Performs the `CDS MOC Service`_ query

        Parameters
        ----------
        region_type : ``astroquery.cds.RegionType``
            The type of the region.
        get_query_payload : bool
            If True, returns a dictionary in the form of a dictionary
        **kwargs
             Arbitrary keyword arguments depending on the ``region_type`` parameter

        Returns
        -------
        response : `~requests.Response`:
            The HTTP response from the `CDS MOC Service`_

        """

        request_payload = self._args_to_payload(region_type=region_type, **kwargs)
        if get_query_payload:
            return request_payload

        params_d = {
            'method': 'GET',
            'url': self.URL,
            'timeout': self.TIMEOUT,
            'cache': False
        }

        if 'filename' not in request_payload:
            params_d.update({'params': request_payload})
            response = self._request(**params_d)

        else:
            filename = request_payload['filename']
            with open(filename, 'rb') as f:
                request_payload.pop('filename')

                params_d.update({'params': request_payload,
                                 'files': {'moc': f}})

                response = self._request(**params_d)

        return response

    def _args_to_payload(self, **kwargs):
        """
        Convert ``kwargs`` keyword arguments to a dictionary of payload

        Parameters
        ----------
        kwargs
            Arbitrary keyword arguments

        Returns
        -------
        request_payload : dict{str : str}
            The payloads submitted to the `CDS MOC service`_

        """

        request_payload = dict()
        # Region Type
        region_type = kwargs['region_type']
        if region_type == CdsClass.RegionType.MOC:
            from .spatial_constraints import Moc

            if 'filename' not in kwargs and 'url' not in kwargs and 'moc' not in kwargs:
                raise KeyError('Need at least one of these three following parameters when querying the '
                               'CDS MOC service with a MOC:\n'
                               '- filename: indicates the local path to a fits moc file\n'
                               '- url: the url to a fits moc file\n'
                               '- moc: a mocpy object')

            if 'filename' in kwargs:
                moc = Moc.from_file(filename=kwargs['filename'],
                                    intersect=kwargs.get('intersect', 'overlaps'))
            elif 'url' in kwargs:
                moc = Moc.from_url(url=kwargs['url'],
                                   intersect=kwargs.get('intersect', 'overlaps'))
            else:
                moc = Moc.from_mocpy_object(mocpy_obj=kwargs['moc'],
                                            intersect=kwargs.get('intersect', 'overlaps'))

            # add the moc region payload to the request payload
            request_payload.update(moc.request_payload)
        elif region_type == CdsClass.RegionType.Cone:
            from .spatial_constraints import Cone

            if 'radius' not in kwargs or 'center' not in kwargs:
                raise KeyError('Need the radius and the position when querying the CDS MOC service'
                               'with a cone region')

            cone = Cone(center=kwargs['center'],
                        radius=kwargs['radius'],
                        intersect=kwargs.get('intersect', 'overlaps'))

            # add the cone region payload to the request payload
            request_payload.update(cone.request_payload)
        elif region_type == CdsClass.RegionType.Polygon:
            from .spatial_constraints import Polygon

            if 'vertices' not in kwargs:
                raise KeyError('Need to specify the skycoords when querying the CDS MOC service'
                               ' with a Polygon')

            polygon = Polygon(vertices=kwargs['vertices'],
                              intersect=kwargs.get('intersect', 'overlaps'))

            # add the polygon region payload to the request payload
            request_payload.update(polygon.request_payload)
        else:
            # in case of region_type == CdsClass.RegionType.AllSky, no need to update the request payload
            pass

        if 'meta_data' in kwargs:
            from .property_constraint import PropertyConstraint
            meta_data_constraint = PropertyConstraint(kwargs['meta_data'])
            request_payload.update(meta_data_constraint.request_payload)

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
        Parsing of the ``response`` following :param:`output_format`

        Parameters
        ----------
        response : `~requests.Response`
            The HTTP response from the `CDS MOC service`_
        verbose : bool, optional
            False by default
        Returns
        -------
        result : depends on :param:`output_format`
            The result that is returned by the :meth:`~astroquery.cds.CdsClass.query_region` method

        """

        if not verbose:
            commons.suppress_vo_warnings()

        json_result = response.json()
        if self.output_format.format is cds.ReturnFormat.record:
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
            # The user will get a mocpy.MOC object that he can manipulate (i.o in fits file,
            # MOC operations, plot the MOC using matplotlib, etc...)
            # TODO : just call the MOC.from_json classmethod to get the corresponding mocpy object.
            # TODO : this method will be available in a new mocpy version

            result = CdsClass._create_mocpy_object_from_json(json_result)
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

    @staticmethod
    def _create_mocpy_object_from_json(json_moc):
        """
        ``mocpy.MOC`` object instantiation from a MOC expressed in json

        Parameters
        ----------
        json_moc : dict{str : [int]}
            json MOC definition involving a list of pix for specific orders in string format.

        Returns
        -------
        moc : ``mocpy.MOC``
            the MOC object created

        """
        """
        Create a mocpy.MOC object from a moc expressed in json format

        """

        try:
            from mocpy import MOC
        except ImportError:
            raise ImportError("Could not import mocpy, which is a requirement for the CDS service."
                              "  Please see https://github.com/cds-astro/mocpy to install it.")

        def orderipix2uniq(n_order, i_pix):
            """
            Convert an (order, pix) tuple defining a MOC tile into a uniq number

            Parameters
            ----------
            n_order : int
                order of the MOC tile. Must be <= 29
            i_pix : int
                pixel number of the MOC tile

            Returns
            -------
            order : int
                uniq singleton number defining a MOC tile

            """

            return ((4 ** n_order) << 2) + i_pix

        from mocpy.interval_set import IntervalSet
        uniq_interval = IntervalSet()
        for order, pix_l in json_moc.items():
            order = int(order)

            for pix in pix_l:
                uniq_interval.add(orderipix2uniq(order, pix))

        moc = MOC.from_uniq_interval_set(uniq_interval)
        return moc

    class RegionType(Enum):
        """
        Region type enumeration for :meth:`~astroquery.cds.CdsClass.query_region`

        """

        MOC = 1,
        Cone = 2,
        Polygon = 3,
        AllSky = 4

    class ReturnFormat(Enum):
        """
        Output format enumeration for :meth:`~astroquery.cds.CdsClass.query_region`

        """

        id = 1,
        record = 2,
        number = 3,
        moc = 4,
        i_moc = 5

    class ServiceType(Enum):
        """
        Service type enumeration for :meth:`~astroquery.cds.Dataset.search`

        """

        cs = 1,
        tap = 2,
        ssa = 4,
        sia = 5


cds = CdsClass()
