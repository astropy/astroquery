import itertools
from operator import itemgetter
import urlparse

import requests
from bs4 import BeautifulSoup

from . import SKYVIEW_URL
from ..query import BaseQuery


class SkyViewClass(BaseQuery):
    URL = SKYVIEW_URL()

    def _submit_form(self, input=None):
        if input is None:
            input = {}
        response = requests.get(self.URL)
        bs = BeautifulSoup(response.text)
        form = bs.find('form')
        url = urlparse.urljoin(self.URL, form.get('action'))
        response = requests.get(url, params=input)
        return response

    def download(self, coordinates, survey):
        """Query the SkyView service, download the FITS file that will be
        found and return the local path to the download FITS file.

        """
        input = {
            'Position': coordinates,
            'survey': survey}
        response = self._submit_form(input)
        bs = BeautifulSoup(response.content)
        a_node = (a for a in bs.find_all('a') if a.text == 'FITS').next()
        href = a_node.get('href')
        abs_href = urlparse.urljoin(response.url, href)
        # download the FITS file
        path = self.request('GET', abs_href, save=True)
        return path

SkyView = SkyViewClass()
