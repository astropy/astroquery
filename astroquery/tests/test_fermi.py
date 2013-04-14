from astroquery import fermi

def test_query():
    
    query = fermi.FermiLAT_Query()
    result = query('M31')
    print result

if __name__ == '__main__':
    test_query()