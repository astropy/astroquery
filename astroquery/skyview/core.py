import urlparse

import six
import requests
from bs4 import BeautifulSoup

from . import SKYVIEW_URL
from ..query import BaseQuery


class SkyViewClass(BaseQuery):
    URL = SKYVIEW_URL()

    def _get_default_form_values(self, form):
        is_button = lambda elem: elem.get('type') in ['submit', 'reset']
        res = []
        for elem in form.find_all(['input', 'select']):
            if is_button(elem):
                continue
            # radio buttons, check boxes and simple input fields
            if elem.get('type') in ['radio', 'checkbox'] and\
                    elem.get('checked') in ["", "checked"] or\
                    elem.get('type') in [None, 'text']:
                res.append((elem.get('name'), elem.get('value')))
            # dropdown menu, multi-section possible
            if elem.name == 'select':
                for option in elem.find_all('option'):
                    if option.get('selected') == '':
                        res.append((elem.get('name'), option.text.strip()))
        return dict(filter(
            lambda (k, v): v not in [None, u'None', u'null'] and v, res))

    def _submit_form(self, input=None):
        """Fill out the form of the SkyView site and submit it with the
        values given in `input` (a dictionary where the keys are the form
        element's names and the values are their respective values).

        """
        if input is None:
            input = {}
        response = requests.get(self.URL)
        bs = BeautifulSoup(response.text)
        form = bs.find('form')
        #payload = self._get_default_form_values(form)
        payload = input
        url = urlparse.urljoin(self.URL, form.get('action'))
        # only overwrite payload's values if the `input` value is not None
        # to avoid overwriting of the form's default values
        for k, v in six.iteritems(input):
            if v is not None:
                payload[k] = v
        response = requests.get(url, params=payload)
        return response

    def download(self, position, survey):
        """Query the SkyView service, download the FITS file that will be
        found and return the local path to the download FITS file.

        """
        input = {
            'Position': position,
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
