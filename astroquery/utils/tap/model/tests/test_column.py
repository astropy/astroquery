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

import unittest
import os
from astroquery.utils.tap.model.tapcolumn import TapColumn


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class TestTableColumn(unittest.TestCase):

    def test_column(self):
        name = "name"
        arraysize = "arraysize"
        datatype = "datatype"
        flag = "flag"
        ucd = "ucd"
        utype = "utype"
        unit = "unit"
        description = "description"
        c = TapColumn()
        c.set_name(name)
        c.set_array_size(arraysize)
        c.set_data_type(datatype)
        c.set_flag(flag)
        c.set_ucd(ucd)
        c.set_unit(unit)
        c.set_utype(utype)
        c.set_description(description)
        assert c.get_name() == name, \
            "Invalid name, expected: %s, found: %s" % (name,
                                                       c.get_name())
        assert c.get_array_size() == arraysize, \
            "Invalid arraysize, expected: %s, found: %s" % (arraysize,
                                                            c.get_array_size())
        assert c.get_data_type() == datatype, \
            "Invalid datatype, expected: %s, found: %s" % (datatype,
                                                           c.get_data_type())
        assert c.get_flag() == flag, \
            "Invalid flag, expected: %s, found: %s" % (flag,
                                                       c.get_flag())
        assert c.get_ucd() == ucd, \
            "Invalid ucd, expected: %s, found: %s" % (ucd,
                                                      c.get_ucd())
        assert c.get_utype() == utype, \
            "Invalid utype, expected: %s, found: %s" % (utype,
                                                        c.get_utype())
        assert c.get_unit() == unit, \
            "Invalid unit, expected: %s, found: %s" % (unit,
                                                       c.get_unit())
        assert c.get_description() == description, \
            "Invalid description, expected: %s, found: %s" % (description,
                                                              c.get_description())


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
