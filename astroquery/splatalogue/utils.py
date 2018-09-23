# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Utilities for working with Splatalogue query results
"""
import numpy as np
import astropy

# Remap column headings to something IPAC-compatible
column_headings_map = {'Log<sub>10</sub> (A<sub>ij</sub>)': 'log10_Aij',
                       'Resolved QNs': 'QNs',
                       'CDMS/JPL Intensity': 'CDMSJPL_Intensity',
                       'S<sub>ij</sub>': 'Sij',
                       'Freq-GHz': 'FreqGHz',
                       'Meas Freq-GHz': 'MeasFreqGHz',
                       'Lovas/AST Intensity': 'LovasAST_Intensity',
                       'E_L (cm^-1)': 'EL_percm',
                       'E_L (K)': 'EL_K',
                       'E_U (cm^-1)': 'EU_percm',
                       'E_U (K)': 'EU_K',
                       'Chemical Name': 'ChemicalName',
                       'Freq Err': 'FreqErr',
                       'Meas Freq Err': 'MeasFreqErr',
                       'Freq-GHz(rest frame,redshifted)': 'FreqGHz',
                       'Freq Err(rest frame,redshifted)': 'eFreqGHz',
                       'Meas Freq-GHz(rest frame,redshifted)': 'MeasFreqGHz',
                       'Meas Freq Err(rest frame,redshifted)': 'eMeasFreqGHz',
                       }


def clean_column_headings(table, renaming_dict=column_headings_map):
    """
    Rename column headings to shorter version that are easier for display
    on-screen / at the terminal
    """

    for key in renaming_dict:
        if key in table.colnames:
            table.rename_column(key, renaming_dict[key])

    return table


def merge_frequencies(table, prefer='measured',
                      theor_kwd='Freq-GHz(rest frame,redshifted)',
                      meas_kwd='Meas Freq-GHz(rest frame,redshifted)'):
    """
    Replace "Freq-GHz" and "Meas Freq-GHz" with a single "Freq" column.

    Parameters
    ----------
    table : table
        The Splatalogue table
    prefer: 'measured' or 'theoretical'
        Which of the two columns to prefer if there is a conflict
    """

    if prefer == 'measured':
        Freq = np.copy(table[theor_kwd])
        measmask = np.logical_not(table[meas_kwd].mask)
        Freq[measmask] = table[meas_kwd][measmask]
    elif prefer == 'theoretical':
        Freq = np.copy(table[meas_kwd])
        theomask = np.logical_not(table[theor_kwd].mask)
        Freq[measmask] = table[theor_kwd][theomask]
    else:
        raise ValueError('prefer must be one of "measured" or "theoretical"')

    index = table.index_column(theor_kwd)
    table.remove_columns([theor_kwd, meas_kwd])
    newcol = astropy.table.Column(name='Freq', data=Freq)
    table.add_column(newcol, index=index)

    return table


def minimize_table(table, columns=['Species', 'Chemical Name',
                                   'Resolved QNs',
                                   'Freq-GHz(rest frame,redshifted)',
                                   'Meas Freq-GHz(rest frame,redshifted)',
                                   'Log<sub>10</sub> (A<sub>ij</sub>)',
                                   'E_U (K)'],
                   merge=True,
                   clean=True):
    """
    Strip a table's headers and rename them to their minimalist form

    Parameters
    ----------
    table : table
        The Splatalogue table
    columns : list
        A list of column names to keep before merging and cleaning
    merge : bool
        Run merge_frequencies to get a single reported frequency for each line?
    clean_column_headings : bool
        Run clean_column_headings to shorted the headers?
    """

    table = table[columns]

    if merge:
        table = merge_frequencies(table)
    if clean:
        table = clean_column_headings(table)

    return table
