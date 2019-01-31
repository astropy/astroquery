# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Javier Duran
@contact: javier.duran@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 13 Ago. 2018


"""
import pytest

from astroquery.esa_hubble.core import ESAHubbleClass
from astroquery.esa_hubble.tests.dummy_handler import DummyHandler
from astroquery.esa_hubble.tests.dummy_tap_handler import DummyESAHubbleTapHandler
from astropy import coordinates
# from astropy.tests.helper import remote_data


class TestESAHubble():

    def test_get_product(self):
        parameterst = {}
        parameterst['query'] = "select top 10 * from hsc_v2.hubble_sc2"
        parameterst['output_file'] = "test2.vot"
        parameterst['output_format'] = "votable"
        parameterst['verbose'] = False
        dummyTapHandler = DummyESAHubbleTapHandler("launch_job", parameterst)

        parameters = {}
        parameters['observation_id'] = "J6FL25S4Q"
        parameters['calibration_level'] = "RAW"
        parameters['verbose'] = False
        dummyHandler = DummyHandler("get_product", parameters)
        ehst = ESAHubbleClass(dummyHandler, dummyTapHandler)
        ehst.get_product("J6FL25S4Q", "RAW")
        dummyHandler.check_call("get_product", parameters)

    def test_get_artifact(self):
        parameterst = {}
        parameterst['query'] = "select top 10 * from hsc_v2.hubble_sc2"
        parameterst['output_file'] = "test2.vot"
        parameterst['output_format'] = "votable"
        parameterst['verbose'] = False
        dummyTapHandler = DummyESAHubbleTapHandler("launch_job", parameterst)

        parameters = {}
        parameters['artifact_id'] = "O5HKAX030_FLT.FITS"
        parameters['verbose'] = False
        dummyHandler = DummyHandler("get_artifact", parameters)
        ehst = ESAHubbleClass(dummyHandler, dummyTapHandler)
        ehst.get_artifact("O5HKAX030_FLT.FITS")
        dummyHandler.check_call("get_artifact", parameters)

    def test_get_postcard(self):
        parameterst = {}
        parameterst['query'] = "select top 10 * from hsc_v2.hubble_sc2"
        parameterst['output_file'] = "test2.vot"
        parameterst['output_format'] = "votable"
        parameterst['verbose'] = False
        dummyTapHandler = DummyESAHubbleTapHandler("launch_job", parameterst)

        parameters = {}
        parameters['observation_id'] = "X0MC5101T"
        parameters['verbose'] = False
        dummyHandler = DummyHandler("get_postcard", parameters)
        ehst = ESAHubbleClass(dummyHandler, dummyTapHandler)
        ehst.get_product("X0MC5101T")
        dummyHandler.check_call("get_postcard", parameters)

    def test_query_target(self):
        parameterst = {}
        parameterst['query'] = "select top 10 * from hsc_v2.hubble_sc2"
        parameterst['output_file'] = "test2.vot"
        parameterst['output_format'] = "votable"
        parameterst['verbose'] = False
        dummyTapHandler = DummyESAHubbleTapHandler("launch_job", parameterst)

        parameters = {}
        parameters['name'] = "m31"
        parameters['verbose'] = False
        dummyHandler = DummyHandler("query_target", parameters)
        ehst = ESAHubbleClass(dummyHandler, dummyTapHandler)
        ehst.query_target(parameters['name'])
        dummyHandler.check_call("query_target", parameters)

    def test_cone_search(self):
        c = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s", frame='icrs')
        parameterst = {}
        parameterst['query'] = "select top 10 * from hsc_v2.hubble_sc2"
        parameterst['output_file'] = "test2.vot"
        parameterst['output_format'] = "votable"
        parameterst['verbose'] = False
        dummyTapHandler = DummyESAHubbleTapHandler("launch_job", parameterst)

        parameters = {}
        parameters['coordinates'] = c
        parameters['radius'] = None
        parameters['file_name'] = None
        parameters['verbose'] = False
        dummyHandler = DummyHandler("cone_search", parameters)

        ehst = ESAHubbleClass(dummyHandler, dummyTapHandler)
        ehst.cone_search(parameters['coordinates'])
        dummyHandler.check_call("cone_search", parameters)

    def test_query_hst_tap(self):
        parameters = {}
        parameters['query'] = "select top 10 * from hsc_v2.hubble_sc2"
        parameters['output_file'] = "test2.vot"
        parameters['output_format'] = "votable"
        parameters['verbose'] = False
        dummyHandler = DummyHandler("launch_job", parameters)
        dummyTapHandler = DummyESAHubbleTapHandler("launch_job", parameters)
        ehst = ESAHubbleClass(dummyHandler, dummyTapHandler)
        ehst.query_hst_tap(parameters['query'], parameters['output_file'],
                           parameters['output_format'], parameters['verbose'])
        dummyTapHandler.check_call("launch_job", parameters)

    def test_get_tables(self):
        parameters = {}
        parameters['query'] = "select top 10 * from hsc_v2.hubble_sc2"
        parameters['output_file'] = "test2.vot"
        parameters['output_format'] = "votable"
        parameters['verbose'] = False

        parameters2 = {}
        parameters2['only_names'] = True
        parameters2['verbose'] = True

        dummyHandler = DummyHandler("launch_job", parameters)
        dummyTapHandler = DummyESAHubbleTapHandler("get_tables", parameters2)
        ehst = ESAHubbleClass(dummyHandler, dummyTapHandler)
        ehst.get_tables(True, True)
        dummyTapHandler.check_call("get_tables", parameters2)

    def test_get_columns(self):
        parameters = {}
        parameters['query'] = "select top 10 * from hsc_v2.hubble_sc2"
        parameters['output_file'] = "test2.vot"
        parameters['output_format'] = "votable"
        parameters['verbose'] = False

        parameters2 = {}
        parameters2['table_name'] = "table"
        parameters2['only_names'] = True
        parameters2['verbose'] = True

        dummyHandler = DummyHandler("launch_job", parameters)
        dummyTapHandler = DummyESAHubbleTapHandler("get_columns", parameters2)
        ehst = ESAHubbleClass(dummyHandler, dummyTapHandler)
        ehst.get_columns("table", True, True)
        dummyTapHandler.check_call("get_columns", parameters2)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    pytest.main()
