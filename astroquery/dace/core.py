# Licensed under a 3-clause BSD style license - see LICENSE.rst

from collections import defaultdict
from json import JSONDecodeError
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

        Returns
        -------
        response : a ``requests.Response`` from DACE
        """
        return self._request("GET", ''.join([self.__DACE_URL, self.__RADIAL_VELOCITIES_ENDPOINT, object_name]),
                             timeout=self.__DACE_TIMEOUT, headers=self.__HEADERS)

    def _parse_result(self, response, verbose=False):
        try:
            json_data = response.json()
            dace_dict = self.transform_data_as_dict(json_data)
            return Table(dace_dict)
        except JSONDecodeError as error:
            raise ParseException("Failed to parse DACE result. Request response : {}".format(response.text)) from error

    @staticmethod
    def transform_data_as_dict(json_data):
        """
        Internally DACE data are provided using protobuff. The format is a list of parameters. Here we parse
        these data to give to the user something more readable and ignore the internal stuff
        """
        data = defaultdict(list)
        parameters = json_data.get('parameters')
        for parameter in parameters:
            variable_name = parameter.get('variableName')
            double_values = parameter.get('doubleValues')
            int_values = parameter.get('intValues')
            string_values = parameter.get('stringValues')
            bool_values = parameter.get('boolValues')
            # Only one type of values can be present. So we look for the next occurence not None
            values = next(values_list for values_list in [double_values, int_values, string_values, bool_values] if
                          values_list is not None)
            data[variable_name].extend(values)

            error_values = parameter.get('minErrorValues')  # min or max is symmetric
            if error_values is not None:
                data[variable_name + '_err'].extend(error_values)
        return data


Dace = DaceClass()
