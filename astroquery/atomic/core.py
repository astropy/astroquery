from astropy.extern.six.moves.urllib import parse as urlparse
from astropy.extern.six.moves import map, zip
from astropy.extern.six import StringIO
from astropy.extern import six

from collections import defaultdict

from astropy.io import ascii
from astropy.table import Table
from astropy import units as u
from bs4 import BeautifulSoup

from ..query import BaseQuery
from ..utils import commons
from ..utils import prepend_docstr_noreturns
from ..utils import async_to_sync
from . import ATOMIC_LINE_LIST_URL, TIMEOUT


__all__ = ['AtomicLineList', 'AtomicLineListClass']


@async_to_sync
class AtomicLineListClass(BaseQuery):
    FORM_URL = ATOMIC_LINE_LIST_URL()
    TIMEOUT = TIMEOUT()

    def __init__(self):
        BaseQuery.__init__(self)
        self._default_form_values = None

    def query_object(self, wavelength_range=None, wavelength_type=None,
                     wavelength_accuracy=None, element_spectrum=None):
        """
        Parameters
        ----------
        wavelength_range : pair of `astropy.units.Unit` values

        wavelength_type : str
            Either 'Air' or 'Vacuum'

        wavelength_accuracy :

        element_spectrum :

        Returns
        -------
        result : `~astropy.table.Table`
            The result of the query as a `~astropy.table.Table` object.

        """
        response = self.query_object_async(
            wavelength_range, wavelength_type, wavelength_accuracy, element_spectrum)
        table = self._parse_result(response)
        return table

    @prepend_docstr_noreturns(query_object.__doc__)
    def query_object_async(self, wavelength_range=None, wavelength_type='',
                           wavelength_accuracy=None, element_spectrum=None):
        """
        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """
        if self._default_form_values is None:
            response = commons.send_request(self.FORM_URL, {}, self.TIMEOUT, 'GET')
            bs = BeautifulSoup(response.text)
            form = bs.find('form')
            self._default_form_values = self._get_default_form_values(form)
        default_values = self._default_form_values
        wltype = (wavelength_type or default_values.get('air', '')).lower()
        if wltype in ('air', 'vacuum'):
            air = wltype.capitalize()
        else:
            raise ValueError('parameter wavelength_type must be either "air" or "vacuum".')
        wlrange = wavelength_range or []
        if len(wlrange) not in (0, 2):
            raise ValueError(
                'length of `wavelength_range` must be 2 or 0, but is: {}'.format(
                    len(wlrange)))
        # convert wavelengths in incoming wavelength range to Angstroms
        wlrange_in_angstroms = (wl.to(u.Angstrom, equivalencies=u.spectral()).value for wl in wlrange)
        input = {
            'wavl': '-'.join(map(str, wlrange_in_angstroms)),
            'wave': 'Angstrom',
            'air': air,
            'wacc': wavelength_accuracy,
            'elmion': element_spectrum,
            # TODO: add support for more parameters
        }
        response = self._submit_form(input)
        return response

    def _parse_result(self, response):
        data = StringIO(BeautifulSoup(response.text).find('pre').text.strip())
        # `header` is e.g. "u'-LAMBDA-VAC-ANG-|-SPECTRUM--|TT|--------TERM---------|---J-J---|----LEVEL ENERGY--CM-1----'"
        header = data.readline().strip().strip('|')
        # `colnames` is then "[u'LAMBDA VAC ANG', u'SPECTRUM', u'TT', u'TERM', u'J J', u'LEVEL ENERGY  CM 1']"
        colnames = [colname.strip('-').replace('-', ' ') for colname in header.split('|') if colname.strip()]
        indices = [i for i, c in enumerate(header) if c == '|']
        input = []
        for line in data:
            # example for `line`:
            # u'      1.010799    Zn XXX     E1          1-10          1/2-*            0.00 - 98933890.00\n'
            row = []
            for start, end in zip([0]+indices, indices+[None]):
                # `value` will hold all cell values in the line, so
                # `u'1.010799'`, `u'Zn XXX'` etc.
                value = line[start:end].strip()
                if value:
                    row.append(value)
            if row:
                input.append('\t'.join(row))
        if input:
            return ascii.read(input, data_start=0, delimiter='\t', names=colnames)
        else:
            # return an empty table if the query yielded no results
            return Table()

    def _submit_form(self, input=None):
        """Fill out the form of the SkyView site and submit it with the
        values given in `input` (a dictionary where the keys are the form
        element's names and the values are their respective values).

        """
        if input is None:
            input = {}
        response = commons.send_request(self.FORM_URL, {}, self.TIMEOUT, 'GET')
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
        url = urlparse.urljoin(self.FORM_URL, form.get('action'))
        response = commons.send_request(url, payload, self.TIMEOUT)
        return response

    def _get_default_form_values(self, form):
        """Return the already selected values of a given form (a BeautifulSoup
        form node) as a dict.

        """
        res = defaultdict(list)
        for elem in form.find_all(['input', 'select']):
            key = elem.get('name')
            value = None
            # ignore the submit and reset buttons
            if elem.get('type') in ['submit', 'reset']:
                continue
            # check boxes: enabled boxes have the value "on" if not specificed
            # otherwise. Found out by debugging, perhaps not documented.
            if elem.get('type') == 'checkbox' and elem.get('checked') in ["", "checked"]:
                value = elem.get('value', 'on')
            # radio buttons and simple input fields
            if elem.get('type') == 'radio' and\
                    elem.get('checked') in ["", "checked"] or\
                    elem.get('type') in [None, 'text']:
                value = elem.get('value')
            # dropdown menu, multi-section possible
            if elem.name == 'select':
                for option in elem.find_all('option'):
                    if option.get('selected') == '':
                        value = option.get('value', option.text.strip())
            if value and value not in [None, u'None', u'null']:
                res[key].append(value)
        # avoid values with size 1 lists
        d = dict(res)
        for k, v in six.iteritems(d):
            if len(v) == 1:
                d[k] = v[0]
        return d


AtomicLineList = AtomicLineListClass()
