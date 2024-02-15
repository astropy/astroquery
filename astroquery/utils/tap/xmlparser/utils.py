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
import gzip
import io
import json

from astropy import units as u
from astropy.table import Table as APTable
from astropy.table.table import Table


def util_create_string_from_buffer(buffer):
    return ''.join(map(str, buffer))


def read_http_response(response, output_format, *, correct_units=True):
    astropy_format = get_suitable_astropy_format(output_format)

    # If we want to use astropy.table, we have to read the data
    data = io.BytesIO(response.read())

    try:
        result = APTable.read(io.BytesIO(gzip.decompress(data.read())), format=astropy_format)
    except OSError:
        # data is not a valid gzip file by BadGzipFile.

        if output_format == 'json':

            data = json.load(response)

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
                result = APTable.read(data, format=astropy_format)
        else:
            result = APTable.read(data, format=astropy_format)

    if correct_units:
        modify_unrecognized_table_units(result)

    return result


def get_suitable_astropy_format(output_format):
    if 'ecsv' == output_format:
        return 'ascii.ecsv'
    elif 'csv' == output_format:
        return 'ascii.csv'
    elif 'votable_plain' == output_format or 'votable_gzip' == output_format:
        return 'votable'
    elif 'json' == output_format:
        return 'pandas.json'
    return output_format


def modify_unrecognized_table_units(table):
    """Modifies the units of an input table column in place
    """
    for cn in table.colnames:
        col = table[cn]
        if isinstance(col.unit, u.UnrecognizedUnit):
            try:
                col.unit = u.Unit(col.unit.name.replace(".", " ").replace("'", ""))
            except Exception:
                pass
        elif isinstance(col.unit, str):
            col.unit = col.unit.replace(".", " ").replace("'", "")
