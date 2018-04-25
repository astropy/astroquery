#!/usr/bin/env python
# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst

# put all imports organized as shown below
# 1. standard library imports
# 2. third party imports
# 3. local imports - use relative imports
# commonly required local imports shown below as example
# all Query classes should inherit from BaseQuery.
from astroquery.query import BaseQuery
# has common functions required by most modules
from astroquery.utils import commons
# async_to_sync generates the relevant query tools from _async methods
from astroquery.utils import async_to_sync

from mocpy import MOC
from mocpy.interval_set import IntervalSet

# import configurable items declared in __init__.py
from . import conf
# import MOCServerConstraints and MOCServerResults
from .constraints import Constraints
from .output_format import OutputFormat
from .dataset import Dataset

# export all the public classes and methods
__all__ = ['cds', 'CdsClass']
# declare global variables and constants if any

# Now begin your main class
# should be decorated with the async_to_sync imported previously


@async_to_sync
class CdsClass(BaseQuery):
    """
    Not all the methods below are necessary but these cover most of the common
    cases, new methods may be added if necessary, follow the guidelines at
    <http://astroquery.readthedocs.io/en/latest/api.html>
    """
    # use the Configuration Items imported from __init__.py to set the URL,
    # TIMEOUT, etc.
    URL = conf.server
    TIMEOUT = conf.timeout

    # For services that can query coordinates, use the query_region method.
    # The pattern is similar to the query_object method. The query_region
    # method also has a 'radius' keyword for specifying the radius around
    # the coordinates in which to search. If the region is a box, then
    # the keywords 'width' and 'height' should be used instead. The coordinates
    # may be accepted as an `astropy.coordinates` object or as a string, which
    # may be further parsed.

    # similarly we write a query_region_async method that makes the
    # actual HTTP request and returns the HTTP response
    def query_region(self, constraints, output_format=OutputFormat(), get_query_payload=False):
        """
        Query the cds mocserver which gives us all the datasets matching the constraints.
        The output format of the query response is expressed by the param output_format

        :param constraints: The constraints (spatial and algebraic) needed by the mocserver for
        getting us all the matching datasets
        :param output_format: The output format we want the matching datasets (full record, just IDs, mocpy object)
        :param get_query_payload: specify if we only want the cds service to return the payload
        :return: matching datasets in a format output_format dependant. (e.g. a list of dataset IDs if we want
        just the IDs, a massive union moc resulting from the union of all the matching dataset mocs or a
        dictionary of datasets indexed by their IDs if the user wants the records of the matching datasets).
        """
        response = self.query_region_async(constraints, output_format, get_query_payload)

        if get_query_payload:
            return response

        result = CdsClass._parse_result_region(response, output_format)

        return result

    @staticmethod
    def _remove_duplicate(value_l):
        if isinstance(value_l, list):
            value_l = list(set(value_l))
            if len(value_l) == 1:
                return value_l[0]

        return value_l

    def query_region_async(self, constraints, output_format, get_query_payload, cache=True):
        """
        Query the cds mocserver which gives us all the datasets matching the constraints.
        The output format of the query response is expressed by the param output_format

        :param constraints: The constraints (spatial and algebraic) needed by the mocserver for
        getting us all the matching datasets
        :param output_format: The output format we want the matching datasets (full record, just IDs, mocpy object)
        :param get_query_payload: specify if we only want the cds service to return the payload
        :param cache: boolean
        :return: The HTTP response returned from the service. All async methods should return the raw HTTP response.
        """
        request_payload = dict()
        if not isinstance(constraints, Constraints):
            print("Invalid constraints. Must be of MOCServerConstraints type")
            raise TypeError

        if not isinstance(output_format, OutputFormat):
            print("Invalid response format. Must be of MOCServerResponseFormat type")
            raise TypeError

        request_payload.update(constraints.payload)
        request_payload.update(output_format.request_payload)

        if get_query_payload:
            return request_payload

        payload_d = {
            'method': 'GET',
            'url': self.URL,
            'timeout': self.TIMEOUT
        }

        if 'moc' not in request_payload:
            payload_d.update({'params': request_payload,
                              'cache': cache})
            return self._request(**payload_d)

        filename = request_payload['moc']
        with open(filename, 'rb') as f:
            request_payload.pop('moc')

            payload_d.update({'params': request_payload,
                              'cache': False,
                              'files': {'moc': f}})

            return self._request(**payload_d)

    @staticmethod
    def _parse_to_float(value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return value

    @staticmethod
    def orderipix2uniq(n_order, n_pix):
        return ((4**n_order) << 2) + n_pix

    @staticmethod
    def create_mocpy_object_from_json(json_moc):
        # TODO : just call the MOC.from_json classmethod to get the corresponding mocpy object
        uniq_interval = IntervalSet()
        for n_order, n_pix_l in json_moc.items():
            n_order = int(n_order)

            for n_pix in n_pix_l:
                uniq_interval.add(__class__.orderipix2uniq(n_order, n_pix))

        moc = MOC.from_uniq_interval_set(uniq_interval)
        return moc

    @staticmethod
    def _parse_result_region(response, output_format, verbose=False):
        """
        Parse the cds mocserver HTTP response to a more convenient format for python users

        :param response: the HTTP response
        :param output_format: the output format that the user has specified
        :param verbose: boolean. if verbose is False then suppress any VOTable related warnings
        :return: the final parsed response that will be given to the user
        """
        if not verbose:
            commons.suppress_vo_warnings()

        r = response.json()
        if output_format.format is OutputFormat.Type.record:
            parsed_r = [dict([k, CdsClass._parse_to_float(v)] for k, v in di.items()) for di in r]
            # Once the properties have been parsed to float we can create the final
            # dictionary of Dataset objects indexed by their IDs
            parsed_r = dict([d['ID'], Dataset(
                **dict([k, CdsClass._remove_duplicate(d.get(k))] for k in (d.keys() - set('ID')))
            )] for d in parsed_r)
        elif output_format.format is OutputFormat.Type.number:
            parsed_r = dict(number=int(r['number']))
        elif output_format.format is OutputFormat.Type.moc or\
                output_format.format is OutputFormat.Type.i_moc:
            # Create a mocpy object from the json syntax
            parsed_r = __class__.create_mocpy_object_from_json(r)
        else:
            parsed_r = r

        return parsed_r


# the default tool for users to interact with is an instance of the Class
cds = CdsClass()

# once your class is done, tests should be written
# See ./tests for examples on this

# Next you should write the docs in astroquery/docs/module_name
# using Sphinx.
