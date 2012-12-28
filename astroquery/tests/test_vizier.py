from astroquery import vizquery

def test_simple():
    query = {}
    query["-source"] = "VII/258/vv10"
    query["-out"] = ["Name", "Sp", "Vmag"]
    query["Vmag"] = "5.0..11.0"
    table1 = vizquery(query)
    
    #Find sources in 2MASS matching the AGNs positions to within 2 arcsec
    query = {}
    query["-source"] = "II/246/out"
    query["-out"] = ["RAJ2000", "DEJ2000", "2MASS", "Kmag"]
    query["-c.rs"] = "2"
    query["-c"] = table1
    table2 = vizquery(query)
    
    print(table1)
    print(table2)

