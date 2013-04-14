# Licensed under a 3-clause BSD style license - see LICENSE.rst
import urllib2
from ...utils import chunk_read, chunk_report

def test_utils():
    response = urllib2.urlopen('http://www.ebay.com')
    C = chunk_read(response, report_hook=chunk_report)
    print C
