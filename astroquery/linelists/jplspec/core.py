# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import warnings

import astropy.units as u
import numpy as np
from astropy.io import ascii
from astropy import table
from astroquery.query import BaseQuery
from astroquery.linelists.core import parse_letternumber, parse_molid
# import configurable items declared in __init__.py
from astroquery.linelists.jplspec import conf, lookup_table
from astroquery.exceptions import EmptyResponseError, InvalidQueryError
from astroquery.utils import process_asyncs
from urllib.parse import parse_qs


__all__ = ['JPLSpec', 'JPLSpecClass']


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class JPLSpecClass(BaseQuery):

    # use the Configuration Items imported from __init__.py
    URL = conf.server
    TIMEOUT = conf.timeout

    def __init__(self):
        super().__init__()

    def query_lines_async(self, min_frequency, max_frequency, *,
                          min_strength=-500,
                          max_lines=2000, molecule='All', flags=0,
                          parse_name_locally=False,
                          get_query_payload=False, cache=True
                          ):
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
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

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
                payload['Mol'] = tuple(self.lookup_ids.find(molecule, flags).values())
                if len(molecule) == 0:
                    raise InvalidQueryError('No matching species found. Please '
                                            'refine your search or read the Docs '
                                            'for pointers on how to search.')
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
        response.raise_for_status()

        return response

    def query_lines(self, min_frequency, max_frequency, *,
                    min_strength=-500,
                    max_lines=2000, molecule='All', flags=0,
                    parse_name_locally=False,
                    get_query_payload=False,
                    fallback_to_getmolecule=True,
                    cache=True):
        """
        Query the JPLSpec service for spectral lines.

        This is a synchronous version of `query_lines_async`.
        See `query_lines_async` for full parameter documentation.

        fallback_to_getmolecule is a unique parameter to this method that
        governs whether `get_molecule` will be used when no results are returned
        by the query service.  This workaround is needed while JPLSpec's query
        tool is broken.
        """
        response = self.query_lines_async(min_frequency=min_frequency,
                                          max_frequency=max_frequency,
                                          min_strength=min_strength,
                                          max_lines=max_lines,
                                          molecule=molecule,
                                          flags=flags,
                                          parse_name_locally=parse_name_locally,
                                          get_query_payload=get_query_payload,
                                          cache=cache)
        if get_query_payload:
            return response
        else:
            return self._parse_result(response, fallback_to_getmolecule=fallback_to_getmolecule)

    query_lines.__doc__ = process_asyncs.async_to_sync_docstr(query_lines_async.__doc__)

    def _parse_result(self, response, *, verbose=False, fallback_to_getmolecule=False):
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

        if 'Zero lines were found' in response.text:
            if fallback_to_getmolecule:
                self.lookup_ids = build_lookup()
                payload = parse_qs(response.request.body)
                tbs = [self.get_molecule(mol) for mol in payload['Mol']]
                if len(tbs) > 1:
                    mols = []
                    for tb, mol in zip(tbs, payload['Mol']):
                        tb['Name'] = self.lookup_ids.find(mol, flags=0)
                        for key in list(tb.meta.keys()):
                            tb.meta[f'{mol}_{key}'] = tb.meta.pop(key)
                        mols.append(mol)
                    tb = table.vstack(tbs)
                    tb.meta['molecule_list'] = mols
                else:
                    tb = tbs[0]
                    tb.meta['molecule_id'] = payload['Mol'][0]
                    tb.meta['molecule_name'] = self.lookup_ids.find(payload['Mol'][0], flags=0)

                return tb
            else:
                raise EmptyResponseError(f"Response was empty; message was '{response.text}'.")

        # data starts at 0 since regex was applied
        # Warning for a result with more than 1000 lines:
        # THIS form is currently limited to 1000 lines.
        result = ascii.read(response.text, header_start=None, data_start=0,
                            comment=r'THIS|^\s{12,14}\d{4,6}.*|CADDIR CATDIR',
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

    def get_species_table(self, *, catfile='catdir.cat'):
        """
        A directory of the catalog is found in a file called 'catdir.cat.'
        Each element of this directory is an 80-character record with the
        following format:

        | TAG,  NAME, NLINE,  QLOG,  VER
        | (I6,X, A13, I6, 7F7.4,  I2)

        Parameters
        ----------
        catfile : str, name of file, default 'catdir.cat'
            The catalog file, installed locally along with the package

        Returns
        -------
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

    def get_molecule(self, molecule_id, *, cache=True):
        """
        Retrieve the whole molecule table for a given molecule id from the JPL catalog.

        Parameters
        ----------
        molecule_id : int or str
            The molecule tag/identifier. Can be an integer (e.g., 18003 for H2O)
            or a zero-padded 6-character string (e.g., '018003').
        cache : bool
            Defaults to True. If set overrides global caching behavior.

        Returns
        -------
        Table : `~astropy.table.Table`
            Table containing all spectral lines for the requested molecule.

        Examples
        --------
        >>> table = JPLSpec.get_molecule(18003)  # doctest: +SKIP
        >>> print(table)  # doctest: +SKIP
        """
        molecule_str = parse_molid(molecule_id)

        # Construct the URL to the catalog file
        url = f'https://spec.jpl.nasa.gov/ftp/pub/catalog/c{molecule_str}.cat'

        # Request the catalog file
        response = self._request(method='GET', url=url,
                                 timeout=self.TIMEOUT, cache=cache)
        response.raise_for_status()

        if 'The requested URL was not found on this server.' in response.text:
            raise EmptyResponseError(f"No data found for molecule ID {molecule_id}.")

        # Parse the catalog file
        result = self._parse_cat(response)

        # Add metadata from species table
        species_table = self.get_species_table()
        # Find the row matching this molecule_id
        int_molecule_id = int(molecule_str)
        matching_rows = species_table[species_table['TAG'] == int_molecule_id]
        if len(matching_rows) > 0:
            # Add metadata as a dictionary
            result.meta = dict(zip(matching_rows.colnames, matching_rows[0]))

        return result

    def _parse_cat(self, response, *, verbose=False):
        """
        Parse a JPL-format catalog file into an `~astropy.table.Table`.

        The catalog data files are composed of 80-character card images, with
        one card image per spectral line.  The format of each card image is:
        FREQ, ERR, LGINT, DR,  ELO, GUP, TAG, QNFMT,  QN',  QN"
        (F13.4,F8.4, F8.4,  I2,F10.4,  I3,  I7,    I4,  6I2,  6I2)

        https://spec.jpl.nasa.gov/ftp/pub/catalog/doc/catintro.pdf

        Parameters
        ----------
        text : str
            The catalog file text content.
        verbose : bool, optional
            Not used currently.

        Returns
        -------
        Table : `~astropy.table.Table`
            Parsed catalog data.
        """
        text = response.text
        if 'Zero lines were found' in text or len(text.strip()) == 0:
            raise EmptyResponseError(f"Response was empty; message was '{text}'.")

        # Parse the catalog file with fixed-width format
        # Format: FREQ(13.4), ERR(8.4), LGINT(8.4), DR(2), ELO(10.4), GUP(3), TAG(7), QNFMT(4), QN'(12), QN"(12)
        result = ascii.read(text, header_start=None, data_start=0,
                            comment=r'THIS|^\s{12,14}\d{4,6}.*',
                            names=('FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP',
                                   'TAG', 'QNFMT', 'QN\'', 'QN"'),
                            col_starts=(0, 13, 21, 29, 31, 41, 44, 51, 55, 67),
                            format='fixed_width', fast_reader=False)

        # Ensure TAG is integer type
        result['TAG'] = result['TAG'].astype(int)

        # Add units
        result['FREQ'].unit = u.MHz
        result['ERR'].unit = u.MHz
        result['LGINT'].unit = u.nm**2 * u.MHz
        result['ELO'].unit = u.cm**(-1)

        # split table by qnfmt; each chunk must be separately parsed.
        qnfmts = np.unique(result['QNFMT'])
        tables = [result[result['QNFMT'] == qq] for qq in qnfmts]

        # some tables have +/-/blank entries in QNs
        # pm_is_ok should be True when the QN columns contain '+' or '-'.
        # (can't do a str check on np.integer dtype so have to filter that out first)
        pm_is_ok = ((not np.issubdtype(result["QN'"].dtype, np.integer))
                    and any(('+' in str(line) or '-' in str(line)) for line in result["QN'"]))

        def int_or_pm(st):
            try:
                return int(st)
            except ValueError:
                try:
                    return parse_letternumber(st)
                except ValueError:
                    if pm_is_ok and (st.strip() == '' or st.strip() == '+' or st.strip() == '-'):
                        return st.strip()
                    else:
                        raise ValueError(f'"{st}" is not a valid +/-/blank entry')

        # At least this molecule, NH, claims 5 QNs but has only 4
        bad_qnfmt_dict = {
            15001: 1234,
        }
        mol_tag = result['TAG'][0]

        if mol_tag in (32001,):
            raise NotImplementedError("Molecule O2 (32001) does not follow the format standard.")

        for tbl in tables:
            if mol_tag in bad_qnfmt_dict:
                n_qns = bad_qnfmt_dict[mol_tag] % 10
            else:
                n_qns = tbl['QNFMT'][0] % 10
            if n_qns > 1:
                qnlen = 2 * n_qns
                for ii in range(n_qns):
                    if tbl["QN'"].dtype in (int, np.int32, np.int64):
                        # for the case where it was already parsed as int
                        # (53005 is an example)
                        tbl[f"QN'{ii+1}"] = tbl["QN'"]
                        tbl[f'QN"{ii+1}'] = tbl['QN"']
                    else:
                        # string parsing can truncate to length=2n or 2n-1 depending
                        # on whether there are any two-digit QNs in the column
                        ind1 = ii * 2
                        ind2 = ii * 2 + 2
                        # rjust(qnlen) is needed to enforce that all strings retain their exact original shape
                        qnp = [int_or_pm(line.rjust(qnlen)[ind1: ind2].strip()) for line in tbl['QN\'']]
                        qnpp = [int_or_pm(line.rjust(qnlen)[ind1: ind2].strip()) for line in tbl['QN"']]
                        dtype = str if any('+' in str(x) for x in qnp) else int
                        tbl[f"QN'{ii+1}"] = np.array(qnp, dtype=dtype)
                        tbl[f'QN"{ii+1}'] = np.array(qnpp, dtype=dtype)
                del tbl['QN\'']
                del tbl['QN"']
            else:
                tbl['QN\''] = np.array(list(map(parse_letternumber, tbl['QN\''])), dtype=int)
                tbl['QN"'] = np.array(list(map(parse_letternumber, tbl['QN"'])), dtype=int)

        result = table.vstack(tables)

        # Add laboratory measurement flag
        # A negative TAG value indicates laboratory-measured frequency
        result['Lab'] = result['TAG'] < 0
        # Convert TAG to absolute value
        result['TAG'] = abs(result['TAG'])

        return result


JPLSpec = JPLSpecClass()


def build_lookup():

    result = JPLSpec.get_species_table()
    keys = list(result['NAME'])
    values = list(result['TAG'])
    dictionary = dict(zip(keys, values))
    lookuptable = lookup_table.Lookuptable(dictionary)  # apply the class above

    return lookuptable
