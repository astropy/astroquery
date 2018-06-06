from astroquery.vo import Registry

# Find all SIA services from HEASARC.
#heasarc_image_services = Registry.query(source='heasarc', service_type='image')
def test_basic():
    # Find all SIA services from HEASARC.
    heasarc_image_services = Registry.query(source='heasarc',\
                                            service_type='image')
    assert(len(heasarc_image_services) >= 108)


