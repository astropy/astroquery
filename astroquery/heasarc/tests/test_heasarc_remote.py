# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
from astropy.tests.helper import remote_data, pytest
from ...heasarc import Heasarc


@remote_data
class TestHeasarc:

    def test_basic_example(self):
        mission = 'rospublic'
        object_name = '3c273'

        heasarc = Heasarc()
        table = heasarc.query_object(object_name, mission=mission)

        assert len(table) == 1000
