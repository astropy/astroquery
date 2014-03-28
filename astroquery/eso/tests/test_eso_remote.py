# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
from astropy.tests.helper import remote_data
from ... import eso
import requests
import imp
imp.reload(requests)


@remote_data
def test_SgrAstar():

    instruments = eso.Eso.list_instruments()
    results = [eso.Eso.query_instrument(ins, target='Sgr A*') for ins in instruments]
    
