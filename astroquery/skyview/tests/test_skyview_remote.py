# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy.tests.helper import remote_data
from astropy.io.fits import HDUList

from ...skyview import SkyView
from .test_skyview import data_path


@remote_data
def test_get_image_list():
    urls = SkyView().get_image_list(position='Eta Carinae',
                                    survey=['Fermi 5', 'HRI', 'DSS'])
    assert len(urls) == 3
    for url in urls:
        assert url.startswith('http://skyview.gsfc.nasa.gov/tempspace/fits/')


@remote_data
def test_get_images():
    images = SkyView().get_images(position='Eta Carinae', survey=['2MASS-J'])
    assert len(images) == 1
    assert isinstance(images[0], HDUList)


@remote_data
def test_survey_list():
    with open(data_path('survey_dict.txt'), 'r') as f:
        survey_dict = eval(f.read())

    for key in survey_dict.keys():
        print(SkyView.survey_dict[key] == survey_dict[key], key)
    print("Canned reference return", survey_dict['Radio'])
    print("online service return", SkyView.survey_dict['Radio'])
    assert SkyView.survey_dict == survey_dict
