# Licensed under a 3-clause BSD style license - see LICENSE.rst
# TODO rovib in H2O has wrong format for header
import requests
import numpy as np
from astropy.table import Table
from astropy import table
from astropy import log

__all__ = ['query', 'print_mols', 'parse_lamda_datafile']

# should skip only if remote_data = False
__doctest_skip__ = ['query']

url = "http://home.strw.leidenuniv.nl/~moldata/datafiles/{0}.dat"
mols = {
    # Atoms
    'C': ['catom'],
    'C+': ['c+', 'c+@uv'],
    'O': ['oatom'],
    # Molecules
    'CO': ['co', '13co', 'c17o', 'c18o', 'co@neufeld'],
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

collider_ids = {'H2': 1,
                'PH2': 2,
                'OH2': 3,
                'E': 4,
                'H': 5,
                'HE': 6,
                'H+': 7}
collider_ids.update({v:k for k,v in list(collider_ids.items())})


def print_mols():
    """
    Print molecule names available for query.
    """
    for mol_family in mols.keys():
        print('-- {0} :'.format(mol_family))
        print(mols[mol_family], '\n')

def get_molfile(mol):
    return requests.get(url.format(mol))

def download_molfile(mol, outfilename):
    molreq = get_molfile(mol)
    with open(outfilename,'w') as f:
        f.write(molreq.text)

def query(mol, query_type=None, coll_partner_index=0, return_datafile=False):
    """
    Query the LAMDA database.

    Parameters
    ----------
    mol : string
        Molecule or atom designation. For a list of valid designations see
        the :meth:`print_mols` method.

    Returns
    -------
    Tuple of tables: ({rateid: Table, },
                      Table,
                      Table)

    Examples
    --------
    >>> from astroquery import lamda
    >>> collrates,radtransitions,enlevels = lamda.query(mol='co')
    >>> enlevels.pprint()
    LEVEL ENERGIES(cm^-1) WEIGHT  J
    ----- --------------- ------ ---
        2     3.845033413    3.0   1
        3    11.534919938    5.0   2
      ...             ...    ... ...
    >>> collrates['H2'].pprint(max_width=60)
    Transition Upper Lower ... C_ij(T=325) C_ij(T=375)
    ---------- ----- ----- ... ----------- -----------
             1     2     1 ...     2.8e-11       3e-11
             2     3     1 ...     1.8e-11     1.9e-11
    """
    # Send HTTP request to open URL
    datafile = [s.strip() for s in get_molfile(mol).text.splitlines()]
    if return_datafile:
        return datafile
    # Parse datafile string list and return a table
    tables = parse_lamda_lines(datafile)
    return tables


def _cln(s):
    """
    Clean a string of comments, newlines
    """
    return s.split("!")[0].strip()

def parse_lamda_datafile(filename):
    with open(filename) as f:
        lines = f.readlines()
    return parse_lamda_lines(lines)

def parse_lamda_lines(data):
    """
    Extract a LAMDA datafile into a dictionary of tables

    (non-pythonic!  more like, fortranic)
    """

    meta_rad = {}
    meta_mol = {}
    meta_coll = {}
    levels = []
    radtrans = []
    collider = None
    ncolltrans = None
    for ii,line in enumerate(data):
        if line[0] == '!':
            continue
        if 'molecule' not in meta_mol:
            meta_mol['molecule'] = _cln(line)
            continue
        if 'molwt' not in meta_mol:
            meta_mol['molwt'] = float(_cln(line))
            continue
        if 'nenergylevels' not in meta_mol:
            meta_mol['nenergylevels'] = int(_cln(line))
            continue
        if len(levels) < meta_mol['nenergylevels']:
            lev,en,wt = _cln(line).split()[:3]
            jul = " ".join(_cln(line).split()[3:])
            levels.append([int(lev), float(en), int(float(wt)), jul])
            continue
        if 'radtrans' not in meta_rad:
            meta_rad['radtrans'] = int(_cln(line))
            continue
        if len(radtrans) < meta_rad['radtrans']:
            # Can have wavenumber at the end.  Ignore that.
            trans,up,low,aval,freq,eu = _cln(line).split()[:6]
            radtrans.append([int(trans), int(up), int(low), float(aval),
                             float(freq), float(eu)])
            continue
        if 'ncoll' not in meta_coll:
            meta_coll['ncoll'] = int(_cln(line))
            ncollrates = {ii:0 for ii in range(1,meta_coll['ncoll']+1)}
            collrates = {}
            continue
        if collider is None:
            collider = int(line[0])
            collname = collider_ids[collider]
            collrates[collider] = []
            meta_coll[collname] = {'collider': collname,
                                   'collider_id': collider}
            continue
        if ncolltrans is None:
            ncolltrans = int(_cln(line))
            meta_coll[collname]['ntrans'] = ncolltrans
            continue
        if 'ntemp' not in meta_coll[collname]:
            meta_coll[collname]['ntemp'] = int(_cln(line))
            continue
        if 'temperatures' not in meta_coll[collname]:
            meta_coll[collname]['temperatures'] = [int(float(x)) for x in
                                                   _cln(line).split()]
            continue
        if len(collrates[collider]) < meta_coll[collname]['ntrans']:
            trans,up,low = [int(x) for x in _cln(line).split()[:3]]
            temperatures = [float(x) for x in _cln(line).split()[3:]]
            collrates[collider].append([trans,up,low]+temperatures)
        if len(collrates[collider]) == meta_coll[collname]['ntrans']:
            #meta_coll[collider_ids[collider]+'_collrates'] = collrates
            log.debug("{ii} Finished loading collider {0:d}: "
                      "{1}".format(collider, collider_ids[collider], ii=ii))
            collider = None
            ncolltrans = None
            if len(collrates) == meta_coll['ncoll']:
                # All done!
                break

    if len(levels[0]) == 4:
        mol_table_names = ['Level','Energy','Weight','J']
    elif len(levels[0]) == 5:
        mol_table_names = ['Level','Energy','Weight','J','F']
    else:
        raise ValueError("Unrecognized levels structure.")
    mol_table_columns = [table.Column(name=name, data=data)
                         for name,data in zip(mol_table_names,
                                              zip(*levels))]
    mol_table = table.Table(data=mol_table_columns, meta=meta_mol)

    rad_table_names = ['Transition','Upper','Lower','EinsteinA','Frequency','E_u(K)']
    rad_table_columns = [table.Column(name=name, data=data)
                         for name,data in zip(rad_table_names,
                                              zip(*radtrans))]
    rad_table = table.Table(data=rad_table_columns, meta=meta_rad)

    coll_tables = {collider_ids[collider]: None for collider in collrates}
    for collider in collrates:
        collname = collider_ids[collider]
        coll_table_names = (['Transition','Upper','Lower'] +
                            ['C_ij(T={0:d})'.format(tem) for tem in
                             meta_coll[collname]["temperatures"]])
        coll_table_columns = [table.Column(name=name, data=data)
                             for name,data in zip(coll_table_names,
                                              zip(*collrates[collider]))]
        coll_table = table.Table(data=coll_table_columns,
                                 meta=meta_coll[collname])
        coll_tables[collname] = coll_table

    return coll_tables,rad_table,mol_table


if __name__ == "__main__":
    pass
