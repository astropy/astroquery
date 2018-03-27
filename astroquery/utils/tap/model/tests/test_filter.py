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
from astroquery.utils.tap.model.filter import Filter


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class TestFilter(unittest.TestCase):

    def test_filter(self):
        f = Filter()
        res = f.create_url_data_request()
        expected = {}
        expected['metadata_only'] = True
        assert res == expected, \
            "Parameters I, expected: %s, found: %s" % (str(expected), str(res))
        filter1 = "f1"
        value1 = "v1"
        filter2 = "f2"
        value2 = "v2"
        f.add_filter(filter1, value1)
        f.add_filter(filter2, value2)
        res = f.create_url_data_request()
        expected = {filter1: value1, filter2: value2}
        expected['metadata_only'] = True
        assert res == expected, \
            "Parameters II, expected: %s, found: %s" % (str(expected), str(res))
        offset = "offset"
        order = "order"
        limit = "limit"
        metadataOnly = "metadataOnly"
        f.set_offset(offset)
        f.set_order(order)
        f.set_limit(limit)
        f.set_metadata_only(metadataOnly)
        res = f.create_url_data_request()
        expected = {filter1: value1,
                    filter2: value2,
                    offset: offset,
                    order: order,
                    limit: limit,
                    'metadata_only': metadataOnly}
        assert res == expected, \
            "Parameters III, expected: %s, found: %s" % (str(expected), str(res))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
