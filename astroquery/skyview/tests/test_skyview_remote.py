from ...skyview import SkyView


def test_get_image_list():
    urls = SkyView().get_image_list(position='Eta Carinae', survey=['Fermi 5', 'HRI', 'DSS'])
    assert urls == [
        u'http://skyview.gsfc.nasa.gov/tempspace/fits/skv6183161285798_1.fits',
        u'http://skyview.gsfc.nasa.gov/tempspace/fits/skv6183161285798_2.fits',
        u'http://skyview.gsfc.nasa.gov/tempspace/fits/skv6183161285798_3.fits']