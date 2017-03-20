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

import io
from astropy.table import Table as APTable
import six


def util_create_string_from_buffer(buffer):
    if six.PY2:
        # 2.7
        return ''.join(x.encode('utf-8') for x in buffer)
    else:
        # 3.0
        return ''.join(map(str, buffer))


def read_http_response(response, outputFormat):
    astropyFormat = get_suitable_astropy_format(outputFormat)
    if six.PY2:
        # 2.7
        return APTable.read(response, format=astropyFormat)
    else:
        # 3.0
        # If we want to use astropy.table, we have to read the data
        data = io.BytesIO(response.read())
        return APTable.read(data, format=astropyFormat)


def get_suitable_astropy_format(outputFormat):
    if "csv" == outputFormat:
        return "ascii.csv"
    return outputFormat


def read_file_content(filePath):
    fileHandler = open(filePath, 'r')
    fileContent = fileHandler.read()
    fileHandler.close()
    return fileContent
