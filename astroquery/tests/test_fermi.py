from astroquery import fermi

def test_FermiLAT_Query():
    
    query = fermi.FermiLAT_Query()
    # Make a query that results in small SC and PH file sizes
    result = query('M31', energyrange_MeV='1000, 100000', obsdates='2013-01-01 00:00:00, 2013-01-02 00:00:00')
    print result

def test_FermiLAT_DelayedQuery():
    query = fermi.FermiLAT_DelayedQuery()
    # TODO
    print query

if __name__ == '__main__':
    test_FermiLAT_Query()
