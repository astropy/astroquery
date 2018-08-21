# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Javier Duran
@contact: javier.duran@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 13 Ago. 2018


"""
import unittest
import os
import pytest

from astroquery.hst.core import HstClass
from astroquery.hst.tests.dummy_handler import DummyHandler

class TestEhst(unittest.TestCase):

    def test_get_product(self):
        parameters = {}
        parameters['observation_id'] = "J6FL25S4Q"
        parameters['calibration_level'] = "RAW"
        parameters['verbose'] = False
        dummyHandler = DummyHandler("get_product", parameters)
        ehst = HstClass(dummyHandler)
        product = ehst.get_product("J6FL25S4Q","RAW")
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
        parameters['params'] = "RESOURCE_CLASS=ARTIFACT&OBSERVATION.OBSERVATION_ID=i9zg04010&SELECTED_FIELDS=ARTIFACT.ARTIFACT_ID&RETURN_TYPE=VOTABLE"
        parameters['verbose'] = False
        dummyHandler = DummyHandler("get_metadata", parameters)
        ehst = HstClass(dummyHandler)
        metadata = ehst.get_metadata("RESOURCE_CLASS=ARTIFACT&OBSERVATION.OBSERVATION_ID=i9zg04010&SELECTED_FIELDS=ARTIFACT.ARTIFACT_ID&RETURN_TYPE=VOTABLE")
        dummyHandler.check_call("get_metadata", parameters)
        assert metadata == "<?xml version=\"1.0\"?><VOTABLE version=\"1.2\" xmlns=\"http://www.ivoa.net/xml/VOTable/v1.2\"><RESOURCE type=\"eHST results\"><DESCRIPTION>eHST Metadata Query Service</DESCRIPTION><INFO name=\"QUERY_STATUS\" value=\"OK\"></INFO><TABLE><FIELD ID=\"ARTIFACT_ID\" datatype=\"char\" arraysize=\"*\"/><DATA><TABLEDATA><TR><TD>i9zg04010_asn.fits</TD></TR><TR><TD>i9zg04010_drz.fits</TD></TR><TR><TD>i9zg04010_drz.jpg</TD></TR><TR><TD>i9zg04010_drz_thumb.jpg</TD></TR><TR><TD>i9zg04010_jif.fits</TD></TR><TR><TD>i9zg04010_jit.fits</TD></TR><TR><TD>i9zg04010_spt.fits</TD></TR><TR><TD>i9zg04010_trl.fits</TD></TR></TABLEDATA></DATA></TABLE></RESOURCE></VOTABLE>"

test = TestEhst()

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
