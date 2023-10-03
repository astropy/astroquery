# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest

from astropy.coordinates import SkyCoord
from pyvo import registry

from ...skyview import SkyView


# Monkeypatch Fixtures

mock_valid_survey = {
    'ivoid': 'ivo://nasa.heasarc/skyview/mockedsurvey',
    'short_name': "mockedsurvey_shortname",
    'res_title': "mockedsurvey_restitle"
}


def siasearch_mockreturn(*args, **kwargs):
    class MockSiaServiceRegsearchResponse():
        def __init__(self):
            # Mock a random SIA survey response
            self.ivoid = mock_valid_survey['ivoid']
            self.short_name = mock_valid_survey['short_name']
            self.res_title = mock_valid_survey['res_title']

        def get_service(self):
            """ Monkeypatch actually retrieving and calling a SIA survey """
            class MockSiaService():
                def search(self, *args, **kwargs):
                    class MockSiaQueryResponse():
                        def getdataurl(self):
                            # This is just a random skyview response
                            return "https://skyview.gsfc.nasa.gov/cgi-bin/images?position=161.26474075372%2C-59.6844587777&amp;survey=dss&amp;pixels=300%2C300&amp;sampler=LI&amp;size=1.0%2C1.0&amp;projection=Tan&amp;coordinates=J2000.0&amp;requestID=skv1696608093085&amp;return=FITS"  # noqa
                    return [MockSiaQueryResponse()]
            return MockSiaService()
    return [MockSiaServiceRegsearchResponse()]


@pytest.fixture
def patch_siaregistry(request):
    """ Monkeypatch (intercept and replace) registry.search with our own siasearch_mockreturn """
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(registry, 'search', siasearch_mockreturn)

    return mp


# Survey validation local tests

def test_survey_validation(patch_siaregistry):
    """ Test interal validation of provided Skyview survey """
    # Test a valid response:
    # As List
    SkyView._validate_surveys([mock_valid_survey['short_name']])
    # As String
    SkyView._validate_surveys(mock_valid_survey['short_name'])

    # Test an invalid survey:
    fake_survey_name = 'not_a_valid_survey'
    # Single Case:
    with pytest.raises(ValueError) as ex:
        SkyView._validate_surveys(fake_survey_name)

    assert str(ex.value) == (f"Survey {fake_survey_name} is not "
                             "among the surveys hosted at "
                             "skyview.  See list_surveys or "
                             "survey_dict for valid surveys.")
    # Mixed Case:
    with pytest.raises(ValueError) as ex:
        SkyView._validate_surveys([mock_valid_survey['short_name'], fake_survey_name])

    assert str(ex.value) == (f"Survey {fake_survey_name} is not "
                             "among the surveys hosted at "
                             "skyview.  See list_surveys or "
                             "survey_dict for valid surveys.")

    # Test invalid survey again, but higher up:
    # Single Case:
    with pytest.raises(ValueError) as ex:
        SkyView.get_image_list(position='doesnt matter',
                               survey=[fake_survey_name])

    assert str(ex.value) == (f"Survey {fake_survey_name} is not "
                             "among the surveys hosted at "
                             "skyview.  See list_surveys or "
                             "survey_dict for valid surveys.")
    # Mixed Case:
    with pytest.raises(ValueError) as ex:
        SkyView.get_image_list(position='doesnt matter',
                               survey=[mock_valid_survey['short_name'], fake_survey_name])

    assert str(ex.value) == (f"Survey {fake_survey_name} is not "
                             "among the surveys hosted at "
                             "skyview.  See list_surveys or "
                             "survey_dict for valid surveys.")


# Test Mock SIA Query

def test_get_image_list_local(patch_siaregistry):
    """
    Test retrieving the URL list for a Skyview Query, but offline (with a monkeypatched response)
    """
    urls = SkyView.get_image_list(position=SkyCoord(42, 42, unit="deg"),
                                  survey=[mock_valid_survey['short_name']])
    assert len(urls) == 1
    for url in urls:
        assert url.startswith('https://skyview.gsfc.nasa.gov/cgi-bin/images?')
