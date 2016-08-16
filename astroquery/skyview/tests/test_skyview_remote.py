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

    with open(data_path('survey_dict.txt'), 'r') as f:
        survey_dict = eval(f.read())

    @pytest.mark.parametrize(('survey',
                              'survey_data'),
                             zip(survey_dict.keys(), survey_dict.values()))
    def test_survey(self, survey, survey_data):
        # The print should help discover changes
        print("Survey: {0} \n Canned reference return: {1} \n"
              "Online service return: {2}".format(
                survey, survey_data,
                self.SkyView.survey_dict.get(
                    survey, "{0} is not in online version".format(survey))))

        assert set(self.SkyView.survey_dict[survey]) == set(survey_data)

    def test_whole_survey_list(self):
        # Content was already checked, test for the keys
        assert set(self.SkyView.survey_dict) == set(self.survey_dict)
