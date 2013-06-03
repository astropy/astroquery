# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import sha

def test_query():
    # Example queries for SHA API help page
    sha.query(ra=163.6136, dec=-11.784, size=0.5)
    sha.query(naifid=2003226)
    sha.query(pid=30080)
    sha.query(reqkey=21641216)


