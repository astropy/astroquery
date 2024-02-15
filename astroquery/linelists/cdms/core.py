# Licensed under a 3-clause BSD style license - see LICENSE.rst
import numpy as np
import requests
import os

from bs4 import BeautifulSoup
import astropy.units as u
from astropy.io import ascii
from astroquery.query import BaseQuery
from astroquery.utils import async_to_sync
# import configurable items declared in __init__.py
from astroquery.linelists.cdms import conf
from astroquery.exceptions import InvalidQueryError, EmptyResponseError

import re
import string

__all__ = ['CDMS', 'CDMSClass']


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@async_to_sync
class CDMSClass(BaseQuery):
    # use the Configuration Items imported from __init__.py
    URL = conf.server
    TIMEOUT = conf.timeout

    def query_lines_async(self, min_frequency, max_frequency, *,
                          min_strength=-500, molecule='All',
                          temperature_for_intensity=300, flags=0,
                          parse_name_locally=False, get_query_payload=False,
                          cache=True):
        """
        Creates an HTTP POST request based on the desired parameters and
        returns a response.

        Parameters
        ----------
        min_frequency : `astropy.units.Quantity` or None
            Minimum frequency (or any spectral() equivalent).
            ``None`` can be interpreted as zero.
        max_frequency : `astropy.units.Quantity` or None
            Maximum frequency (or any spectral() equivalent).
            ``None`` can be interpreted as infinite.

        min_strength : int, optional
            Minimum strength in catalog units, the default is -500

        molecule : list, string of regex if parse_name_locally=True, optional
            Identifiers of the molecules to search for. If this parameter
            is not provided the search will match any species. Default is 'All'.
            As a first pass, the molecule will be searched for with a direct
            string match.  If no string match is found, a regular expression
            match is attempted.  Note that if the molecule name regex contains
            parentheses, they must be escaped.  For example, 'H2C(CN)2.*' must be
            specified as 'H2C\\(CN\\)2.*'  (but because of the first-attempt
            full-string matching, 'H2C(CN)2' will match that molecule
            successfully).

        temperature_for_intensity : float
            The temperature to use when computing the intensity Smu^2.  Set
            to 300 by default for compatibility with JPL and the native
            catalog format, which defaults to 300.
            ** If temperature is set to zero, the return value in this column
            will be the Einstein A value **

        flags : int, optional
            Regular expression flags. Default is set to 0

        parse_name_locally : bool, optional
            When set to True it allows the method to parse through catdir.cat
            (see `get_species_table`) in order to match the regex inputted in
            the molecule parameter and request the corresponding tags of the
            matches instead. Default is set to False

        get_query_payload : bool, optional
            When set to `True` the method should return the HTTP request
            parameters as a dict. Default value is set to False

        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.

        Examples
        --------
        >>> table = CDMS.query_lines(min_frequency=100*u.GHz,
        ...                          max_frequency=110*u.GHz,
        ...                          min_strength=-500,
        ...                          molecule="018505 H2O+") # doctest: +REMOTE_DATA
        >>> print(table) # doctest: +SKIP
            FREQ     ERR   LGINT   DR   ELO    GUP  TAG  QNFMT  Ju  Ku  vu  Jl  Kl  vl      F      name
            MHz      MHz  MHz nm2      1 / cm
        ----------- ----- ------- --- -------- --- ----- ----- --- --- --- --- --- --- ----------- ----
        103614.4941 2.237 -4.1826   3 202.8941   8 18505  2356   4   1   4   4   0   4 3 2 1 3 0 3 H2O+
        107814.8763 148.6 -5.4438   3 878.1191  12 18505  2356   6   5   1   7   1   6 7 4 4 8 1 7 H2O+
        107822.3481 148.6 -5.3846   3 878.1178  14 18505  2356   6   5   1   7   1   7 7 4 4 8 1 8 H2O+
        107830.1216 148.6 -5.3256   3 878.1164  16 18505  2356   6   5   1   7   1   8 7 4 4 8 1 9 H2O+
        """
        # first initialize the dictionary of HTTP request parameters
        payload = dict()

        if min_frequency is not None and max_frequency is not None:
            # allow setting payload without having *ANY* valid frequencies set
            min_frequency = min_frequency.to(u.GHz, u.spectral())
            max_frequency = max_frequency.to(u.GHz, u.spectral())
            if min_frequency > max_frequency:
                raise InvalidQueryError("min_frequency must be less than max_frequency")

            payload['MinNu'] = min_frequency.value
            payload['MaxNu'] = max_frequency.value

        payload['UnitNu'] = 'GHz'
        payload['StrLim'] = min_strength
        payload['temp'] = temperature_for_intensity
        payload['logscale'] = 'yes'
        payload['mol_sort_query'] = 'tag'
        payload['sort'] = 'frequency'
        payload['output'] = 'text'
        payload['but_action'] = 'Submit'

        # changes interpretation of query
        self._last_query_temperature = temperature_for_intensity

        if molecule is not None:
            if parse_name_locally:
                self.lookup_ids = build_lookup()
                luts = self.lookup_ids.find(molecule, flags)
                if len(luts) == 0:
                    raise InvalidQueryError('No matching species found. Please '
                                            'refine your search or read the Docs '
                                            'for pointers on how to search.')
                payload['Molecules'] = tuple(f"{val:06d} {key}"
                                             for key, val in luts.items())[0]
            else:
                payload['Molecules'] = molecule

        payload = list(payload.items())

        if get_query_payload:
            return payload
        # BaseQuery classes come with a _request method that includes a
        # built-in caching system
        response = self._request(method='POST', url=self.URL, data=payload,
                                 timeout=self.TIMEOUT, cache=cache)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        ok = False
        urls = [x.attrs['src'] for x in soup.findAll('frame',)]
        for url in urls:
            if 'tab' in url and 'head' not in url:
                ok = True
                break
        if not ok:
            raise EmptyResponseError("Did not find table in response")

        baseurl = self.URL.split('cgi-bin')[0]
        fullurl = f'{baseurl}/{url}'

        response2 = self._request(method='GET', url=fullurl,
                                  timeout=self.TIMEOUT, cache=cache)

        return response2

    def _parse_result(self, response, *, verbose=False):
        """
        Parse a response into an `~astropy.table.Table`

        The catalog data files are composed of fixed-width card images, with
        one card image per spectral line.  The format of each card image is
        similar to the JPL version:
        FREQ, ERR, LGINT, DR,  ELO, GUP, TAG, QNFMT,  QN',  QN"
        (F13.4,F8.4, F8.4,  I2,F10.4,  I3,  I7,    I4,  6I2,  6I2)
        but the formats are somewhat different and are encoded below.
        The first several entries are the same, but more detail is appended at
        the end of the line

        FREQ:  Frequency of the line in MHz.
        ERR:   Estimated or experimental error of FREQ in MHz.
        LGINT: Base 10 logarithm of the integrated intensity in units of nm^2 MHz at
            300 K.

        DR:    Degrees of freedom in the rotational partition function (0 for atoms,
            2 for linear molecules, and 3 for nonlinear molecules).

        ELO:   Lower state energy in cm^{-1} relative to the ground state.
        GUP:   Upper state degeneracy.
        MOLWT: The first half of the molecular weight tag, which is the mass in atomic
               mass units (Daltons).
        TAG:   Species tag or molecular identifier.  This only includes the
               last 3 digits of the CDMS tag

        A negative value of MOLWT flags that the line frequency has been
        measured in the laboratory.  We record this boolean in the 'Lab'
        column.  ERR is the reported experimental error.

        QNFMT: Identifies the format of the quantum numbers
        Ju/Ku/vu and Jl/Kl/vl are the upper/lower QNs
        F: the hyperfine lines
        name: molecule name

        The full detailed description is here:
        https://cdms.astro.uni-koeln.de/classic/predictions/description.html#description
        """

        if 'Zero lines were found' in response.text:
            raise EmptyResponseError(f"Response was empty; message was '{response.text}'.")

        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.find('pre').text

        starts = {'FREQ': 0,
                  'ERR': 14,
                  'LGINT': 25,
                  'DR': 36,
                  'ELO': 38,
                  'GUP': 47,
                  'MOLWT': 51,
                  'TAG': 54,
                  'QNFMT': 58,
                  'Ju': 61,
                  'Ku': 63,
                  'vu': 65,
                  'F1u': 67,
                  'F2u': 69,
                  'F3u': 71,
                  'Jl': 73,
                  'Kl': 75,
                  'vl': 77,
                  'F1l': 79,
                  'F2l': 81,
                  'F3l': 83,
                  'name': 89}

        result = ascii.read(text, header_start=None, data_start=0,
                            comment=r'THIS|^\s{12,14}\d{4,6}.*',
                            names=list(starts.keys()),
                            col_starts=list(starts.values()),
                            format='fixed_width', fast_reader=False)

        result['FREQ'].unit = u.MHz
        result['ERR'].unit = u.MHz

        result['Lab'] = result['MOLWT'] < 0
        result['MOLWT'] = np.abs(result['MOLWT'])
        result['MOLWT'].unit = u.Da

        fix_keys = ['GUP']
        for suf in 'ul':
            for qn in ('J', 'v', 'K', 'F1', 'F2', 'F3'):
                qnind = qn+suf
                fix_keys.append(qnind)
        for key in fix_keys:
            if result[key].dtype != int:
                intcol = np.array(list(map(parse_letternumber, result[key])),
                                  dtype=int)
                result[key] = intcol

        # if there is a crash at this step, something went wrong with the query
        # and the _last_query_temperature was not set.  This shouldn't ever
        # happen, but, well, I anticipate it will.
        if self._last_query_temperature == 0:
            result.rename_column('LGINT', 'LGAIJ')
            result['LGAIJ'].unit = u.s**-1
        else:
            result['LGINT'].unit = u.nm**2 * u.MHz
        result['ELO'].unit = u.cm**(-1)

        return result

    def get_species_table(self, *, catfile='catdir.cat', use_cached=True,
                          catfile_url=conf.catfile_url):
        """
        A directory of the catalog is found in a file called 'catdir.cat.'

        The table is derived from https://cdms.astro.uni-koeln.de/classic/entries/partition_function.html

        Parameters
        ----------
        catfile : str, name of file, default 'catdir.cat'
            The catalog file, installed locally along with the package

        Returns
        -------
        Table: `~astropy.table.Table`
            | tag : The species tag or molecular identifier.
            | molecule : An ASCII name for the species.
            | #line : The number of lines in the catalog.
            | lg(Q(n)) : A seven-element vector containing the base 10 logarithm of
                the partition function.

        """

        if use_cached:
            result = ascii.read(data_path(catfile), format='fixed_width', delimiter='|')
        else:
            result = retrieve_catfile(catfile_url)

        meta = {'lg(Q(1000))': 1000.0,
                'lg(Q(500))': 500.0,
                'lg(Q(300))': 300.0,
                'lg(Q(225))': 225.0,
                'lg(Q(150))': 150.0,
                'lg(Q(75))': 75.0,
                'lg(Q(37.5))': 37.5,
                'lg(Q(18.75))': 18.75,
                'lg(Q(9.375))': 9.375,
                'lg(Q(5.000))': 5.0,
                'lg(Q(2.725))': 2.725}

        def tryfloat(x):
            try:
                return float(x)
            except ValueError:
                return np.nan

        for key in meta:
            result[key].meta = {'Temperature (K)': meta[key]}
            result[key] = np.array([tryfloat(val) for val in result[key]])

        result.meta = {'Temperature (K)': [1000., 500., 300., 225., 150., 75.,
                                           37.5, 18.75, 9.375, 5., 2.725]}

        return result


