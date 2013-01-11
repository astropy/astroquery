from astroquery import nrao

def test_get_image():
    fitsfile = nrao.get_nrao_image(49.489,-0.37,overwrite=True)
