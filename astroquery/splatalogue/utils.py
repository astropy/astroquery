# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Utilities for working with Splatalogue query results
"""
from bs4 import BeautifulSoup


def clean_column_headings(table, *, renaming_dict={}):
    """
    Rename column headings to shorter version that are easier for display
    on-screen / at the terminal

    As of March 2024, the default column names are all valid and no longer need
    renaming.
    """

    for key in renaming_dict:
        if key in table.colnames:
            table.rename_column(key, renaming_dict[key])

    return table


def try_clean(row):
    if row:
        return BeautifulSoup(row, features='html5lib').text


def clean_columns(table):
    """
    Remove HTML tags in table columns

    (modifies table inplace)
    """
    for col in table.colnames:
        # check for any html tag
        if isinstance(table[col][0], str) and '<' in table[col][0]:
            table[col] = [
                try_clean(row)
                for row in table[col]
            ]


def minimize_table(table, *, columns=['name', 'chemical_name',
                                      'resolved_QNs',
                                      'orderedfreq',
                                      'aij',
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
    from .core import colname_mapping_feb2024

    clean_columns(table)

    columns = [colname_mapping_feb2024[c] if c in colname_mapping_feb2024 else c
               for c in columns]

    table = table[columns]

    if merge:
        table.rename_column('orderedfreq', 'Freq')
    if clean:
        table = clean_column_headings(table)

    return table
