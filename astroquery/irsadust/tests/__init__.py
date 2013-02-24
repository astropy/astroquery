# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
This packages contains affiliated package tests.
"""
import os
import xml.etree.ElementTree as tree

class DustTestCase(object):
    def data(self, filename):
        data_dir = os.path.join(os.path.dirname(__file__), 't')
        return os.path.join(data_dir, filename)
