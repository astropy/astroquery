# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

@author: Juan Carlos Segovia
@contact: juan.carlos.segovia@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 30 jun. 2016


"""

import json
import os

from astropy.table import Table as APTable
from astropy.table.table import Table

from astroquery.utils.tap.xmlparser import utils


def check_file_exists(file_name):
    if file_name is None:
        return False
    if file_name.strip() == "":
        return False
    return os.path.exists(file_name)


def read_results_table_from_file(file_name, output_format, *, correct_units=True):
    astropy_format = utils.get_suitable_astropy_format(output_format)

    if check_file_exists(file_name):

        if output_format == 'json':

            with open(file_name) as f:
                data = json.load(f)

                if data.get('data') and data.get('metadata'):

                    column_name = []
                    for name in data['metadata']:
                        column_name.append(name['name'])

                    result = Table(rows=data['data'], names=column_name, masked=True)

                    for v in data['metadata']:
                        col_name = v['name']
                        result[col_name].unit = v['unit']
                        result[col_name].description = v['description']
                        result[col_name].meta = {'metadata': v}

                else:
                    result = APTable.read(file_name, format=astropy_format)

                if correct_units:
                    utils.modify_unrecognized_table_units(result)

                return result

        else:
            result = APTable.read(file_name, format=astropy_format)

            if correct_units:
                utils.modify_unrecognized_table_units(result)

            return result
    else:
        return None
