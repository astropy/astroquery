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
from astropy import units as u
from astropy.table import Table as APTable


def util_create_string_from_buffer(buffer):
    return ''.join(map(str, buffer))


def read_http_response(response, output_format, correct_units=True):
    astropy_format = get_suitable_astropy_format(output_format)

    # If we want to use astropy.table, we have to read the data
    data = io.BytesIO(response.read())

    try:
        result = APTable.read(io.BytesIO(gzip.decompress(data.read())), format=astropy_format)
    except OSError:
        # data is not a valid gzip file by BadGzipFile.
        result = APTable.read(data, format=astropy_format)
        pass

    if correct_units:
        for cn in result.colnames:
            col = result[cn]
            if isinstance(col.unit, u.UnrecognizedUnit):
                try:
                    col.unit = u.Unit(col.unit.name.replace(".", " ").replace("'", ""))
                except Exception as ex:
                    pass
            elif isinstance(col.unit, str):
                col.unit = col.unit.replace(".", " ").replace("'", "")

    return result


def get_suitable_astropy_format(output_format):
    if 'ecsv' == output_format:
        return 'ascii.ecsv'
    elif 'csv' == output_format:
        return 'ascii.csv'
    elif 'votable_plain' == output_format:
        return 'votable'
    return output_format


def read_file_content(file_path):
    file_handler = open(file_path, 'r')
    file_content = file_handler.read()
    file_handler.close()
    return file_content
