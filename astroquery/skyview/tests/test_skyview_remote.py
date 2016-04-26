# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy.tests.helper import remote_data, pytest
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
class TestSkyviewRemote(object):

    @classmethod
    def setup_class(cls):
        cls.SkyView = SkyView()
        cls.survey_dict = cls.SkyView.survey_dict

    with open(data_path('survey_dict.txt'), 'r') as f:
        survey_dict = eval(f.read())

    @pytest.mark.parametrize(('survey',
                              'survey_data'),
                             zip(survey_dict.keys(), survey_dict.values()))
    def test_survey(self, survey, survey_data):

        print(self.SkyView.survey_dict[survey] == survey_data, survey)
        print("Canned reference return", self.__class__.survey_dict['Radio'])
        print("online service return", self.SkyView.survey_dict['Radio'])

    def test_whole_survey_list(self):
        assert self.SkyView.survey_dict == self.__class__.survey_dict
