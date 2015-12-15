# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import re

import astropy.units as u
import astropy.io.ascii as asciitable

from ..query import BaseQuery
from ..utils import commons, async_to_sync
from ..utils.docstr_chompers import prepend_docstr_noreturns
from . import conf
from ..exceptions import TableParseError

__all__ = ['Nist', 'NistClass']


def _strip_blanks(table):
    """
    Remove blank lines from table (included for "human readability" but
    useless to us...
    returns a single string joined by \n newlines

    Parameters
    ----------
    table : str
       table to strip as a string

    Returns
    -------
    single string joined by newlines.
    """
    numbersletters = re.compile("[0-9A-Za-z]")
    if isinstance(table, str):
        table = table.split('\n')
    table = [line for line in table if numbersletters.search(line)]
    return "\n".join(table)


@async_to_sync
class NistClass(BaseQuery):
    URL = conf.server
    TIMEOUT = conf.timeout
    unit_code = {'Angstrom': 0,
                 'nm': 1,
                 'um': 2}
    energy_level_code = {'cm-1': 0, 'invcm': 0, 'cm': 0,
                         'ev': 1, 'eV': 1, 'EV': 1, 'electronvolt': 1,
                         'R': 2, 'Rydberg': 2, 'rydberg': 2}
    order_out_code = {'wavelength': 0,
                      'multiplet': 1}
    wavelength_unit_code = {'vacuum': 3,
                            'vac+air': 4}

    def _args_to_payload(self, *args, **kwargs):
        """
        Serves the same purpose as `~NistClass.query` but returns
        the raw HTTP response rather than a `~astropy.table.Table` object.

        Parameters
        ----------
        minwav : `astropy.units.Quantity` object
            The lower wavelength for the spectrum in appropriate units.
        maxwav : `astropy.units.Quantity` object
            The upper wavelength for the spectrum in appropriate units.
        linename : str, optional
            The spectrum to fetch. Defaults to "H I"
        energy_level_unit : str, optional
            The energy level units must be one of the following:
            'R', 'Rydberg', 'rydberg', 'cm', 'cm-1', 'EV', 'eV',
            'electronvolt', 'ev', 'invcm' Defaults to 'eV'.
        output_order : str, optional
            Decide ordering of output. Must be one of following:
            ['wavelength', 'multiplet']. Defaults to 'wavelength'.
        wavelength_type : str, optional
            Must be one of 'vacuum' or 'vac+air'. Defaults to 'vacuum'.
        get_query_payload : bool, optional
            If true then returns the dictionary of query parameters, posted to
            remote server. Defaults to `False`.

        Returns
        -------
        request_payload : dict
            The dictionary of parameters sent with the HTTP request

        """
        request_payload = {}
        request_payload["spectra"] = kwargs['linename']
        (min_wav, max_wav, wav_unit) = _parse_wavelength(args[0], args[1])
        request_payload["low_wl"] = min_wav
        request_payload["upp_wl"] = max_wav
        request_payload["unit"] = wav_unit
        request_payload["submit"] = "Retrieve Data"
        request_payload["format"] = 1  # ascii
        request_payload["line_out"] = 0  # All lines
        request_payload["en_unit"] = Nist.energy_level_code[
            kwargs["energy_level_unit"]]
        request_payload["output"] = 0  # entirely rather than pagewise
        request_payload["bibrefs"] = 1
        request_payload["show_obs_wl"] = 1
        request_payload["show_calc_wl"] = 1
        request_payload["order_out"] = Nist.order_out_code[
            kwargs['output_order']]
        request_payload["max_low_enrg"] = ""
        request_payload["show_av"] = Nist.wavelength_unit_code[
            kwargs['wavelength_type']]
        request_payload["max_upp_enrg"] = ""
        request_payload["tsb_value"] = 0
        request_payload["min_str"] = ""
        request_payload["A_out"] = 0
        request_payload["f_out"] = "on"
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

    @prepend_docstr_noreturns("\n" + _args_to_payload.__doc__)
    def query_async(self, minwav, maxwav, linename="H I",
                    energy_level_unit='eV', output_order='wavelength',
                    wavelength_type='vacuum', get_query_payload=False):
        """
        Returns
        -------
        response : `requests.Response` object
            The response of the HTTP request.
        """
        request_payload = self._args_to_payload(
            minwav, maxwav, linename=linename,
            energy_level_unit=energy_level_unit, output_order=output_order,
            wavelength_type=wavelength_type)
        if get_query_payload:
            return request_payload

        response = commons.send_request(Nist.URL, request_payload,
                                        Nist.TIMEOUT, request_type='GET')
        return response

    def _parse_result(self, response, verbose=False):
        """
        Parses the results form the HTTP response to `astropy.table.Table`.

        Parameters
        ----------
        response : `requests.Response`
            The HTTP response object

        Returns
        -------
        table : `astropy.table.Table`
        """

        pre_re = re.compile("<pre>(.*)</pre>", flags=re.DOTALL)
        links_re = re.compile(r"<a.*?>\s*(\w+)\s*</a>")
        content = response.text

        try:
            pre = pre_re.findall(content)[0]
        except IndexError:
            raise Exception("Result did not contain a table")
        try:
            table = _strip_blanks(pre)
            table = links_re.sub(r'\1', table)
            table = asciitable.read(table, Reader=asciitable.FixedWidth,
                                    data_start=3, delimiter='|')
            return table
        except Exception as ex:
            self.response = response
            self.table_parse_error = ex
            raise TableParseError("Failed to parse asciitable! The raw "
                                  "response can be found in self.response, "
                                  "and the error in self.table_parse_error.")

Nist = NistClass()


def _parse_wavelength(min_wav, max_wav):
    """
    Helper function to return wavelength and units in form accepted by NIST

    Parameters
    ----------
    min_wav : `astropy.units.Quantity` object
        The lower wavelength in proper units.
    max_wav : `astropy.units.Quantity` object
        The upper wavelength in proper units.

    Returns
    -------
    tuple : (number, number, number)
        The value of lower, upper wavelength and their unit.
    """
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
