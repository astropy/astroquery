#!/usr/bin/env python
# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst

from astroquery.query import BaseQuery
from astroquery.utils import commons
from astroquery.utils import async_to_sync

try:
    from mocpy import MOC
except ImportError:
    raise ImportError("Could not import mocpy, which is a requirement for the CDS service."
                      "  Please see https://github.com/cds-astro/mocpy to install it.")

from . import conf
from .constraints import Constraints
from .output_format import OutputFormat
from .dataset import Dataset

__all__ = ['cds', 'CdsClass']


@async_to_sync
class CdsClass(BaseQuery):
    URL = conf.server
    TIMEOUT = conf.timeout

    def query_region(self, constraints, output_format=OutputFormat(), get_query_payload=False):
        """
        Query the CDS MOC service which gives all the data sets matching the constraints.
        The output format of the query response is expressed by the param output_format

        :param constraints: The constraints needed by the CDS MOC service to perform the query
        :param output_format: The output format we want to retrieve the matched data sets (e.g. full record,
         just IDs, mocpy.MOC objects)
        :param get_query_payload: specifies if we only want the CDS service to return the payload
        :return: data sets in a format `output_format` dependant. (e.g. a list of data set IDs, a MOC object resulting
         from the union of all the matched data set MOCs or a dictionary of data sets indexed by their IDs.
        """
        response = self.query_region_async(constraints, output_format, get_query_payload)

        if get_query_payload:
            return response

        result = CdsClass.__output_format(response, output_format)

        return result

    def query_region_async(self, constraints, output_format, get_query_payload, cache=True):
        """
        Query the CDS MOC service which gives all the data sets matching the constraints.
        The output format of the query response is expressed by the param output_format

        :param constraints: The constraints needed by the CDS MOC service to perform the query
        :param output_format: The output format we want to retrieve the matched data sets (e.g. full record,
         just IDs, mocpy.MOC objects)
        :param get_query_payload: specifies if we only want the CDS service to return the payload
        :param cache: boolean
        :return: The HTTP response returned from the CDS MOC service.
         All async methods should return the raw HTTP response.
        """
        request_payload = dict()
        if not isinstance(constraints, Constraints):
            raise TypeError("Invalid constraints. Must be of Constraints type")

        if not isinstance(output_format, OutputFormat):
            raise TypeError("Invalid response format. Must be of OutputFormat type")

        request_payload.update(constraints.payload)
        request_payload.update(output_format.request_payload)

        if get_query_payload:
            return request_payload

        params_d = {
            'method': 'GET',
            'url': self.URL,
            'timeout': self.TIMEOUT
        }

        if 'moc' not in request_payload:
            params_d.update({'params': request_payload,
                              'cache': cache})
            return self._request(**params_d)

        filename = request_payload['moc']
        with open(filename, 'rb') as f:
            request_payload.pop('moc')

            params_d.update({'params': request_payload,
                              'cache': False,
                              'files': {'moc': f}})

            return self._request(**params_d)

    @staticmethod
    def __output_format(response, output_format, verbose=False):
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
        if output_format.format is OutputFormat.Type.record:
            # The user will get a dictionary of Dataset objects indexed by their ID names.
            # The http response is a list of dict. Each dict represents one data set. Each dict is a list
            # of (meta-data name, value in str)

            # 1 : all the meta-data values from the data sets returned by the CDS are cast to floats if possible
            result = [dict([md_name, CdsClass.__cast_to_float(md_val)]
                           for md_name, md_val in data_set.items())
                      for data_set in json_result]
            # 2 : a final dictionary of Dataset objects indexed by their ID names is created
            result_tmp = {}
            for data_set in result:
                data_set_id = data_set['ID']
                result_tmp[data_set_id] = Dataset(
                    **dict([md_name, CdsClass.__remove_duplicate(data_set.get(md_name))]
                           for md_name in (data_set.keys() - set('ID')))
                )

            result = result_tmp
        elif output_format.format is OutputFormat.Type.number:
            # The user will get the number of matching data sets
            result = dict(number=int(json_result['number']))
        elif output_format.format is OutputFormat.Type.moc or\
                output_format.format is OutputFormat.Type.i_moc:
            # The user will get a mocpy.MOC object that he can manipulate (i.o in fits file,
            # MOC operations, plot the MOC using matplotlib, etc...)
            # TODO : just call the MOC.from_json classmethod to get the corresponding mocpy object.
            # TODO : this method will be available in a new mocpy version
            result = __class__.__create_mocpy_object_from_json(json_result)
        else:
            # The user will get a list of the matched data sets ID names
            result = json_result

        return result

    @staticmethod
    def __cast_to_float(value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return value

    @staticmethod
    def __remove_duplicate(value_l):
        if isinstance(value_l, list):
            value_l = list(set(value_l))
            if len(value_l) == 1:
                return value_l[0]

        return value_l

    @staticmethod
    def __create_mocpy_object_from_json(json_moc):
        """
        Create a mocpy.MOC object from a moc expressed in json format

        :param json_moc:
        :return: a mocpy.MOC object
        """
        def __orderipix2uniq(n_order, n_pix):
            return ((4 ** n_order) << 2) + n_pix

        from mocpy.interval_set import IntervalSet
        uniq_interval = IntervalSet()
        for n_order, n_pix_l in json_moc.items():
            n_order = int(n_order)

            for n_pix in n_pix_l:
                uniq_interval.add(__orderipix2uniq(n_order, n_pix))

        moc = MOC.from_uniq_interval_set(uniq_interval)
        return moc


cds = CdsClass()
