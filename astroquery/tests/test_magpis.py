from astroquery import magpis

def test_get_file():
    fitsfile = get_magpis_image_gal(10.5,0.0)
