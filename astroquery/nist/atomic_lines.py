# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import re

import astropy.units as u
try:
    import astropy.io.ascii as asciitable
except ImportError:
    import asciitable

from ..query import BaseQuery
from ..utils.class_or_instance import class_or_instance
from ..utils import commons

def strip_blanks(table):
    """
    Remove blank lines from table (included for "human readability" but useless to us...

    returns a single string joined by \n newlines
    """
    numbersletters = re.compile("[0-9A-Za-z]")
    if isinstance(table,str):
        table = table.split('\n')
    table = [line for line in table if numbersletters.search(line)]
    return "\n".join(table)

class Nist(BaseQuery):
    URL = "http://physics.nist.gov/cgi-bin/ASD/lines1.pl"
    TIMEOUT = 30
    unit_code = {'Angstrom':0,
                 'nm': 1,
                 'um': 2}
    energy_level_code = {'cm-1':0, 'invcm':0,'cm':0,
                'ev':1,'eV':1,'EV':1,'electronvolt':1,
                'R':2,'Rydberg':2,'rydberg':2}
    order_out_code = {'wavelength':0,
                'multiplet':1}
    wavelength_unit_code = {'vacuum': 3,
                'vac+air':4}

    @class_or_instance
    def query(self, linename, minwav, maxwav, energy_level_unit='eV', output_order='wavelength',
              wavelength_type='vacuum', get_query_payload=False):

        response = self.query_async(linename, minwav, maxwav,
                                    energy_level_unit=energy_level_unit,
                                    output_order=output_order,
                                    wavelength_type=wavelength_type,
                                    get_query_payload=get_query_payload)
        if get_query_payload:
            return response

        result = self._parse_result(response)
        return result

    @class_or_instance
    def query_async(self, linename, minwav, maxwav, energy_level_unit='eV', output_order='wavelength',
                    wavelength_type='vacuum', get_query_payload=False):

        request_payload = self._args_to_payload(linename, minwav, maxwav,
                                                energy_level_unit=energy_level_unit,
                                                output_order=output_order,
                                                wavelength_type=wavelength_type)
        if get_query_payload:
            return request_payload

        response = commons.send_request(Nist.URL, request_payload, Nist.TIMEOUT, request_type='GET')
        return response

    @class_or_instance
    def _args_to_payload(self, *args, **kwargs):
        request_payload = {}
        request_payload["spectra"] = args[0]
        (min_wav, max_wav, wav_unit) = _parse_wavelength(args[1], args[2])
        request_payload["low_wl"] = min_wav
        request_payload["upp_wl"] = max_wav
        request_payload["unit"] = wav_unit
        request_payload["submit"] = "Retrieve Data"
        request_payload["format"] = 1 # ascii
        request_payload["line_out"] = 0 # All lines
        request_payload["en_unit"] = Nist.energy_level_code[kwargs["energy_level_unit"]]
        request_payload["output"] = 0 # entirely rather than pagewise
        request_payload["bibrefs"] = 1
        request_payload["show_obs_wl"] = 1
        request_payload["show_calc_wl"] = 1
        request_payload["order_out"] = Nist.order_out_code[kwargs['output_order']]
        request_payload["max_low_enrg"] = ""
        request_payload["show_av"] = Nist.wavelength_unit_code[kwargs['wavelength_type']]
        request_payload["max_upp_enrg"] = ""
        request_payload["tsb_value"] = 0
        request_payload["min_str"] = ""
        request_payload["A_out"] = 0
        request_payload["intens_out"] = "on"
        request_payload["max_str"] = ""
        request_payload["allowed_out"] = 1
        request_payload["forbid_out"] = 1
        request_payload["min_accur"] = ""
        request_payload["min_intens"] = ""
        request_payload["conf_out"] = "on"
        request_payload["term_out"] = "on"
        request_payload["enrg_out"] = "on"
        request_payload["J_out"] = "on"
        request_payload["page_size"] = 15
        return request_payload

    @class_or_instance
    def _parse_result(self, response):
        pre_re = re.compile("<pre>(.*)</pre>",flags=re.DOTALL)
        pre = pre_re.findall(response.content)[0]
        table = strip_blanks(pre)
        Table = asciitable.read(table, Reader=asciitable.FixedWidth,
                data_start=3)
        return Table


def _parse_wavelength(min_wav, max_wav):

    max_wav = max_wav.to(min_wav.unit)
    wav_unit = min_wav.unit.to_string()
    if wav_unit not in Nist.unit_code:
        max_wav = max_wav.to(u.angstrom).value
        min_wav = min_wav.to(u.angstrom).value
        wav_unit = Nist.unit_code['Angstrom']
    else:
        max_wav = max_wav.value
        min_wav = min_wav.value
        wav_unit = Nist.unit_code[wav_unit]
    return (min_wav, max_wav, wav_unit)
