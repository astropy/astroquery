# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import json
from astropy import table
from astropy import log
from astropy.utils.console import ProgressBar
from bs4 import BeautifulSoup
from astropy.extern.six.moves import urllib_parse as urlparse
import re
import warnings

from ..exceptions import InvalidQueryError
from ..query import BaseQuery

__all__ = ['Lamda']

# should skip only if remote_data = False
__doctest_skip__ = ['LamdaClass.query']

# query_types and collider_ids are potentially useful but not used.
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
collider_ids.update({v: k for k, v in list(collider_ids.items())})


class LamdaClass(BaseQuery):

    url = "http://home.strw.leidenuniv.nl/~moldata/datafiles/{0}.dat"

    def __init__(self, **kwargs):
        super(LamdaClass, self).__init__(**kwargs)
        self.moldict_path = os.path.join(self.cache_location,
                                         "molecules.json")

    def _get_molfile(self, mol, cache=True, timeout=None):
        """
        """
        if mol not in self.molecule_dict:
            raise InvalidQueryError("Molecule {0} is not in the valid "
                                    "molecule list.  See Lamda.molecule_dict")
        response = self._request('GET', self.molecule_dict[mol],
                                 timeout=timeout, cache=cache)
        response.raise_for_status()
        return response

    def download_molfile(self, mol, outfilename):
        """
        Download a particular molecular data file `mol` to output file
        `outfilename`
        """
        molreq = self._get_molfile(mol)
        with open(outfilename, 'w') as f:
            f.write(molreq.text)

    def query(self, mol, return_datafile=False, cache=True, timeout=None):
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
        >>> from astroquery.lamda import Lamda
        >>> collrates,radtransitions,enlevels = Lamda.query(mol='co')
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
        datafile = [s.strip() for s in
                    self._get_molfile(mol, timeout=timeout,
                                      cache=cache).text.splitlines()]
        if return_datafile:
            return datafile
        # Parse datafile string list and return a table
        tables = parse_lamda_lines(datafile)
        return tables

    def get_molecules(self, cache=True):
        """
        Scrape the list of valid molecules
        """
        if cache and hasattr(self, '_molecule_dict'):
            return self._molecule_dict
        elif cache and os.path.isfile(self.moldict_path):
            with open(self.moldict_path, 'r') as f:
                md = json.load(f)
            return md

        main_url = 'http://home.strw.leidenuniv.nl/~moldata/'
        response = self._request('GET', main_url, cache=cache)
        response.raise_for_status()

        soup = BeautifulSoup(response.content)

        links = soup.find_all('a', href=True)
        datfile_urls = [url
                        for link in ProgressBar(links)
                        for url in self._find_datfiles(link['href'],
                                                       base_url=main_url)]

        molecule_re = re.compile(r'http://[a-zA-Z0-9.]*/~moldata/datafiles/([A-Z0-9a-z_+@-]*).dat')
        molecule_dict = {molecule_re.search(url).groups()[0]:
                         url
                         for url in datfile_urls}

        with open(self.moldict_path, 'w') as f:
            s = json.dumps(molecule_dict)
            f.write(s)

        return molecule_dict

    @property
    def molecule_dict(self):
        if not hasattr(self, '_molecule_dict'):
            warnings.warn("The first time a LAMDA function is called, it must "
                          "assemble a list of valid molecules and URLs.  This "
                          "list will be cached so future operations will be "
                          "faster.")
            self._molecule_dict = self.get_molecules()

        return self._molecule_dict

    def _find_datfiles(self, url, base_url, raise_for_status=False):

        myurl = _absurl_from_url(url, base_url)
        if 'http' not in myurl:
            # assume this is a bad URL, like a mailto:blah href
            return []

        response = self._request('GET', myurl)
        if raise_for_status:
            response.raise_for_status()
        elif not response.ok:
            # assume this URL does not contain data b/c it does not exist
            return []

        soup = BeautifulSoup(response.content)

        links = soup.find_all('a', href=True)

        urls = [_absurl_from_url(link['href'], base_url)
                for link in links if '.dat' in link['href']]

        return urls


def _absurl_from_url(url, base_url):
    if url[:4] != 'http':
        return urlparse.urljoin(base_url, url)
    return url


def parse_lamda_datafile(filename):
    """
    Read a datafile that follows the format adopted for the atomic and
    molecular data in the LAMDA database.

    Parameters
    ----------
    filename : str
        Fully qualified path of the file to read.

    Returns
    -------
    Tuple of tables: ({rateid: Table, },
                        Table,
                        Table)
    """
    with open(filename) as f:
        lines = f.readlines()
    return parse_lamda_lines(lines)


