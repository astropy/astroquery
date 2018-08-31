# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Javier Duran
@contact: javier.duran@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 13 Ago. 2018


"""
import unittest

from astroquery.hst.core import HstClass
from astroquery.hst.tests.dummy_handler import DummyHandler
from astroquery.hst.tests.dummy_tap_handler import DummyEhstTapHandler
from astropy import coordinates


class TestEhst(unittest.TestCase):

    def test_get_product(self):
        parameters = {}
        parameters['observation_id'] = "J6FL25S4Q"
        parameters['calibration_level'] = "RAW"
        parameters['verbose'] = False
        dummyHandler = DummyHandler("get_product", parameters)
        ehst = HstClass(dummyHandler)
        ehst.get_product("J6FL25S4Q", "RAW")
        dummyHandler.check_call("get_product", parameters)

    def test_get_artifact(self):
        parameters = {}
        parameters['artifact_id'] = "O5HKAX030_FLT.FITS"
        parameters['verbose'] = False
        dummyHandler = DummyHandler("get_artifact", parameters)
        ehst = HstClass(dummyHandler)
        ehst.get_artifact("O5HKAX030_FLT.FITS")
        dummyHandler.check_call("get_artifact", parameters)

    def test_get_postcard(self):
        parameters = {}
        parameters['observation_id'] = "X0MC5101T"
        parameters['verbose'] = False
        dummyHandler = DummyHandler("get_postcard", parameters)
        ehst = HstClass(dummyHandler)
        ehst.get_product("X0MC5101T")
        dummyHandler.check_call("get_postcard", parameters)

    def test_get_metadata(self):
        parameters = {}
        parameters['params'] = "".join((
                                        "RESOURCE_CLASS=ARTIFACT&OBSERVATION.",
                                        "OBSERVATION_ID=i9zg04010&",
                                        "SELECTED_FIELDS=ARTIFACT.ARTIFACT_ID",
                                        "&RETURN_TYPE=VOTABLE"
                                        ))
        parameters['verbose'] = False
        dummyHandler = DummyHandler("get_metadata", parameters)
        ehst = HstClass(dummyHandler)
        ehst.get_metadata("".join(("RESOURCE_CLASS=ARTIFACT&",
                                   "OBSERVATION.OBSERVATION_ID=",
                                   "i9zg04010&SELECTED_FIELDS=",
                                   "ARTIFACT.ARTIFACT_ID&RETURN",
                                   "_TYPE=VOTABLE")))
        dummyHandler.check_call("get_metadata", parameters)

    def test_query_target(self):
        parameters = {}
        parameters['name'] = "m31"
        parameters['verbose'] = False
        dummyHandler = DummyHandler("query_target", parameters)
        ehst = HstClass(dummyHandler)
        ehst.query_target(parameters['name'])
        dummyHandler.check_call("query_target", parameters)

    def test_cone_search(self):
        c = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s", frame='icrs')
        parameters = {}
        parameters['coordinates'] = c
        parameters['radius'] = None
        parameters['file_name'] = None
        parameters['verbose'] = False
        dummyHandler = DummyHandler("cone_search", parameters)
        ehst = HstClass(dummyHandler)
        ehst.cone_search(parameters['coordinates'])
        dummyHandler.check_call("cone_search", parameters)

    def test_query_hst_tap(self):
        parameters = {}
        parameters['query'] = "select top 10 * from hsc_v2.hubble_sc2"
        parameters['output_file'] = "test2.vot"
        parameters['output_format'] = "votable"
        parameters['verbose'] = False
        dummyHandler = DummyHandler("launch_job", parameters)
        dummyTapHandler = DummyEhstTapHandler("launch_job", parameters)
        ehst = HstClass(dummyHandler, dummyTapHandler)
        ehst.query_hst_tap(parameters['query'], parameters['output_file'],
                           parameters['output_format'], parameters['verbose'])
        dummyTapHandler.check_call("launch_job", parameters)

test = TestEhst()

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
