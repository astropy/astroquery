# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import fermi

def test_FermiLAT_Query():
    
    # Make a query that results in small SC and PH file sizes
    result = fermi.FermiLAT_Query('M31', energyrange_MeV='1000, 100000', obsdates='2013-01-01 00:00:00, 2013-01-02 00:00:00')
    print result

def test_FermiLAT_DelayedQuery():
    result_url = 'TODO'
    query = fermi.FermiLAT_DelayedQuery(result_url)
    # TODO
    print query

if __name__ == '__main__':
    test_FermiLAT_Query()
