# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Module to search Splatalogue.net via splat, modeled loosely on
ftp://ftp.cv.nrao.edu/NRAO-staff/bkent/slap/idl/

:author: Adam Ginsburg <adam.g.ginsburg@gmail.com>
"""
from astropy.io import ascii
from ..query import BaseQuery
from ..utils.class_or_instance import class_or_instance
from ..utils import commons,async_to_sync
from ..utils.docstr_chompers import prepend_docstr_noreturns
from astropy import units as u
from . import SLAP_URL,QUERY_URL,SPLATALOGUE_TIMEOUT
from . import load_species_table

__all__ = ['Splatalogue']

# example query of SPLATALOGUE directly:
# http://www.cv.nrao.edu/php/splat/c.php?sid%5B%5D=64&sid%5B%5D=108&calcIn=&data_version=v2.0&from=&to=&frequency_units=MHz&energy_range_from=&energy_range_to=&lill=on&tran=&submit=Search&no_atmospheric=no_atmospheric&no_potential=no_potential&no_probable=no_probable&include_only_nrao=include_only_nrao&displayLovas=displayLovas&displaySLAIM=displaySLAIM&displayJPL=displayJPL&displayCDMS=displayCDMS&displayToyaMA=displayToyaMA&displayOSU=displayOSU&displayRecomb=displayRecomb&displayLisa=displayLisa&displayRFI=displayRFI&ls1=ls1&ls5=ls5&el1=el1


@async_to_sync
class Splatalogue(BaseQuery):

    SLAP_URL = SLAP_URL
    QUERY_URL = QUERY_URL
    TIMEOUT = SPLATALOGUE_TIMEOUT()
    versions = ('v1.0','v2.0')

    def __init__(self, **kwargs):
        """
        Initialize a Splatalogue query class with default arguments set.
        Frequency specification is required for *every* query, but any default keyword
        arguments (see `query_lines`) can be overridden here
        """
        self.data = self._default_kwargs()
        self.set_default_options(**kwargs)

    def set_default_options(self,**kwargs):
        """
        Modify the default options.
        See `query_lines`
        """
        self.data.update(self._parse_kwargs(**kwargs))

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
    def _default_kwargs(self):
        kwargs = dict(chemical_name='',
                      line_lists=('Lovas', 'SLAIM', 'JPL', 'CDMS', 'ToyoMA',
                                  'OSU', 'Recomb', 'Lisa', 'RFI'),
                      line_strengths=('ls1','ls3','ls4','ls5'),
                      energy_levels=('el1','el2','el3','el4'),
                      exclude=('potential','atmospheric','probable'),
                      version='v2.0',
                      only_NRAO_recommended=None,
                      export=True,
                      export_limit=10000,
                      noHFS=False, displayHFS=False, show_unres_qn=False,
                      show_upper_degeneracy=False, show_molecule_tag=False,
                      show_qn_code=False, show_lovas_labref=False,
                      show_lovas_obsref=False, show_orderedfreq_only=False,
                      show_nrao_recommended=False,)
        return self._parse_kwargs(**kwargs)

    @class_or_instance
    def _parse_kwargs(self, chemical_name=None, chem_re_flags=0,
                      energy_min=None, energy_max=None, energy_type=None,
                      intensity_lower_limit=None, intensity_type=None,
                      transition=None, version=None, exclude=None,
                      only_NRAO_recommended=None, line_lists=None,
                      line_strengths=None, energy_levels=None, export=None,
                      export_limit=None, noHFS=None, displayHFS=None,
                      show_unres_qn=None, show_upper_degeneracy=None,
                      show_molecule_tag=None, show_qn_code=None,
                      show_lovas_labref=None, show_lovas_obsref=None,
                      show_orderedfreq_only=None, show_nrao_recommended=None):
        """

        Other Parameters
        ----------------
        chemical_name : str
            Name of the chemical to search for.  Treated as a regular expression.
            An empty set ('', (), [], {}) will match *any* species.
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
        energy_type : "el_cm1","eu_cm1","eu_k","el_k"
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
        noHFS : bool
            No HFS Display
        displayHFS : bool
            Display HFS Intensity
        show_unres_qn : bool
            Display Unresolved Quantum Numbers
        show_upper_degeneracy : bool
            Display Upper State Degeneracy
        show_molecule_tag : bool
            Display Molecule Tag
        show_qn_code : bool
            Display Quantum Number Code
        show_lovas_labref : bool
            Display Lab Ref
        show_lovas_obsref : bool
            Display Obs Ref
        show_orderedfreq_only : bool
            Display Ordered Frequency ONLY
        show_nrao_recommended : bool
            Display NRAO Recommended Frequencies
        payload : dict
            A dictionary of keywords

        Returns
        -------
        Dictionary of the parameters to send to the SPLAT page
        """

        payload = {'submit':'Search'}

        if chemical_name in ('',{},(),[],set()):
            # include all
            payload['sid[]'] = []
        elif chemical_name is not None:
            species_ids = self.get_species_ids(chemical_name,chem_re_flags)
            if len(species_ids) == 0:
                raise ValueError("No matching chemical species found.")
            payload['sid[]'] = species_ids.values()

        if energy_min is not None:
            payload['energy_range_from'] = float(energy_min)
        if energy_max is not None:
            payload['energy_range_to'] = float(energy_max)
        if energy_type is not None:
            payload['energy_range_type'] = energy_type

        if intensity_type is not None:
            payload['lill'] = 'lill_' + intensity_type
            if intensity_lower_limit is not None:
                payload[payload['lill']] = intensity_lower_limit

        if transition is not None:
            payload['tran'] = transition

        if version in self.versions:
            payload['version'] = version
        elif version is not None:
            raise ValueError("Invalid version specified.  Allowed versions are {vers}".format(vers=str(self.versions)))

        if exclude is not None:
            for e in exclude:
                payload['no_'+e] = 'no_'+e

        if only_NRAO_recommended:
            payload['include_only_nrao'] = 'include_only_nrao'

        if line_lists is not None:
            for L in line_lists:
                payload['display'+L] = 'display'+L

        if line_strengths is not None:
            for LS in line_strengths:
                payload[LS] = LS

        if energy_levels is not None:
            for EL in energy_levels:
                payload[EL] = EL

        for b in "noHFS,displayHFS,show_unres_qn,show_upper_degeneracy,show_molecule_tag,show_qn_code,show_lovas_labref,show_orderedfreq_only,show_lovas_obsref,show_nrao_recommended".split(","):
            if locals()[b]:
                payload[b] = b

        # default arg, unmodifiable...
        payload['jsMath'] = 'font:symbol,warn:0'
        payload['__utma'] = ''
        payload['__utmc'] = ''

        if export:
            payload['submit'] = 'Export'
            payload['export_delimiter'] = 'colon'  # or tab or comma
            payload['export_type'] = 'current'
            payload['offset'] = 0
            payload['range'] = 'on'
            payload['limit'] = export_limit

        return payload

    @class_or_instance
    def _parse_frequency(self, min_frequency, max_frequency):
        """
        The Splatalogue service returns lines with rest frequencies in the
        range [min_frequency, max_frequency]

        Parameters
        ----------
        min_frequency : `astropy.unit`
        max_frequency : `astropy.unit`
            Minimum and maximum frequency (or any spectral() equivalent)
        """

        payload = {'frequency_units':'GHz'}

        min_frequency = min_frequency.to(u.GHz, u.spectral())
        max_frequency = max_frequency.to(u.GHz, u.spectral())
        if min_frequency > max_frequency:
            min_frequency,max_frequency = max_frequency,min_frequency

        payload['from'] = min_frequency.value
        payload['to'] = max_frequency.value

        return payload

    @class_or_instance
    @prepend_docstr_noreturns("\n"+_parse_frequency.__doc__ + "\n" + _parse_kwargs.__doc__)
    def query_lines_async(self, *args, **kwargs):
        """
        Returns
        -------
        response : `requests.Response` object
            The response of the HTTP request.
        """
        if hasattr(self,'data'):
            data_payload = self.data.copy()
            data_payload.update(self._parse_frequency(*args))
            data_payload.update(self._parse_kwargs(**kwargs))
        else:
            data_payload = self._default_kwargs()
            data_payload.update(self._parse_kwargs(**kwargs))
            data_payload.update(self._parse_frequency(*args))
        if kwargs.get('get_query_payload'):
            return data_payload

        response = commons.send_request(
            self.QUERY_URL,
            data_payload,
            self.TIMEOUT)
        return response

    @class_or_instance
    def _parse_result(self, response, verbose=False):
        """
        Parse a response into an astropy Table
        """

        try:
            result = ascii.read(response.content.split('\n'),
                                delimiter=':',
                                format='basic')
        except TypeError:
            # deprecated
            result = ascii.read(response.content.split('\n'),
                                delimiter=':',
                                Reader=ascii.Basic)

        return result
