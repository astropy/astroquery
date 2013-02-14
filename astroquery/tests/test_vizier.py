from astroquery import vizier

def test_simple1():
    query = {}
    query["-source"] = "VII/258/vv10"
    query["-out"] = ["Name", "Sp", "Vmag"]
    query["Vmag"] = "5.0..11.0"
    table1 = vizier.vizquery(query)
    return table1
    
def test_simple2():
    table1 = test_simple1()
    print(table1)
    #Find sources in 2MASS matching the AGNs positions to within 2 arcsec
    query = {}
    query["-source"] = "II/246/out"
    query["-out"] = ["RAJ2000", "DEJ2000", "2MASS", "Kmag"]
    query["-c.rs"] = "2"
    query["-c"] = table1
    table2 = vizier.vizquery(query)
    print(table2)

# get this error from Table(data,names)...
# ValueError: masked should be one of True, False, None