def write_lamda_datafile(filename, tables):
    """
    Write tuple of tables with LAMDA data into a datafile that follows the
    format adopted for the LAMDA database.

    Parameters
    ----------
    filename : str
        Fully qualified path of the file to write.

    tables: tuple
        Tuple of Tables ({rateid: coll_table}, rad_table, mol_table)
    """
    import platform
    import sys

    collrates, radtransitions, enlevels = tables

    levels_hdr = ("""! MOLECULE
                  {0}
                  ! MOLECULAR WEIGHT
                  {1}
                  ! NUMBER OF ENERGY LEVELS
                  {2}
                  ! LEVEL + ENERGIES(cm^-1) + WEIGHT + J
                  """)
    levels_hdr = re.sub('^ +', '', levels_hdr, flags=re.MULTILINE)
    radtrans_hdr = ("""! NUMBER OF RADIATIVE TRANSITIONS
                    {0}
                    ! TRANS + UP + LOW + EINSTEINA(s^-1) + FREQ(GHz) + E_u(K)
                    """)
    radtrans_hdr = re.sub('^ +', '', radtrans_hdr, flags=re.MULTILINE)
    coll_hdr = ("""! NUMBER OF COLL PARTNERS
                {0}
                """)
    coll_hdr = re.sub('^ +', '', coll_hdr, flags=re.MULTILINE)
    coll_part_hdr = ("""! COLLISION PARTNER
                     {0} {1}
                     ! NUMBER OF COLLISIONAL TRANSITIONS
                     {2}
                     ! NUMBER OF COLLISION TEMPERATURES
                     {3}
                     ! COLLISION TEMPERATURES
                     {4}
                     ! TRANS + UP + LOW + RATE COEFFS(cm^3 s^-1)
                     """)
    coll_part_hdr = re.sub('^ +', '', coll_part_hdr, flags=re.MULTILINE)

    if platform.system() == 'Windows':
        if sys.version_info[0] >= 3:
            stream = open(filename, 'w', newline='')
        else:
            stream = open(filename, 'wb')
    else:
        stream = open(filename, 'w')

    with stream as f:
        f.write(levels_hdr.format(enlevels.meta['molecule'],
                                  enlevels.meta['molwt'],
                                  enlevels.meta['nenergylevels']))
        enlevels.write(f, format='ascii.no_header')
        f.write(radtrans_hdr.format(radtransitions.meta['radtrans']))
        radtransitions.write(f, format='ascii.no_header')
        f.write(coll_hdr.format(len(collrates)))
        for k, v in collrates.items():
            temperatures = ' '.join([str(i) for i in v.meta['temperatures']])
            f.write(coll_part_hdr.format(v.meta['collider_id'],
                                         v.meta['collider'],
                                         v.meta['ntrans'],
                                         v.meta['ntemp'],
                                         temperatures))
            v.write(f, format='ascii.no_header')


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
    for ii, line in enumerate(data):
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
            lev, en, wt = _cln(line).split()[:3]
            jul = " ".join(_cln(line).split()[3:])
            levels.append([int(lev), float(en), int(float(wt)), jul])
            continue
        if 'radtrans' not in meta_rad:
            meta_rad['radtrans'] = int(_cln(line))
            continue
        if len(radtrans) < meta_rad['radtrans']:
            # Can have wavenumber at the end.  Ignore that.
            trans, up, low, aval, freq, eu = _cln(line).split()[:6]
            radtrans.append([int(trans), int(up), int(low), float(aval),
                             float(freq), float(eu)])
            continue
        if 'ncoll' not in meta_coll:
            meta_coll['ncoll'] = int(_cln(line))
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
            trans, up, low = [int(x) for x in _cln(line).split()[:3]]
            temperatures = [float(x) for x in _cln(line).split()[3:]]
            collrates[collider].append([trans, up, low] + temperatures)
        if len(collrates[collider]) == meta_coll[collname]['ntrans']:
            # meta_coll[collider_ids[collider]+'_collrates'] = collrates
            log.debug("{ii} Finished loading collider {0:d}: "
                      "{1}".format(collider, collider_ids[collider], ii=ii))
            collider = None
            ncolltrans = None
            if len(collrates) == meta_coll['ncoll']:
                # All done!
                break

    if len(levels[0]) == 4:
        mol_table_names = ['Level', 'Energy', 'Weight', 'J']
    elif len(levels[0]) == 5:
        mol_table_names = ['Level', 'Energy', 'Weight', 'J', 'F']
    else:
        raise ValueError("Unrecognized levels structure.")
    mol_table_columns = [table.Column(name=name, data=data)
                         for name, data in zip(mol_table_names,
                                               zip(*levels))]
    mol_table = table.Table(data=mol_table_columns, meta=meta_mol)

    rad_table_names = ['Transition', 'Upper', 'Lower', 'EinsteinA',
                       'Frequency', 'E_u(K)']
    rad_table_columns = [table.Column(name=name, data=data)
                         for name, data in zip(rad_table_names,
                                               zip(*radtrans))]
    rad_table = table.Table(data=rad_table_columns, meta=meta_rad)

    coll_tables = {collider_ids[collider]: None for collider in collrates}
    for collider in collrates:
        collname = collider_ids[collider]
        coll_table_names = (['Transition', 'Upper', 'Lower'] +
                            ['C_ij(T={0:d})'.format(tem) for tem in
                             meta_coll[collname]["temperatures"]])
        coll_table_columns = [table.Column(name=name, data=data)
                              for name, data in zip(coll_table_names,
                                                    zip(*collrates[collider]))]
        coll_table = table.Table(data=coll_table_columns,
                                 meta=meta_coll[collname])
        coll_tables[collname] = coll_table

    return coll_tables, rad_table, mol_table


def _cln(s):
    """
    Clean a string of comments, newlines
    """
    return s.split("!")[0].strip()


Lamda = LamdaClass()
