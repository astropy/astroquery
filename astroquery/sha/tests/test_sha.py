# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ...utils import turn_off_internet
turn_off_internet()
from ... import sha


def test_query():
    # Example queries for SHA API help page
    pos_t = sha.query(ra=163.6136, dec=-11.784, size=0.5)
    nid_t = sha.query(naifid=2003226)
    pid_t = sha.query(pid=30080)
    rqk_t = sha.query(reqkey=21641216)
    # Get table and fits URLs
    table_url = pid_t['accessUrl'][10]
    image_url = pid_t['accessUrl'][16]
    # Not implemented because running will download file
    # sha.save_file(table_url)
    # sha.save_file(image_url)
    img = sha.get_file(image_url)
