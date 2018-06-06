from astroquery.vo import Registry
from astropy.tests.helper import remote_data 

## To run just this test, 
## 
## ( cd ../../ ; python setup.py test -t astroquery/vo/tests/test_registry_remote.py --remote-data )
##


# Find all SIA services from HEASARC.
@remote_data
def test_basic():
    # Find all SIA services from HEASARC.
    heasarc_image_services = Registry.query(source='heasarc',
                                            service_type='image')
    assert(len(heasarc_image_services) >= 108)
    print(f"yes, len={len(heasarc_image_services)}")


@remote_data
def test_adql_service():
    query=Registry._build_adql(service_type="image")
    assert "sia#query" in query
    print(f"yes, query={query}")

test_basic()
test_adql_service()
