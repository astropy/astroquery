# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
from collections import defaultdict
from astropy.table import Table
from ..query import BaseQuery
from ..utils import async_to_sync
from . import conf

__all__ = ['Dace', 'DaceClass']


class ParseException(Exception):
    """Raised when parsing Dace data fails"""


@async_to_sync
class DaceClass(BaseQuery):
    """
    DACE class to access DACE (Data Analysis Center for Exoplanets) data based in Geneva Observatory
    """

    __DACE_URL = conf.server
    __DACE_TIMEOUT = conf.timeout
    __OBSERVATION_ENDPOINT = 'ObsAPI/observation/'
    __RADIAL_VELOCITIES_ENDPOINT = __OBSERVATION_ENDPOINT + 'radialVelocities/'
    __HEADERS = {'Accept': 'application/json'}

    def query_radial_velocities_async(self, object_name):
        """
        Get radial velocities data for an object_name. For example : HD40307

        Parameters
        ----------
        object_name : str
            The target you want radial velocities data

        Return
        ------
        response : a ``requests.Response`` from DACE
        """
        return self._request("GET", ''.join([self.__DACE_URL, self.__RADIAL_VELOCITIES_ENDPOINT, object_name]),
                             timeout=self.__DACE_TIMEOUT, headers=self.__HEADERS)

    def _parse_result(self, response, verbose=False):
        try:
            json_data = response.json()
            dace_dict = self._transform_data_as_dict(json_data)
            return Table(dace_dict)
        except Exception as ex:
            raise ParseException(
                "Failed to parse DACE result! Exception : {} \nRaw content : {}".format(ex, response.text))

    @staticmethod
    def _transform_data_as_dict(json_data):
        """
        Internally DACE data are provided using protobuff. The format is a list of parameters. Here we parse
        these data to give to the user something more readable and ignore the internal stuff
        """
        data = defaultdict(list)
        parameters = json_data['parameters']
        for parameter in parameters:
            variable_name = parameter['variableName']
            data[variable_name].extend(parameter['doubleValues']) if 'doubleValues' in parameter \
                else None
            data[variable_name].extend(parameter['intValues']) if 'intValues' in parameter \
                else None
            data[variable_name].extend(parameter['stringValues']) if 'stringValues' in parameter \
                else None
            data[variable_name].extend(parameter['boolValues']) if 'boolValues' in parameter \
                else None
            data[variable_name + '_err'].extend(parameter['minErrorValues']) \
                if 'minErrorValues' in parameter else []  # min or max is symmetric
        return data


Dace = DaceClass()
