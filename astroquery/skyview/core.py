import itertools
from operator import itemgetter

import requests
from bs4 import BeautifulSoup

from . import SKYVIEW_URL
from ..query import BaseQuery
from ..utils import commons


class SkyViewClass(BaseQuery):
    URL = SKYVIEW_URL()

    def _get_default_form_values(self, form):
        is_button = lambda elem: elem.get('type') in ['submit', 'reset']
        res = []
        for elem in form.find_all(['input', 'select']):
            if is_button(elem):
                continue
            # radio buttons, check boxes and simple input fields
            if elem.get('type') in ['radio', 'checkbox'] and elem.get('checked') in ["", "checked"] or\
                    elem.get('type') in [None, 'text']:
                res.append((elem.get('name'), elem.get('value')))
            # dropdown menue, multi-section possible
            if elem.name == 'select':
                for option in elem.find_all('option'):
                    if option.get('selected') == '':
                        res.append((elem.get('name'), option.text.strip()))
        # combine multiple name->value associations to
        # a single name->[list of values] association
        # the keys of the returned dict will be the names of the form elements,
        # the values will be a list of values because the select elements may
        # allow multiple selection
        return dict(
            [(k, list(set(map(itemgetter(1), g))))
                for k, g in itertools.groupby(res, itemgetter(0))])

    def _submit_form(self, input=None):
        if input is None:
            input = {}
        response = requests.get(self.URL)
        bs = BeautifulSoup(response.text)
        form = bs.find('form')
        payload = self._get_default_form_values(form)
        payload.update(input)
        response = self.request('GET', self.URL, params=payload)
        return response

    def query(self):
        raise NotImplementedError

SkyView = SkyViewClass()
