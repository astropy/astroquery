# Licensed under a 3-clause BSD style license - see LICENSE.rst

from ... import ned
import socket
import time

def test_objname():
    result = ned.query_ned_by_objname()

def test_nearname():
    result = ned.query_ned_nearname()

def test_near_iauname():
    result = ned.query_ned_near_iauname()

def test_by_refcode():
    result = ned.query_ned_by_refcode()

def test_names():
    result = ned.query_ned_names()

def test_basic_posn():
    result = ned.query_ned_basic_posn()

def test_ned_external():
    result = ned.query_ned_external()

# I cannot get this to pass.  It just gives timeout errors.
#try:
#    #time.sleep(1)  # wait before running another query
#    def test_ned_allsky():
#        result = ned.query_ned_allsky(ra_constraint='Between',
#                                      ra_1='00h00m00.0',
#                                      ra_2='01h00m00.0',
#                                      z_constraint='Larger Than',
#                                      z_value1=2.0)
#except Exception as error: #socket.error:
#    print "Some kind of error: ",error

def test_ned_photometry():
    result = ned.query_ned_photometry()

def test_ned_diameters():
    result = ned.query_ned_diameters()

def test_ned_redshifts():
    result = ned.query_ned_redshifts()

def test_ned_notes():
    result = ned.query_ned_notes()

def test_ned_position():
    result = ned.query_ned_position()

def test_ned_nearpos():
    result = ned.query_ned_nearpos()
