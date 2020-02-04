# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import warnings

import astropy.units as u
from astropy.io import ascii
from ..query import BaseQuery
from ..utils import async_to_sync
# import configurable items declared in __init__.py
from . import conf
from . import lookup_table


__all__ = ['JPLSpec', 'JPLSpecClass']


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@async_to_sync
class JPLSpecClass(BaseQuery):

    # use the Configuration Items imported from __init__.py
    URL = conf.server
    TIMEOUT = conf.timeout

    def query_lines_async(self, min_frequency, max_frequency,
                          min_strength=-500,
                          max_lines=2000, molecule='All', flags=0,
                          parse_name_locally=False,
                          get_query_payload=False, cache=True):
        """
        Creates an HTTP POST request based on the desired parameters and
        returns a response.

        Parameters
        ----------
        min_frequency : `astropy.units`
            Minimum frequency (or any spectral() equivalent)
        max_frequency : `astropy.units`
            Maximum frequency (or any spectral() equivalent)
        min_strength : int, optional
            Minimum strength in catalog units, the default is -500
        max_lines :  int, optional
            Maximum number of lines to query, the default is 2000.
            The most the query allows is 100000

        molecule : list, string of regex if parse_name_locally=True, optional
            Identifiers of the molecules to search for. If this parameter
            is not provided the search will match any species. Default is 'All'.

        flags : int, optional
            Regular expression flags. Default is set to 0

        parse_name_locally : bool, optional
            When set to True it allows the method to parse through catdir.cat
            in order to match the regex inputted in the molecule parameter
            and request the corresponding tags of the matches instead. Default
            is set to False

        get_query_payload : bool, optional
            When set to `True` the method should return the HTTP request
            parameters as a dict. Default value is set to False

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.

        Examples
        --------
        >>> table = JPLSpec.query_lines(min_frequency=100*u.GHz,
        ...                             max_frequency=200*u.GHz,
        ...                             min_strength=-500, molecule=18003) # doctest: +REMOTE_DATA
        >>> print(table) # doctest: +SKIP
            FREQ     ERR    LGINT    DR    ELO    GUP  TAG   QNFMT   QN'      QN"
        ----------- ------ -------- --- --------- --- ------ ----- -------- --------
        115542.5692 0.6588 -13.2595   3 4606.1683  35  18003  1404 17 810 0 18 513 0
         139614.293   0.15  -9.3636   3 3080.1788  87 -18003  1404 14 6 9 0 15 312 0
         177317.068   0.15 -10.3413   3 3437.2774  31 -18003  1404 15 610 0 16 313 0
         183310.087  0.001  -3.6463   3  136.1639   7 -18003  1404  3 1 3 0  2 2 0 0
        """
        # first initialize the dictionary of HTTP request parameters
        payload = dict()

        if min_frequency is not None and max_frequency is not None:
            # allow setting payload without having *ANY* valid frequencies set
            min_frequency = min_frequency.to(u.GHz, u.spectral())
            max_frequency = max_frequency.to(u.GHz, u.spectral())
            if min_frequency > max_frequency:
                min_frequency, max_frequency = max_frequency, min_frequency

            payload['MinNu'] = min_frequency.value
            payload['MaxNu'] = max_frequency.value

        if max_lines is not None:
            payload['MaxLines'] = max_lines

        payload['UnitNu'] = 'GHz'
        payload['StrLim'] = min_strength

        if molecule is not None:
            if parse_name_locally:
                self.lookup_ids = build_lookup()
                payload['Mol'] = tuple(self.lookup_ids.find(molecule, flags))
                if len(molecule) == 0:
                    raise ValueError('No matching species found. Please\
                                     refine your search or read the Docs\
                                     for pointers on how to search.')
            else:
                payload['Mol'] = molecule

        self.maxlines = max_lines

        payload = list(payload.items())

        if get_query_payload:
            return payload
        # BaseQuery classes come with a _request method that includes a
        # built-in caching system
        response = self._request(method='POST', url=self.URL, data=payload,
                                 timeout=self.TIMEOUT, cache=cache)

        return response

    def _parse_result(self, response, verbose=False):
        """
        Parse a response into an `~astropy.table.Table`

        The catalog data files are composed of 80-character card images, with
        one card image per spectral line.  The format of each card image is:
        FREQ, ERR, LGINT, DR,  ELO, GUP, TAG, QNFMT,  QN',  QN"
        (F13.4,F8.4, F8.4,  I2,F10.4,  I3,  I7,    I4,  6I2,  6I2)

        FREQ:  Frequency of the line in MHz.
        ERR:   Estimated or experimental error of FREQ in MHz.
        LGINT: Base 10 logarithm of the integrated intensity in units of nm^2 MHz at
            300 K.

        DR:    Degrees of freedom in the rotational partition function (0 for atoms,
            2 for linear molecules, and 3 for nonlinear molecules).

        ELO:   Lower state energy in cm^{-1} relative to the ground state.
        GUP:   Upper state degeneracy.
        TAG:   Species tag or molecular identifier.
            A negative value flags that the line frequency has
            been measured in the laboratory.  The absolute value of TAG is then the
            species tag and ERR is the reported experimental error.  The three most
            significant digits of the species tag are coded as the mass number of
            the species.

        QNFMT: Identifies the format of the quantum numbers
        QN':   Quantum numbers for the upper state.
        QN":   Quantum numbers for the lower state.
        """

        # data starts at 0 since regex was applied
        # Warning for a result with more than 1000 lines:
        # THIS form is currently limited to 1000 lines.
        result = ascii.read(response.text, header_start=None, data_start=0,
                            comment=r'THIS|^\s{12,14}\d{4,6}.*',
                            names=('FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP',
                                   'TAG', 'QNFMT', 'QN\'', 'QN"'),
                            col_starts=(0, 13, 21, 29, 31, 41, 44, 51, 55, 67),
                            format='fixed_width', fast_reader=False)

        if len(result) > self.maxlines:
            warnings.warn("This form is currently limited to {0} lines."
                          "Please limit your search.".format(self.maxlines))

        result['FREQ'].unit = u.MHz
        result['ERR'].unit = u.MHz
        result['LGINT'].unit = u.nm**2 * u.MHz
        result['ELO'].unit = u.cm**(-1)

        return result

    def get_species_table(self, catfile='catdir.cat'):
        """
        A directory of the catalog is found in a file called 'catdir.cat.'
        Each element of this directory is an 80-character record with the
        following format:

        | TAG,  NAME, NLINE,  QLOG,  VER
        | (I6,X, A13, I6, 7F7.4,  I2)

        Parameters
        -----------
        catfile : str, name of file, default 'catdir.cat'
            The catalog file, installed locally along with the package

        Returns
        --------
        Table: `~astropy.table.Table`
            | TAG : The species tag or molecular identifier.
            | NAME : An ASCII name for the species.
            | NLINE : The number of lines in the catalog.
            | QLOG : A seven-element vector containing the base 10 logarithm of
                the partition function for temperatures of 300 K, 225 K, 150 K,
                75 K, 37.5 K, 18.75 K, and 9.375 K, respectively.
            | VER : The version of the calculation for this species in the catalog.
                The version number is followed by * if the entry is newer than the
                last edition of the catalog.

        """

        result = ascii.read(data_path(catfile), header_start=None, data_start=0,
                            names=('TAG', 'NAME', 'NLINE', 'QLOG1', 'QLOG2',
                                   'QLOG3', 'QLOG4', 'QLOG5', 'QLOG6',
                                   'QLOG7', 'VER'),
                            col_starts=(0, 6, 20, 26, 33, 40, 47, 54, 61,
                                        68, 75),
                            format='fixed_width', fast_reader=False)

        # store the corresponding temperatures as metadata
        result['QLOG1'].meta = {'Temperature (K)': 300}
        result['QLOG2'].meta = {'Temperature (K)': 225}
        result['QLOG3'].meta = {'Temperature (K)': 150}
        result['QLOG4'].meta = {'Temperature (K)': 75}
        result['QLOG5'].meta = {'Temperature (K)': 37.5}
        result['QLOG6'].meta = {'Temperature (K)': 18.75}
        result['QLOG7'].meta = {'Temperature (K)': 9.375}
        result.meta = {'Temperature (K)': [300, 225, 150, 75, 37.5, 18.5,
                                           9.375]}

        return result


JPLSpec = JPLSpecClass()


def build_lookup():

    result = JPLSpec.get_species_table()
    keys = list(result[1][:])  # convert NAME column to list
    values = list(result[0][:])  # convert TAG column to list
    dictionary = dict(zip(keys, values))  # make k,v dictionary
    lookuptable = lookup_table.Lookuptable(dictionary)  # apply the class above

    return lookuptable
