# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Module to search Splatalogue.net via splat, modeled loosely on
ftp://ftp.cv.nrao.edu/NRAO-staff/bkent/slap/idl/

:author: Adam Ginsburg <adam.g.ginsburg@gmail.com>
"""
from astropy.io import ascii
from ..query import BaseQuery
from ..utils.class_or_instance import class_or_instance
from ..utils import commons,process_asyncs
from astropy import units as u
from . import SLAP_URL,QUERY_URL
from . import load_species_table

# example query of SPLATALOGUE directly:
# http://www.cv.nrao.edu/php/splat/c.php?sid%5B%5D=64&sid%5B%5D=108&calcIn=&data_version=v2.0&from=&to=&frequency_units=MHz&energy_range_from=&energy_range_to=&lill=on&tran=&submit=Search&no_atmospheric=no_atmospheric&no_potential=no_potential&no_probable=no_probable&include_only_nrao=include_only_nrao&displayLovas=displayLovas&displaySLAIM=displaySLAIM&displayJPL=displayJPL&displayCDMS=displayCDMS&displayToyaMA=displayToyaMA&displayOSU=displayOSU&displayRecomb=displayRecomb&displayLisa=displayLisa&displayRFI=displayRFI&ls1=ls1&ls5=ls5&el1=el1

@process_asyncs
class Splatalogue(BaseQuery):

    SLAP_URL = SLAP_URL
    QUERY_URL = QUERY_URL
    TIMEOUT = 30
    versions = ('v1.0','v2.0')

    @class_or_instance
    def get_species_ids(self,restr=None,reflags=0):
        """
        Get a dictionary of "species" IDs, where species refers to the molecule
        name, mass, and chemical composition

        Parameters
        ----------
        restr : str
            String to compile into an re, if specified.   Searches table for
            species whose names match
        reflags : int
            Flags to pass to :python:`re`
        """
        # loading can be an expensive operation and should not change at runtime:
        # do it lazily
        if not hasattr(self,'_species_ids'):
            self._species_ids = load_species_table.species_lookuptable()

        if restr is not None:
            return self._species_ids.find(restr,reflags)
        else: 
            return self._species_ids

    @class_or_instance
    def _parse_args(self, min_frequency, max_frequency, chemical_name=None, chem_re_flags=0,
            energy_min=None, energy_max=None, energy_type=None, intensity_lower_limit=None,
            intensity_type=None, transition=None, version='v2.0', exclude=('potential','atmospheric','probable'),
            only_NRAO_recommended=False, 
            line_lists=('Lovas', 'SLAIM', 'JPL', 'CDMS', 'ToyoMA', 'OSU', 'Recomb', 'Lisa', 'RFI'),
            line_strengths=('ls1','ls3','ls4','ls5'),
            energy_levels=('el1','el2','el3','el4'),
            export=True,
            export_limit=10000):
        """
        Query splatalogue using effectively the standard online interface

        Parameters
        ----------
        min_frequency : `astropy.unit`
        max_frequency : `astropy.unit`
            Minimum and maximum frequency (or any spectral() equivalent)
        chemical_name : str
            Name of the chemical to search for.  Treated as a regular expression.
            Example:
            "H2CO" - 13 species have H2CO somewhere in their formula
            "Formaldehyde" - There are 8 isotopologues of Formaldehyde (e.g., H213CO)
            "formaldehyde" - Thioformaldehyde,Cyanoformaldehyde
            "formaldehyde",flags=re.I - Formaldehyde,thioformaldehyde, and Cyanoformaldehyde
            " H2CO " - Just 1 species, H2CO.  The spaces prevent including others.
        chem_re_flags : int
            See the :python:`re` module
        energy_min : None or float
        energy_max : None or float
            Energy range to include.  See energy_type
        energy_type : "E_L(cm)","E_U(cm)","E_U(K)","E_L(K)"
            Type of energy to restrict.  L/U for lower/upper state energy,
            cm/K for *inverse* cm, i.e. wavenumber, or K for Kelvin
        intensity_lower_limit : None or float
            Lower limit on the intensity.  See intensity_type
        intensity_type : None or 'sij','cdms_jpl','aij'
            The type of intensity on which to place a lower limit
        transition : str
            e.g. 1-0
        version : 'v1.0' or 'v2.0'
            Data version
        exclude : list
            Types of lines to exclude.  Default is:
            ('potential','atmospheric','probable')
            Can also exclude 'known'
        only_NRAO_recommended : bool
            Show only NRAO recommended species?
        line_lists : list
            Options:
            Lovas, SLAIM, JPL, CDMS, ToyoMA, OSU, Recomb, Lisa, RFI
        line_strengths : list
            CDMS/JPL Intensity : ls1
            Sij : ls3
            Aij : ls4
            Lovas/AST : ls5
        energy_levels : list
            E_lower (cm^-1) : el1
            E_lower (K) : el2
            E_upper (cm^-1) : el3
            E_upper (K) : el4
        export : bool
            Set up arguments for the export server (as opposed to the HTML
            server)?
        export_limit : int
            Maximum number of lines in output file

        Returns
        -------
        Dictionary of the parameters to send to the SPLAT page
        """

        payload = {'submit':'Search','frequency_units':'GHz'}
    
        min_frequency = min_frequency.to(u.GHz, u.spectral())
        max_frequency = max_frequency.to(u.GHz, u.spectral())
        if min_frequency > max_frequency:
            min_frequency,max_frequency = max_frequency,min_frequency

        payload['from'] = min_frequency.value
        payload['to']   = max_frequency.value

        species_ids = self.get_species_ids(chemical_name,chem_re_flags)
        payload['sid[]'] = species_ids.values()

        payload['energy_range_from'] = float(energy_min) if energy_min is not None else ''
        payload['energy_range_to'] = float(energy_max) if energy_max is not None else ''
        payload['energy_type'] = energy_type if energy_type is not None else ''

        if intensity_type is not None:
            payload['lill'] = 'lill_' + intensity_type
            payload[payload['lill']] = intensity_lower_limit if intensity_lower_limit is not None else ''

        payload['tran'] = transition if transition is not None else ''

        if version in self.versions:
            payload['version'] = version
        else:
            raise ValueError("Invalid version specified.  Allowed versions are {vers}".format(vers=str(self.versions)))

        for e in exclude:
            payload['no_'+e] = 'no_'+e

        if only_NRAO_recommended:
            payload['include_only_nrao'] = 'include_only_nrao'
        
        for L in line_lists:
            payload['display'+L] = 'display'+L

        for LS in line_strengths:
            payload[LS] = LS

        for EL in energy_levels:
            payload[EL] = EL

        # default arg, unmodifiable...
        payload['jsMath'] = 'font:symbol,warn:0'
        payload['__utma'] = ''
        payload['__utmc'] = ''

        if export:
            payload['submit'] = 'Export'
            payload['export_delimiter'] = 'colon' # or tab or comma
            payload['export_type'] = 'current'
            payload['offset'] = 0
            payload['range'] = 'on'
            payload['limit'] = export_limit

        return payload

    @class_or_instance
    def query_species_async(self, *args, **kwargs):
        """
        Returns
        -------
        response : `requests.Response` object
            The response of the HTTP request.
        """
        data_payload = self._parse_args(*args, **kwargs)
        response = commons.send_request(
            self.QUERY_URL,
            data_payload,
            self.TIMEOUT)
        return response

    query_species_async.__doc__ += _parse_args.__doc__


    @class_or_instance
    def _parse_result(self, response, verbose=False):
        """
        Parse a response into an astropy Table
        """

        result = ascii.read(response.content.split('\n'),
                            delimiter=':',
                            format='basic')

        return result

def slap_default_payload(request='queryData', version='2.0', wavelength='',
        chemical_element='', initial_level_energy='', final_level_energy='',
        temperature='', einstein_a=''):
    """
    Parse the valid parameters specified by the `IVOA SLAP`_ interface document.

    .. _IVOA SLAP: http://www.ivoa.net/documents/SLAP/20101209/REC-SLAP-1.0-20101209.pdf
    

    Parameters
    ----------
    request : 'queryData'
        No other valid entries are known
    version : '2.0'
        A valid data version number
    wavelength : 'x/y' or 'x' or 'x,y/z' or 'x/'
        Wavelength range in meters.
        'x/y' means 'in the range from x to y'
        'x/' means 'wavelength > x'
        'x' means 'wavelength == x'
        'x/y,y/z' means 'wavelength in range [x,y] or [y,z]'
        See Appendix A of the `IVOA SLAP`_ manual

    Other Parameters
    ----------------
    chemical_element : str
        A chemical element name.  Can be specified as a comma-separated list
    initial_level_energy : float
        Unit: Joules
    final_level_energy : float
        Unit: Joules
    temperature : float
        Unit : Kelvin
        Expected temperature of object.  Not needed for splatalogue
    einstein_a : float
        Unit : s^-1
    process_type : str
    process_name : str
        Examples: 
        "Photoionization", "Collisional excitation", 
        "Gravitational redshift", "Stark broadening", "Resonance broadening", "Van der 
        Waals broadening"

    Returns
    -------
    Dictionary of parameters which can then be POSTed to the service
    """
    return locals()
