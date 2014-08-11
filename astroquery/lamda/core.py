# Licensed under a 3-clause BSD style license - see LICENSE.rst
# TODO rovib in H2O has wrong format for header
import requests
import numpy as np
from astropy.table import Table

__all__ = ['query', 'print_mols']

# should skip only if remote_data = False
__doctest_skip__ = ['query']

url = "http://home.strw.leidenuniv.nl/~moldata/datafiles/{0}.dat"
mols = {
    # Atoms
    'C': ['catom'],
    'C+': ['c+', 'c+@uv'],
    'O': ['oatom'],
    # Molecules
    'CO': ['co', '13co', 'c17o', 'c18o', 'co@neufold'],
    'CS': ['cs@xpol', '13cs@xpol', 'c34s@xpol'],
    'HCl': ['hcl', 'hcl@hfs'],
    'OCS': ['ocs@xpol'],
    'SO': ['so'],
    'SO2': ['so2@xpol'],
    'SiO': ['sio', '29sio'],
    'SiS': ['sis@xpol'],
    'SiC2': ['o-sic2'],
    'HCO+': ['hco+@xpol', 'h13co+@xpol', 'hc17o+@xpol', 'hc18o+@xpol',
             'dco+@xpol'],
    'N2H+': ['n2h+@xpol', 'n2h+_hfs'],
    'HCS+': ['hcs+@xpol'],
    'HC3N': ['hc3n'],
    'HCN': ['hcn', 'hcn@xpol', 'hcn@hfs', 'h13cn@xpol', 'hc15n@xpol'],
    'HNC': ['hnc'],
    'C3H2': ['p-c3h2', 'o-c3h2'],
    'H2O': ['ph2o@daniel', 'oh2o@daniel', 'ph2o@rovib', 'oh2o@rovib'],
    'H2CO': ['p-h2co', 'o-h2co'],
    'OH': ['oh', 'oh@hfs'],
    'CH3OH': ['e-ch3oh', 'a-ch3oh'],
    'NH3': ['p-nh3', 'o-nh3'],
    'HDO': ['hdo'],
    'H3O+': ['p-h3o+', 'o-h3o+'],
    'HNCO': ['hnco'],
    'NO': ['no'],
    'CN': ['cn'],
    'CH3CN': ['ch3cn'],
    'O2': ['o2'],
    'HF': ['hf']
}
query_types = {
    'erg_levels': '!NUMBER OF ENERGY LEVELS',
    'rad_trans': '!NUMBER OF RADIATIVE TRANSITIONS',
    'coll_rates': '!COLLISIONS BETWEEN'
}


def print_mols():
    """
    Print molecule names available for query.
    """
    for mol_family in mols.keys():
        print('-- {0} :'.format(mol_family))
        print(mols[mol_family], '\n')


def query(mol, query_type=None, coll_partner_index=0, return_datafile=False):
    """
    Query the LAMDA database.

    Parameters
    ----------
    mol : string
        Molecule or atom designation. For a list of valid designations see
        the :meth:`print_mols` method.
    query_type : string
        Query type to execute. Valid options:
            ``'erg_levels'`` -> Energy Levels
            ``'rad_trans'``  -> Radiative transitions
            ``'coll_rates'`` -> Collisional rates
    coll_partner_index : number, default 0
        If collisional rates are queried, set the index of the collisional
        partner to the order found in the LAMDA datafile. If no index is
        specified, the first collsional partner is taken.

    Returns
    -------
    table : `~astropy.table.Table`

    Examples
    --------
    >>> from astroquery import lamda
    >>> t = lamda.query(mol='co', query_type='erg_levels')
    >>> t.pprint()
    LEVEL ENERGIES(cm^-1) WEIGHT  J
    ----- --------------- ------ ---
        2     3.845033413    3.0   1
        3    11.534919938    5.0   2
      ...             ...    ... ...
    """
    if query_type not in query_types.keys() and not return_datafile:
        raise ValueError("Query type must be one of " + ",".join(query_type.keys()))
    # Send HTTP request to open URL
    datafile = [s.strip() for s in requests.get(url.format(mol)).text.splitlines()]
    if return_datafile:
        return datafile
    # Parse datafile string list and return a table
    table = _parse_datafile(datafile, query_type=query_type,
                            coll_partner_index=coll_partner_index)
    return table


def _parse_datafile(datafile, query_type, coll_partner_index=0):
    """
    Parse datafile according to query type and return a Table instance of
    the data.

    Parameters
    ----------
    datafile : `np.ndarray`
        Raw data array pulled from LAMDA
    query_type : string
        Valid query_type in ['coll_rates', 'rad_trans', 'erg_levels']
    coll_partner_index : number, default 0
        Collision partner index, order of partner in file

    Returns
    -------
    table : `~astropy.table.Table`
    """
    query_identifier = query_types[query_type]
    if query_type == 'coll_rates':
        i = coll_partner_index
    else:
        i = 0
    # Select lines that contain the query identifier
    # np.in1d does not work in np < 1.7
    sections = np.argwhere([query_identifier in line for line in datafile])
    if len(sections) == 0:
        raise Exception('Query data not found in file.')
    start_index = sections[i][0]
    # Select rows and columns from the raw datafile list
    data, col_names = _select_data(datafile, start_index,
                                   query_type=query_type)
    # Convert columns with string data types to floats if possible
    col_dtypes = _check_dtypes(data)
    table = Table(data, names=col_names, dtype=col_dtypes)
    return table


def _select_data(data, i, query_type):
    """
    Select only data relevant to a specific query type in the raw data
    array and pick out column names from context.

    Parameters
    ----------
    data : `np.ndarray`
        Raw data array pulled from LAMDA.
    i : number
        Row index to start reading from data in.
    query_type : string
        Valid query_type in ['coll_rates', 'rad_trans', 'erg_levels'].

    Returns
    -------
    data : `np.array`
        Data for query_type
    col_names : list
        Column name list
    """
    # LAMDA datafiles have regular formatting, so the index and an "index
    # offset" are used to retrieve the row data.
    if query_type == 'erg_levels':
        num_erg_levels = int(data[i + 1])
        col_names = [s.strip() for s in data[i + 2][1:].split('+')]
        erg_levels = [data[i + 3 + j].split() for j in range(0, num_erg_levels)]
        return np.array(erg_levels), col_names
    elif query_type == 'rad_trans':
        num_trans = int(data[i + 1])
        col_names = [s.strip() for s in data[i + 2][1:].split('+')]
        rad_trans = [data[i + 3 + j].split() for j in range(0, num_trans)]
        return np.array(rad_trans), col_names
    elif query_type == 'coll_rates':
        num_coll_trans = int(data[i + 3])
        coll_temps = data[i + 7].split()
        coll_trans = [data[i + 9 + j].split() for j in range(0, num_coll_trans)]
        col_names = ['TRANS', 'UP', 'LOW'] + coll_temps
        return np.array(coll_trans), col_names
    else:
        raise ValueError('Unknown query type.')


def _check_dtypes(data):
    """
    Check the data types of each column. If a column cannot be converted to
    a float, a string is used as a fall-back.

    Parameters
    ----------
    data : `np.ndarray`

    Returns
    -------
    dtypes : list
        List of a dtypes for each column in data
    """
    dtypes = []
    for i in range(data.shape[1]):
        try:
            data[:, i].astype('float')
            dtypes.append('<f8')
        except ValueError:
            dtypes.append('|S14')
    return dtypes


if __name__ == "__main__":
    pass
