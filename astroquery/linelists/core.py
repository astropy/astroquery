# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Base classes and common utilities for linelist queries (JPLSpec, CDMS, etc.)
"""
import numpy as np
import string
import astropy.units as u
from astropy.io import ascii
from astroquery.exceptions import EmptyResponseError
from astroquery import log
from astropy import table


__all__ = ['LineListClass', 'parse_letternumber']


def parse_letternumber(st):
    """
    Parse CDMS's two-letter QNs into integers.

    Masked values are converted to -999999.

    From the CDMS docs:
    "Exactly two characters are available for each quantum number. Therefore, half
    integer quanta are rounded up ! In addition, capital letters are used to
    indicate quantum numbers larger than 99. E. g. A0 is 100, Z9 is 359. Lower case characters
    are used similarly to signal negative quantum numbers smaller than –9. e. g., a0 is –10, b0 is –20, etc."
    """
    if np.ma.is_masked(st):
        return -999999

    asc = string.ascii_lowercase
    ASC = string.ascii_uppercase
    newst = ''.join(['-' + str((asc.index(x)+1)) if x in asc else
                     str((ASC.index(x)+10)) if x in ASC else
                     x for x in st])
    return int(newst)


class LineListClass:
    """
    Base class for line list catalog queries (JPL, CDMS, etc.)

    This class provides common functionality for parsing catalog files
    and retrieving molecule data from spectroscopic databases.
    """

    def get_molecule(self, molecule_id, *, cache=True, **kwargs):
        """
        Retrieve the whole molecule table for a given molecule id from the catalog.

        This method should be overridden by subclasses to implement
        catalog-specific behavior, but provides common structure.

        Parameters
        ----------
        molecule_id : int or str
            The molecule tag/identifier. Can be an integer or a string.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
        **kwargs : dict
            Additional keyword arguments specific to the subclass implementation.

        Returns
        -------
        Table : `~astropy.table.Table`
            Table containing all spectral lines for the requested molecule.
        """
        raise NotImplementedError("Subclasses must implement get_molecule()")

    def _parse_cat(self, response_or_text, *, verbose=False):
        """
        Parse a catalog file response into an `~astropy.table.Table`.

        The catalog data files are typically composed of 80-character card images,
        with one card image per spectral line. This method provides the common
        parsing logic, but can be overridden by subclasses for catalog-specific formats.

        Parameters
        ----------
        response_or_text : `requests.Response` or str
            The HTTP response from the catalog file request or the text content.
        verbose : bool, optional
            If True, print additional debugging information.

        Returns
        -------
        Table : `~astropy.table.Table`
            Parsed catalog data.
        """
        raise NotImplementedError("Subclasses must implement _parse_cat()")

    def _parse_cat_jpl_format(self, text, *, verbose=False):
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

        # parse QNs
        n_qns = result['QNFMT'] % 10
        tables = [result[result['QNFMT'] % 10 == qq] for qq in set(n_qns)]

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

        for tbl in tables:
            n_qns = tbl['QNFMT'][0] % 10
            if n_qns > 1:
                if tbl['QN\''].dtype.kind == 'U':  # Unicode
                    qnlen = tbl['QN\''].dtype.itemsize // 4
                elif tbl['QN\''].dtype.kind == 'S':  # Byte string
                    qnlen = tbl['QN\''].dtype.itemsize
                else:
                    raise TypeError("Unexpected dtype for QN' column")
                if qnlen % 2 == 1:
                    # entries are always even, but the leftmost entry can get truncated by the reader
                    qnlen += 1
                for ii in range(n_qns):
                    qn_col = f'QN\'{ii+1}'
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
                tbl['QN\''] = np.array(tbl['QN\''], dtype=int)
                tbl['QN"'] = np.array(tbl['QN"'], dtype=int)

        result = table.vstack(tables)


        # Add laboratory measurement flag
        # A negative TAG value indicates laboratory-measured frequency
        result['Lab'] = result['TAG'] < 0
        # Convert TAG to absolute value
        result['TAG'] = abs(result['TAG'])

        return result

    def _parse_cat_cdms_format(self, text, *, verbose=False):
        """
        Parse a CDMS-format catalog file into an `~astropy.table.Table`.

        The catalog data files are composed of 80-character card images.
        Format: [F13.4, 2F8.4, I2, F10.4, I3, I7, I4, 12I2]:
        FREQ, ERR, LGINT, DR, ELO, GUP, TAG, QNFMT, QN

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
        # Column start positions
        starts = {'FREQ': 0,
                  'ERR': 14,
                  'LGINT': 22,
                  'DR': 30,
                  'ELO': 32,
                  'GUP': 42,
                  'TAG': 44,
                  'QNFMT': 51,
                  'Q1': 55,
                  'Q2': 57,
                  'Q3': 59,
                  'Q4': 61,
                  'Q5': 63,
                  'Q6': 65,
                  'Q7': 67,
                  'Q8': 69,
                  'Q9': 71,
                  'Q10': 73,
                  'Q11': 75,
                  'Q12': 77,
                  'Q13': 79,
                  'Q14': 81,
                  }

        result = ascii.read(text, header_start=None, data_start=0,
                            comment=r'THIS|^\s{12,14}\d{4,6}.*',
                            names=list(starts.keys()),
                            col_starts=list(starts.values()),
                            format='fixed_width', fast_reader=False)

        # Ensure TAG is integer type for computation
        # int truncates - which is what we want
        result['TAG'] = result['TAG'].astype(int)
        result['MOLWT'] = [int(x/1e3) for x in result['TAG']]

        result['FREQ'].unit = u.MHz
        result['ERR'].unit = u.MHz

        result['Lab'] = result['MOLWT'] < 0
        result['MOLWT'] = np.abs(result['MOLWT'])
        result['MOLWT'].unit = u.Da

        fix_keys = ['GUP']
        for qn in (f'Q{ii}' for ii in range(1, 15)):
            fix_keys.append(qn)
        log.debug(f"fix_keys: {fix_keys} should include Q1, Q2, ..., Q14 and GUP")
        for key in fix_keys:
            if not np.issubdtype(result[key].dtype, np.integer):
                intcol = np.array(list(map(parse_letternumber, result[key])),
                                  dtype=int)
                if any(intcol == -999999):
                    intcol = np.ma.masked_where(intcol == -999999, intcol)
                result[key] = intcol
                if not np.issubdtype(result[key].dtype, np.integer):
                    raise ValueError(f"Failed to parse {key} as integer")

        result['LGINT'].unit = u.nm**2 * u.MHz
        result['ELO'].unit = u.cm**(-1)

        return result
