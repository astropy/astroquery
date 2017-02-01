# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
Gaia TAP plus
=============

@author: Juan Carlos Segovia
@contact: juan.carlos.segovia@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 30 jun. 2016


"""
import unittest
import os
from astroquery.gaiatap.tapplus.model.table import Table
from astroquery.gaiatap.tapplus.model.column import Column

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

class TestTable(unittest.TestCase):
    
    def test_table(self):
        table = Table()
        schemaName = "sch"
        tableName = "tbl"
        expected = schemaName + "." + tableName
        table.set_schema(schemaName)
        table.set_name(tableName)
        res = table.get_qualified_name()
        assert res == expected, \
            "Qualified name, expected: %s, found: %s" % (expected, res)
        pass
    
    def test_table_columns(self):
        table = Table()
        c1 = Column()
        c2 = Column()
        table.add_column(c1)
        table.add_column(c2)
        res = table.get_columns()
        assert len(res) == 2, \
            "Num columns, expected: %d, found: %d" % (2, len(res))
        pass
    
    pass

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()