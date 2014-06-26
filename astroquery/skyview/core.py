import urlparse

import six
import requests
from bs4 import BeautifulSoup

from . import SKYVIEW_URL
from ..query import BaseQuery


class SkyViewClass(BaseQuery):
    URL = SKYVIEW_URL()

    def __init__(self):
        BaseQuery.__init__(self)
        self._default_form_values = None

    def _get_default_form_values(self, form):
        """Return the already selected values of a given form (a BeautifulSoup
        form node) as a dict.

        """
        res = []
        for elem in form.find_all(['input', 'select']):
            # ignore the submit and reset buttons
            if elem.get('type') in ['submit', 'reset']:
                continue
            # check boxes: enabled boxes have the value "on" if not specificed
            # otherwise. Found out by debugging, perhaps not documented.
            if elem.get('type') == 'checkbox' and elem.get('checked') in ["", "checked"]:
                value = elem.get('value', 'on')
                res.append((elem.get('name'), value))
            # radio buttons and simple input fields
            if elem.get('type') == 'radio' and\
                    elem.get('checked') in ["", "checked"] or\
                    elem.get('type') in [None, 'text']:
                res.append((elem.get('name'), elem.get('value')))
            # dropdown menu, multi-section possible
            if elem.name == 'select':
                for option in elem.find_all('option'):
                    if option.get('selected') == '':
                        value = option.get('value', option.text.strip())
                        res.append((elem.get('name'), value))
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
        # cache the default values to save HTTP traffic
        if self._default_form_values is None:
            self._default_form_values = self._get_default_form_values(form)
        # only overwrite payload's values if the `input` value is not None
        # to avoid overwriting of the form's default values
        payload = self._default_form_values.copy()
        for k, v in six.iteritems(input):
            if v is not None:
                payload[k] = v
        url = urlparse.urljoin(self.URL, form.get('action'))
        response = requests.get(url, params=payload)
        return response

    def download(
            self, position, survey, deedger=None, lut=None,
            projection=None, gridlabels=None, coordinates=None, scaling=None,
            grid=None, resolver=None, sampler=None, pixels=None):
        """Query the SkyView service, download the FITS file that will be
        found and return the local path to the download FITS file.

        """
        input = {
            'Position': position,
            'survey': survey,
            'Deedger': deedger,
            'lut': lut,
            'projection': projection,
            'gridlabels': gridlabels,
            'coordinates': coordinates,
            'scaling': scaling,
            'grid': grid,
            'resolver': resolver,
            'Sampler': sampler,
            'pixels': pixels}
        response = self._submit_form(input)
        bs = BeautifulSoup(response.content)
        for a in bs.find_all('a'):
            if a.text == 'FITS':
                href = a.get('href')
                abs_href = urlparse.urljoin(response.url, href)
                # download the FITS file
                path = self.request('GET', abs_href, save=True)
                yield path

SkyView = SkyViewClass()
