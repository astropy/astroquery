import urllib2
import urllib
import re
import asciitable

url_lines = "http://physics.nist.gov/cgi-bin/ASD/lines1.pl"

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

    def query_line(self, linename, minwav, maxwav, wavelength_unit='A',
            energy_level_unit='eV', page_size=15, output_order='wavelength',
            wavelength_type='vacuum'):
        """
        Query the NIST Atomic Lines database

        Example
        =======

        >>> Q = NISTAtomicLinesQuery()
        >>> Q.query_line('H I',4000,7000,wavelength_unit='A',energy_level_unit='eV')
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

if __name__ == "__main__":
    #test query
    Q = NISTAtomicLinesQuery()
    T = Q.query_line('H I',4000,7000,wavelength_unit='A',energy_level_unit='eV')
