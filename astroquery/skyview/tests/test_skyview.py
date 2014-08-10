# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os.path

from ...utils.testing_tools import MockResponse
from ...skyview import SkyView


class MockResponseSkyView(MockResponse):
    def __init__(self):
        super(MockResponseSkyView, self).__init__()
        with open(data_path('results.html'), 'rb') as f:
            self.content = f.read()

    def get_content(self):
        return self.content


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def test_get_image_list_local(monkeypatch):
    sv = SkyView()
    monkeypatch.setattr(sv, '_submit_form', lambda inp: MockResponseSkyView())
    urls = sv.get_image_list(
        position='Eta Carinae', survey=['Fermi 5', 'HRI', 'DSS'])
    assert len(urls) == 3
    for url in urls:
        assert url.startswith('../../tempspace/fits/')
