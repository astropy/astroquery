# Licensed under a 3-clause BSD style license - see LICENSE.rst
import urllib2
import urllib
import re
import numpy as np
from astropy.table import Table
if sys.version_info[0] >= 3:
    from io import BytesIO as StringIO
else:
    from cStringIO import StringIO

# TODO make correct method name
__all__ = ['lamdaquery']

class URLs(object):
    """
    URLs on the Leiden University site for data files.
    """
    def __init__(self):
        self.top_level = "http://home.strw.leidenuniv.nl/~moldata/"
        self.data_file = "datafiles/{}.dat"
urls = URLs()

class LAMDAMolecules(object):
    """
    LAMDA molecules base class container
    """
    def __init__(self):
        self.mols = {
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

    def print_molecules(self):
        pass
    pass

class LAMDAQuery(object)
    """
    LAMDA query base class
    """
    def __init__(self):
        pass
    pass

# extract stuff within <pre> tag
pre_re = re.compile("<pre>(.*)</pre>",flags=re.DOTALL)
numbersletters = re.compile("[0-9A-Za-z]")

def strip_blanks(table):
    """
    Remove blank lines from table (included for "human readability" but useless to us...

    returns a single string joined by \n newlines
    """
    if isinstance(table,str):
        table = table.split('\n')
    table = [line for line in table if numbersletters.search(line)]
    return "\n".join(table)

class NISTAtomicLinesQuery(object):
    def __init__(self):
        self.opener = urllib2.build_opener()

    def query_line_ascii(self, linename, minwav, maxwav, wavelength_unit='A',
            energy_level_unit='eV', page_size=15, output_order='wavelength',
            wavelength_type='vacuum'):
        """
        Query the NIST Atomic Lines database

        Example
        =======

        >>> Q = NISTAtomicLinesQuery()
        >>> Q.query_line_ascii('H I',4000,7000,wavelength_unit='A',energy_level_unit='eV')
        """



        unit_code = {'A':0,'angstrom':0,
                'nm':1,'nanometer':1,
                'um':2,'micron':2,'micrometer':2}
        energy_level_code = {'cm-1':0, 'invcm':0,'cm':0,
                'ev':1,'eV':1,'EV':1,'electronvolt':1,
                'R':2,'Rydberg':2,'rydberg':2}
        order_out_code = {'wavelength':0,
                'multiplet':1}
        wavelength_unit_code = {'vacuum': 3,
                'vac+air':4}

        self.request = {
            "spectra":"H I",
            "low_wl":minwav,
            "upp_wl":maxwav,
            "unit":unit_code[wavelength_unit],
            "submit":"Retrieve Data",
            "format":"1", # 0 = html, 1=ascii
            "line_out":"0",
            "en_unit":energy_level_code[energy_level_unit],
            "output":"0",
            "bibrefs":"1",
            "page_size":page_size,
            "show_obs_wl":"1",
            "show_calc_wl":"1",
            "order_out":order_out_code[output_order],
            "max_low_enrg":"",
            "show_av":wavelength_unit_code[wavelength_type],
            "max_upp_enrg":"",
            "tsb_value":"0",
            "min_str":"",
            "A_out":"0",
            "intens_out":"on",
            "max_str":"",
            "allowed_out":"1",
            "forbid_out":"1",
            "min_accur":"",
            "min_intens":"",
            "conf_out":"on",
            "term_out":"on",
            "enrg_out":"on",
            "J_out":"on"}
            #wavenumber 
            #"upp_wn":""
            #"low_wn":""

        page = self.opener.open(url_lines, urllib.urlencode(self.request))
        pre = pre_re.findall(page.read())[0]
        table = strip_blanks(pre)
        Table = asciitable.read(table, Reader=asciitable.FixedWidth,
                data_start=3)

        return Table

    def query_line_html(self, linename, minwav, maxwav, wavelength_unit='A',
            energy_level_unit='eV', page_size=15, output_order='wavelength',
            wavelength_type='vacuum'):
        """
        Query the NIST Atomic Lines database

        Example
        =======

        >>> Q = NISTAtomicLinesQuery()
        >>> Q.query_line_html('H I',4000,7000,wavelength_unit='A',energy_level_unit='eV')
        """

        import bs4


        unit_code = {'A':0,'angstrom':0,
                'nm':1,'nanometer':1,
                'um':2,'micron':2,'micrometer':2}
        energy_level_code = {'cm-1':0, 'invcm':0,'cm':0,
                'ev':1,'eV':1,'EV':1,'electronvolt':1,
                'R':2,'Rydberg':2,'rydberg':2}
        order_out_code = {'wavelength':0,
                'multiplet':1}
        wavelength_unit_code = {'vacuum': 3,
                'vac+air':4}

        self.request = {
            "spectra":"H I",
            "low_wl":minwav,
            "upp_wl":maxwav,
            "unit":unit_code[wavelength_unit],
            "submit":"Retrieve Data",
            "format":"0", # 0 = html, 1=ascii
            "line_out":"0",
            "en_unit":energy_level_code[energy_level_unit],
            "output":"0",
            "bibrefs":"1",
            "page_size":page_size,
            "show_obs_wl":"1",
            "show_calc_wl":"1",
            "order_out":order_out_code[output_order],
            "max_low_enrg":"",
            "show_av":wavelength_unit_code[wavelength_type],
            "max_upp_enrg":"",
            "tsb_value":"0",
            "min_str":"",
            "A_out":"0",
            "intens_out":"on",
            "max_str":"",
            "allowed_out":"1",
            "forbid_out":"1",
            "min_accur":"",
            "min_intens":"",
            "conf_out":"on",
            "term_out":"on",
            "enrg_out":"on",
            "J_out":"on"}
            #wavenumber 
            #"upp_wn":""
            #"low_wn":""

        page = self.opener.open(url_lines, urllib.urlencode(self.request))
        tables = bs4.BeautifulSoup(page.read()).findAll('table')[4]

        return parse_nist_table(tables)

def parse_nist_table(table):
    """
    Slightly hacky parsing of NIST table into np.recarray
    """
    result = []
    allrows = table.findAll('tr')
    for row in allrows:
        result.append([])
        allcols = row.findAll('td') + row.findAll('th')
        for col in allcols:
            thestrings = [s.encode('ascii','ignore').strip(" []()")
                    for s in col.findAll(text=True)]
            thetext = ''.join(thestrings)
            result[-1].append(thetext)
    header = result.pop(0)
    header = [x for y in header for x in y.split(',')]
    def func(lis):
        pref=""
        for x in lis:
            if "lower" in x.lower():
                pref="Lower"
            elif "upper" in x.lower():    
                pref="Upper"
            if header.count(x)>1:    
                yield pref+x
            elif x == "":
                yield "blank"
            else:      
                yield x
    header = list(func(header))        
    columns = [np.array(z) for z in zip(*result)]
    for ii,col in enumerate(columns):
        try:
            col[col==''] = np.nan
            col = col.astype('float')
            columns[ii] = col
        except ValueError:
            pass

    dtypes = zip(header,[z.dtype for z in columns])
    blankarr = np.recarray(columns[0].size, dtype=dtypes)
    for H,col in zip(header,columns):
        blankarr[H] = col

    return blankarr
    #try:
    #    tblarr = np.recarray(columns, names=header, dtype=dtypes)
    #    return tblarr
    #except:
    #    return header,result


if __name__ == "__main__":
    # TODO add test query when classes completed
    #test query
    #Q = LAMDAMolQuery()
    #LAMDA_Table = Q.query_mol('H I',4000,7000,wavelength_unit='A',energy_level_unit='eV')
    pass


