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
from astropy.table import Table as APTable
from astropy import units as u


def check_file_exists(file_name):
    if file_name is None:
        return False
    if file_name.strip() == "":
        return False
    return os.path.exists(file_name)


def read_results_table_from_file(file_name, output_format, correct_units=True):
    if check_file_exists(file_name):
        result = APTable.read(file_name, format=output_format)
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
    else:
        return None
