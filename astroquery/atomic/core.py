# Licensed under a 3-clause BSD style license - see LICENSE.rst

from six.moves.urllib import parse as urlparse
from six.moves import map, zip
from six import StringIO
import six

from collections import defaultdict

from astropy.io import ascii
from astropy.table import Table
from astropy import units as u
from bs4 import BeautifulSoup

from ..query import BaseQuery
from ..utils import prepend_docstr_nosections, async_to_sync
from . import conf
from .utils import is_valid_transitions_param

__all__ = ['AtomicLineList', 'AtomicLineListClass']


@async_to_sync
class AtomicLineListClass(BaseQuery):
    FORM_URL = conf.url
    TIMEOUT = conf.timeout

    def __init__(self):
        super(AtomicLineListClass, self).__init__()
        self._default_form_values = None

    def query_object(self, wavelength_range=None, wavelength_type=None,
                     wavelength_accuracy=None, element_spectrum=None,
                     minimal_abundance=None, depl_factor=None,
                     lower_level_energy_range=None,
                     upper_level_energy_range=None, nmax=None,
                     multiplet=None, transitions=None,
                     show_fine_structure=None,
                     show_auto_ionizing_transitions=None,
                     output_columns=('spec', 'type', 'conf',
                                     'term', 'angm', 'prob',
                                     'ener')):
        """
        Queries Atomic Line List for the given parameters adnd returns the
        result as a `~astropy.table.Table`. All parameters are optional.

        Parameters
        ----------
        wavelength_range : pair of `astropy.units.Unit` values
            Wavelength range. Can be done in two ways: supply a lower and
            upper limit for the region or, supply the central wavelength and
            the 1 sigma error (68 % confidence value) for that line. If the
            first number is smaller than the second number, this implies
            that the first option has been chosen, and otherwise the second
            option.

        wavelength_type : str
            Either ``'Air'`` or ``'Vacuum'``.

        wavelength_accuracy : str
            All wavelengths in the line list have relative accuracies of
            5% or better. The default is to list all lines, irrespective
            of their accuracy. When a relative accuracy in percent is
            given, only those lines with accuracies better than or equal
            to the passed value are included in the search. Values larger
            than 5% will be ignored.

        element_spectrum : str
            Restrict the search to a range of elements and/or ionization
            stages. The elements should be entered by their usual
            symbolic names (e.g. Fe) and the ionization stages by the
            usual spectroscopic notation (e.g. I for neutral, II for
            singly ionized etc.). To pass multiple values, separate them
            by ``\\n`` (newline).

        minimal_abundance : str
             Impose a lower limit on the abundances of elements to be
             considered for possible identifications. Default is to
             consider arbitrary low abundances. The elements are assumed
             to have standard cosmic abundances.

        depl_factor : str
            For nebular conditions it is not a realistic assumption that
            the elements have standard cosmic abundances since most
            metals will be depleted on grains. To simulate this it is
            possible to supply a depletion factor df. This factor will be
            used to calculate the actual abundance A from the cosmic
            abundance Ac using the formula A(elm) = Ac(elm) - df*sd(elm)
            where sd is the standard depletion for each element.

        lower_level_energy_range : `~astropy.units.Quantity`
            Default is to consider all values for the lower/upper level
            energy to find a possible identification. To restrict the
            search a range of energies can be supplied.
            The supported units are: Ry, eV, 1/cm, J, erg.

        upper_level_energy_range : `~astropy.units.Quantity`
            See parameter ``lower_level_energy_range``.

        nmax : int
            Maximum for principal quantum number n. Default is to
            consider all possible values for the principal quantum number
            n to find possible identifications. However, transitions
            involving electrons with a very high quantum number n tend to
            be weaker and can therefore be less likely identifications.
            These transitions can be suppressed using this parameter.

        multiplet : str
            This option (case sensitive) can be used to find all lines in
            a specific multiplet within a certain wavelength range. The
            lower and upper level term should be entered here exactly as
            they appear in the output of the query. The spectrum to which
            this multiplet belongs should of course also be supplied in
            the ``element_spectrum`` parameter.

        transitions : str`
            Possible values are:
                - ``'all'``:
                    The default, consider all transition types.
                - ``'nebular'``:
                    Consider only allowed transitions of Hydrogen or
                    Helium and only magnetic dipole or electric quadrupole
                    transitions of other elements.
                - A union of the values: One of the following:
                  ``'E1'``, ``'IC'``, ``'M1'``, ``'E2'``
                  Refer to [1]_ for the meaning of these values.

        show_fine_structure : bool
             If `True`, the fine structure components will be included in
             the output. Refer to [1]_ for more information.

        show_auto_ionizing_transitions : bool
            If `True`, transitions originating from auto-ionizing levels
            will be included in the output. In this context, all levels
            with energies higher than the ionization potential going to
            the ground state of the next ion are considered auto-ionizing
            levels.

        output_columns : tuple
            A Tuple of strings indicating which output columns are retrieved.
            A subset of ('spec', 'type', 'conf', 'term', 'angm', 'prob',
            'ener') should be used. Where each string corresponds to the
            column titled Spectrum, Transition type, Configuration, Term,
            Angular momentum, Transition probability and Level energies
            respectively.

        Returns
        -------
        result : `~astropy.table.Table`
            The result of the query as a `~astropy.table.Table` object.

        References
        ----------
        .. [1] http://www.pa.uky.edu/~peter/atomic/instruction.html
        """
        response = self.query_object_async(
            wavelength_range=wavelength_range, wavelength_type=wavelength_type,
            wavelength_accuracy=wavelength_accuracy,
            element_spectrum=element_spectrum,
            minimal_abundance=minimal_abundance, depl_factor=depl_factor,
            lower_level_energy_range=lower_level_energy_range,
            upper_level_energy_range=upper_level_energy_range, nmax=nmax,
            multiplet=multiplet, transitions=transitions,
            show_fine_structure=show_fine_structure,
            show_auto_ionizing_transitions=show_auto_ionizing_transitions,
            output_columns=output_columns)
        table = self._parse_result(response)
        return table

    @prepend_docstr_nosections(query_object.__doc__)
    def query_object_async(self, wavelength_range=None, wavelength_type='',
                           wavelength_accuracy=None, element_spectrum=None,
                           minimal_abundance=None, depl_factor=None,
                           lower_level_energy_range=None,
                           upper_level_energy_range=None, nmax=None,
                           multiplet=None, transitions=None,
                           show_fine_structure=None,
                           show_auto_ionizing_transitions=None,
                           output_columns=('spec', 'type', 'conf',
                                           'term', 'angm', 'prob',
                                           'ener')):
        """
        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """
        if self._default_form_values is None:
            response = self._request("GET", url=self.FORM_URL, data={},
                                     timeout=self.TIMEOUT)
            bs = BeautifulSoup(response.text)
            form = bs.find('form')
            self._default_form_values = self._get_default_form_values(form)
        default_values = self._default_form_values
        wltype = (wavelength_type or default_values.get('air', '')).lower()
        if wltype in ('air', 'vacuum'):
            air = wltype.capitalize()
        else:
            raise ValueError('parameter wavelength_type must be either "air" '
                             'or "vacuum".')
        if wavelength_range is not None:
            wlrange = wavelength_range
        else:
            wlrange = []
        if len(wlrange) not in (0, 2):
            raise ValueError('Length of `wavelength_range` must be 2 or 0, '
                             'but is: {}'.format(len(wlrange)))
        if not is_valid_transitions_param(transitions):
            raise ValueError('Invalid parameter "transitions": {0!r}'
                             .format(transitions))
        if transitions is None:
            _type = self._default_form_values.get('type')
            type2 = self._default_form_values.get('type2')
        else:
            s = str(transitions)
            if len(s.split(',')) > 1:
                _type = 'Sel'
                type2 = s.split(',')
            else:
                _type = s
                type2 = ''
        # convert wavelengths in incoming wavelength range to Angstroms
        wlrange_in_angstroms = (wl.to(u.Angstrom,
                                      equivalencies=u.spectral()).value
                                for wl in wlrange)

        lower_level_erange = lower_level_energy_range
        if lower_level_erange is not None:
            lower_level_erange = lower_level_erange.to(
                u.cm ** -1, equivalencies=u.spectral()).value
        upper_level_erange = upper_level_energy_range
        if upper_level_erange is not None:
            upper_level_erange = upper_level_erange.to(
                u.cm ** -1, equivalencies=u.spectral()).value
        input = {
            'wavl': '-'.join(map(str, wlrange_in_angstroms)),
            'wave': 'Angstrom',
            'air': air,
            'wacc': wavelength_accuracy,
            'elmion': element_spectrum,
            'abun': minimal_abundance,
            'depl': depl_factor,
            'elo': lower_level_erange,
            'ehi': upper_level_erange,
            'ener': 'cm^-1',
            'nmax': nmax,
            'term': multiplet,
            'type': _type,
            'type2': type2,
            'hydr': show_fine_structure,
            'auto': show_auto_ionizing_transitions,
            'form': output_columns,
            'tptype': 'as_a'}
        response = self._submit_form(input)
        return response

    def _parse_result(self, response):
        data = StringIO(BeautifulSoup(response.text).find('pre').text.strip())
        # `header` is e.g.:
        # "u'-LAMBDA-VAC-ANG-|-SPECTRUM--|TT|--------TERM---------|---J-J---|----LEVEL-ENERGY--CM-1----'"
        # `colnames` is then
        # [u'LAMBDA VAC ANG', u'SPECTRUM', u'TT', u'TERM', u'J J',
        #  u'LEVEL ENERGY  CM 1']

        header = data.readline().strip().strip('|')

        colnames = [colname.strip('-').replace('-', ' ')
                    for colname in header.split('|') if colname.strip()]
        indices = [i for i, c in enumerate(header) if c == '|']
        input = []
        for line in data:
            row = []
            for start, end in zip([0] + indices, indices + [None]):
                # `value` will hold all cell values in the line, so
                # `u'1.010799'`, `u'Zn XXX'` etc.
                value = line[start:end].strip()
                if value:
                    row.append(value)
                else:
                    # maintain table dimensions when data missing
                    row.append('None')
            if row:
                input.append('\t'.join(row))
        if input:
            return ascii.read(input, data_start=0, delimiter='\t',
                              names=colnames)
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
        response = self._request("GET", url=self.FORM_URL, data={},
                                 timeout=self.TIMEOUT)
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
        response = self._request("POST", url=url, data=payload,
                                 timeout=self.TIMEOUT)
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
            # check boxes: enabled boxes have the value "on" if not specified
            # otherwise. Found out by debugging, perhaps not documented.
            if (elem.get('type') == 'checkbox' and
                    elem.get('checked') in ["", "checked"]):
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
