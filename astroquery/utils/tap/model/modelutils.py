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

import os
import json

from astropy.table import Table as APTable

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
            files = {}
            with open(file_name) as f:
                data = json.load(f)

                if data.get('data') and data.get('metadata'):

                    files['data'] = APTable.read(json.dumps({"data": data['data']}), format=astropy_format)
                    files['metadata'] = APTable.read(json.dumps({"metadata": data['metadata']}), format=astropy_format)

                    return files
                else:
                    return APTable.read(file_name, format=astropy_format)
        else:
            result = APTable.read(file_name, format=astropy_format)

            if correct_units:
                utils.modify_unrecognized_table_units(result)

            return result
    else:
        return None