CDMS = CDMSClass()


def parse_letternumber(st):
    """
    Parse CDMS's two-letter QNs

    From the CDMS docs:
    "Exactly two characters are available for each quantum number. Therefore, half
    integer quanta are rounded up ! In addition, capital letters are used to
    indicate quantum numbers larger than 99. E. g. A0 is 100, Z9 is 359. Small
    types are used to signal corresponding negative quantum numbers."
    """
    asc = string.ascii_lowercase
    ASC = string.ascii_uppercase
    newst = ''.join(['-' + str(asc.index(x)+10) if x in asc else
                     str(ASC.index(x)+10) if x in ASC else
                     x for x in st])
    return int(newst)


class Lookuptable(dict):

    def find(self, st, flags):
        """
        Search dictionary keys for a regex match to string s

        Parameters
        ----------
        s : str
            String to compile as a regular expression
            Can be entered non-specific for broader results
            ('H2O' yields 'H2O' but will also yield 'HCCCH2OD')
            or as the specific desired regular expression for
            catered results, for example: ('H2O$' yields only 'H2O')

        flags : int
            Regular expression flags.

        Returns
        -------
        The list of values corresponding to the matches

        """

        out = {}

        for kk, vv in self.items():
            # note that the string-match attempt here differs from the jplspec
            # implementation
            match = (st in kk) or re.search(st, str(kk), flags=flags)
            if match:
                out[kk] = vv

        return out


def build_lookup():

    result = CDMS.get_species_table()
    keys = list(result['molecule'][:])  # convert NAME column to list
    values = list(result['tag'][:])  # convert TAG column to list
    dictionary = dict(zip(keys, values))  # make k,v dictionary
    lookuptable = Lookuptable(dictionary)  # apply the class above

    return lookuptable


def retrieve_catfile(url='https://cdms.astro.uni-koeln.de/classic/entries/partition_function.html'):
    """
    Simple retrieve index function
    """
    response = requests.get(url)
    response.raise_for_status()
    tbl = ascii.read(response.text, header_start=None, data_start=15, data_end=-5,
                     names=['tag', 'molecule', '#lines', 'lg(Q(1000))', 'lg(Q(500))', 'lg(Q(300))', 'lg(Q(225))',
                            'lg(Q(150))', 'lg(Q(75))', 'lg(Q(37.5))', 'lg(Q(18.75))', 'lg(Q(9.375))', 'lg(Q(5.000))',
                            'lg(Q(2.725))'],
                     col_starts=(0, 7, 34, 41, 53, 66, 79, 92, 106, 117, 131, 145, 159, 173),
                     format='fixed_width', delimiter=' ')
    return tbl
