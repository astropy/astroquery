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
    URL = conf.server
    TIMEOUT = conf.timeout

    def query_region(self, type, get_query_payload=False, verbose=False, **kwargs):
        """
        Query the CDS MOC service according to some spatial and meta-data constraints

        The output format of the query response is expressed by the param `output_format`

        Parameters
        ----------
        constraints : cds.Constraints
            The constraints needed by the CDS MOC service to perform the query
        output_format : cds.OutputFormat
            The output format we want to retrieve the matched data sets (e.g. full record,
            just IDs, mocpy.MOC objects)
        get_query_payload : bool
            specifies if we only want the CDS service to return the payload

        Returns
        -------
            data sets in a format `output_format` dependant. (e.g. a list of data set IDs, a MOC object resulting
            from the union of all the matched data set MOCs or a dictionary of data sets indexed by their IDs.

        """

        response = self.query_region_async(type, get_query_payload, **kwargs)
        if get_query_payload:
            return response

        result = self._parse_result(response, verbose)

        return result

    def query_region_async(self, type, get_query_payload, **kwargs):
        """
        Query the CDS MOC service according to some spatial and meta-data constraints

        The output format of the query response is expressed by the param `output_format`

        Parameters
        ----------
        constraints : cds.Constraints
            The constraints needed by the CDS MOC service to perform the query
        output_format : cds.OutputFormat
            The output format we want to retrieve the matched data sets (e.g. full record,
            just IDs, mocpy.MOC objects)
        get_query_payload : bool
            specifies if we only want the CDS service to return the payload

        Returns
        -------
            data sets in a format `output_format` dependant. (e.g. a list of data set IDs, a MOC object resulting
            from the union of all the matched data set MOCs or a dictionary of data sets indexed by their IDs.

        """
        request_payload = self._args_to_payload(type=type, **kwargs)
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
            return response

        filename = request_payload['filename']
        with open(filename, 'rb') as f:
            request_payload.pop('filename')

            params_d.update({'params': request_payload,
                             'files': {'moc': f}})

            return self._request(**params_d)

    def _args_to_payload(self, *args, **kwargs):
        request_payload = dict()
        # Region Type
        type = kwargs['type']
        if type == CdsClass.RegionType.MOC:
            from .spatial_constraints import Moc

            assert 'filename' in kwargs or 'url' in kwargs or 'moc' in kwargs,\
                KeyError('Need at least one of these three following parameters when querying the '
                         'CDS MOC service with a MOC:\n'
                         '- filename: indicates the local path to a fits moc file\n'
                         '- url: the url to a fits moc file\n'
                         '- moc: a mocpy object')

            moc = None
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
        elif type == CdsClass.RegionType.Cone:
            from .spatial_constraints import Cone

            assert 'radius' in kwargs and 'center' in kwargs,\
                KeyError('Need the radius and the position when querying the CDS MOC service'
                         'with a cone region')

            cone = Cone(center=kwargs['center'],
                        radius=kwargs['radius'],
                        intersect=kwargs.get('intersect', 'overlaps'))

            # add the cone region payload to the request payload
            request_payload.update(cone.request_payload)
        elif type == CdsClass.RegionType.Polygon:
            from .spatial_constraints import Polygon

            assert 'vertices' in kwargs, KeyError('Need to specify the skycoords when querying the CDS MOC service'
                                                  ' with a Polygon')

            polygon = Polygon(vertices=kwargs['vertices'],
                              intersect=kwargs.get('intersect', 'overlaps'))

            # add the polygon region payload to the request payload
            request_payload.update(polygon.request_payload)
        else:
            # in case of type == CdsClass.RegionType.AllSky, no need to update the request payload
            pass

        if 'meta_data' in kwargs:
            from .property_constraint import PropertyConstraint
            meta_data_constraint = PropertyConstraint(kwargs['meta_data'])
            request_payload.update(meta_data_constraint.request_payload)

        # Output format payload
        from sys import maxsize
        self.output_format = OutputFormat(format=kwargs.get('format', cds.ReturnFormat.id),
                                          field_l=kwargs.get('meta_var', list()),
                                          moc_order=kwargs.get('moc_order', maxsize),
                                          case_sensitive=kwargs.get('case_sensitive', True),
                                          max_rec=kwargs.get('max_rec', None))
        request_payload.update(self.output_format.request_payload)

        return request_payload

    def _parse_result(self, response, verbose=False):
        """
        Parse the CDS HTTP response to a more convenient format for python users

        :param response: the HTTP response
        :param output_format: the output format that the user has specified
        :param verbose: boolean. if verbose is False then suppress any VOTable related warnings
        :return: the final parsed response that will be given to the user
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
        try:
            return float(value)
        except (ValueError, TypeError):
            return value

    @staticmethod
    def _remove_duplicate(value_l):
        if isinstance(value_l, list):
            value_l = list(set(value_l))
            if len(value_l) == 1:
                return value_l[0]

        return value_l

    @staticmethod
    def _create_mocpy_object_from_json(json_moc):

        """
        Create a mocpy.MOC object from a moc expressed in json format

        :param json_moc:
        :return: a mocpy.MOC object
        """

        try:
            from mocpy import MOC
        except ImportError:
            raise ImportError("Could not import mocpy, which is a requirement for the CDS service."
                              "  Please see https://github.com/cds-astro/mocpy to install it.")

        def orderipix2uniq(n_order, i_pix):
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
        MOC = 1,
        Cone = 2,
        Polygon = 3,
        AllSky = 4

    class ReturnFormat(Enum):
        id = 1,
        record = 2,
        number = 3,
        moc = 4,
        i_moc = 5

    class ServiceType(Enum):
        cs = 1,
        tap = 2,
        ssa = 4,
        sia = 5


cds = CdsClass()
