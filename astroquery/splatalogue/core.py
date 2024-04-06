# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
Module to search Splatalogue.net via splat, modeled loosely on
ftp://ftp.cv.nrao.edu/NRAO-staff/bkent/slap/idl/

:author: Adam Ginsburg <adam.g.ginsburg@gmail.com>
"""
import json
from astropy.table import Table
from astropy import units as u
from ..query import BaseQuery
from ..utils import async_to_sync, prepend_docstr_nosections
from . import conf
from . import load_species_table
from .utils import clean_column_headings

from astropy.utils.decorators import deprecated_renamed_argument

__all__ = ['Splatalogue', 'SplatalogueClass']

# example query of SPLATALOGUE directly:
# https://www.cv.nrao.edu/php/splat/c.php?sid%5B%5D=64&sid%5B%5D=108&calcIn=&data_version=v3.0&from=&to=&frequency_units=MHz&energy_range_from=&energy_range_to=&lill=on&tran=&submit=Search&no_atmospheric=no_atmospheric&no_potential=no_potential&no_probable=no_probable&include_only_nrao=include_only_nrao&displayLovas=displayLovas&displaySLAIM=displaySLAIM&displayJPL=displayJPL&displayCDMS=displayCDMS&displayToyaMA=displayToyaMA&displayOSU=displayOSU&displayRecomb=displayRecomb&displayLisa=displayLisa&displayRFI=displayRFI&ls1=ls1&ls5=ls5&el1=el1

# for backward-compatibility
# (As of March 5, this is incomplete, but is enough to make `minimize_table` work)
colname_mapping_feb2024 = {
    'Species': 'name',
    'Chemical Name': 'chemical_name',
    'Resolved QNs': 'resolved_QNs',
    'Freq-GHz(rest frame,redshifted)': 'orderedFreq',
    'Meas Freq-GHz(rest frame,redshifted)': 'measFreq',
    'Log<sub>10</sub> (A<sub>ij</sub>)': 'aij',
    'E_U (K)': 'upper_state_energy_K',
}


@async_to_sync
class SplatalogueClass(BaseQuery):

    SLAP_URL = conf.slap_url
    QUERY_URL = conf.query_url
    TIMEOUT = conf.timeout
    LINES_LIMIT = conf.lines_limit
    versions = ('v1.0', 'v2.0', 'v3.0', 'vall')
    # global constant, not user-configurable
    ALL_LINE_LISTS = ('LovasNIST', 'SLAIM', 'JPL', 'CDMS', 'ToyaMA', 'OSU',
                      'TopModel', 'Recombination', 'RFI')
    VALID_LINE_STRENGTHS = ('CDMSJPL', 'SijMu2', 'Sij', 'Aij', 'LovasAST')
    VALID_ENERGY_LEVELS = {'One': 'EL_cm-1',
                           'Two': 'EL_K',
                           'Three': 'EU_cm-1',
                           'Four': 'EU_K'}
    VALID_ENERGY_TYPES = ('el_cm1', 'eu_cm1', 'eu_k', 'el_k')
    VALID_INTENSITY_TYPES = ('CDMS/JPL (log)', 'Sij-mu2', 'Aij (log)')

    def __init__(self, **kwargs):
        """
        Initialize a Splatalogue query class with default arguments set.
        Frequency specification is required for *every* query, but any
        default keyword arguments (see `query_lines`) can be overridden
        here.
        """
        super().__init__()
        self.data = self._default_kwargs()
        self.set_default_options(**kwargs)

    def set_default_options(self, **kwargs):
        """
        Modify the default options.
        See `query_lines`
        """
        self.data.update(json.loads(self._parse_kwargs(**kwargs)['body']))

    @deprecated_renamed_argument("restr", "species_regex", since="0.4.7")
    def get_species_ids(self, species_regex=None, *, reflags=0, recache=False):
        """
        Get a dictionary of "species" IDs, where species refers to the molecule
        name, mass, and chemical composition.

        Parameters
        ----------
        species_regex : str
            String to search for among the species names, if specified.
            The string will be compiled into a regular expression using the
            python `re` module.
        reflags : int
            Flags to pass to `re`.
        recache : bool
            Flag whether to refresh the local cache of species IDs

        Examples
        --------
        >>> import re
        >>> import pprint # unfortunate hack required for documentation testing
        >>> rslt = Splatalogue.get_species_ids(species_regex='Formaldehyde')
        >>> pprint.pprint(rslt)
        {'03023 H2CO - Formaldehyde': '194',
         '03106 H213CO - Formaldehyde': '324',
         '03107 HDCO - Formaldehyde': '109',
         '03108 H2C17O - Formaldehyde': '982',
         '03202 H2C18O - Formaldehyde': '155',
         '03203 D2CO - Formaldehyde': '94',
         '03204 HD13CO - Formaldehyde': '1219',
         '03301 D213CO - Formaldehyde': '1220',
         '03315 HDC18O - Formaldehyde': '21141',
         '03410 D2C18O - Formaldehyde': '21140'}
        >>> rslt = Splatalogue.get_species_ids(species_regex='H2CO')
        >>> pprint.pprint(rslt)
        {'03023 H2CO - Formaldehyde': '194',
         '03109 H2COH+ - Hydroxymethylium ion': '224',
         '04406 c-H2COCH2 - Ethylene Oxide': '21',
         '06029 NH2CONH2 - Urea': '21166',
         '07510 H2NCH2COOH - I v=0 - Glycine': '389',
         '07511 H2NCH2COOH - I v=1 - Glycine': '1312',
         '07512 H2NCH2COOH - I v=2 - Glycine': '1313',
         '07513 H2NCH2COOH - II v=0 - Glycine': '262',
         '07514 H2NCH2COOH - II v=1 - Glycine': '1314',
         '07515 H2NCH2COOH - II v=2 - Glycine': '1315',
         '07517 NH2CO2CH3 v=0 - Methyl Carbamate': '1334',
         '07518 NH2CO2CH3 v=1 - Methyl Carbamate': '1335',
         '08902 CH3CHNH2COOH - I - α-Alanine': '1321',
         '08903 CH3CHNH2COOH - II - α-Alanine': '1322'}
        >>> # note the whitespace, preventing H2CO within other
        >>> # more complex molecules
        >>> Splatalogue.get_species_ids(species_regex=' H2CO ')
        {'03023 H2CO - Formaldehyde': '194'}
        >>> Splatalogue.get_species_ids(species_regex=' h2co ', reflags=re.IGNORECASE)
        {'03023 H2CO - Formaldehyde': '194'}

        """
        # loading can be an expensive operation and should not change at
        # runtime: do it lazily
        if not hasattr(self, '_species_ids'):
            self._species_ids = load_species_table.species_lookuptable(recache=recache)

        if species_regex is not None:
            return self._species_ids.find(species_regex, flags=reflags)
        else:
            return self._species_ids

    def _default_kwargs(self):
        kwargs = dict(min_frequency=0 * u.GHz,
                      max_frequency=100 * u.THz,
                      chemical_name='',
                      line_lists=self.ALL_LINE_LISTS,
                      line_strengths=self.VALID_LINE_STRENGTHS,
                      energy_levels=self.VALID_ENERGY_LEVELS.keys(),
                      exclude=('potential', 'atmospheric', 'probable'),
                      version='v3.0',
                      only_NRAO_recommended=None,
                      export=True,
                      export_limit=self.LINES_LIMIT,
                      noHFS=False, displayHFS=False, show_unres_qn=False,
                      show_upper_degeneracy=False, show_molecule_tag=False,
                      show_qn_code=False, show_lovas_labref=False,
                      show_lovas_obsref=False, show_orderedfreq_only=False,
                      show_nrao_recommended=False,)
        return json.loads(self._parse_kwargs(**kwargs)['body'])

    def _parse_kwargs(self, *, min_frequency=None, max_frequency=None,
                      chemical_name=None,
                      chem_re_flags=0, energy_min=None, energy_max=None,
                      energy_type=None, intensity_lower_limit=None,
                      intensity_type=None, transition=None, version=None,
                      exclude=None,
                      only_astronomically_observed=None,
                      only_NRAO_recommended=None,
                      line_lists=None, line_strengths=None, energy_levels=None,
                      export=None, export_limit=None, noHFS=None,
                      displayHFS=None, show_unres_qn=None,
                      show_upper_degeneracy=None, show_molecule_tag=None,
                      show_qn_code=None, show_lovas_labref=None,
                      show_lovas_obsref=None, show_orderedfreq_only=None,
                      show_nrao_recommended=None,
                      parse_chemistry_locally=True,
                      export_start=0,
                      export_stop=250):
        """
        The Splatalogue service returns lines with rest frequencies in the
        range [min_frequency, max_frequency].

        Parameters
        ----------
        min_frequency : `astropy.units`
            Minimum frequency (or any spectral() equivalent)
        max_frequency : `astropy.units`
            Maximum frequency (or any spectral() equivalent)
        chemical_name : str
            Name of the chemical to search for. Treated as a regular
            expression.  An empty set ('', (), [], {}) will match *any*
            species. Examples:

            ``'H2CO'`` - 13 species have H2CO somewhere in their formula.

            ``'Formaldehyde'`` - There are 8 isotopologues of Formaldehyde
                                 (e.g., H213CO).

            ``'formaldehyde'`` - Thioformaldehyde,Cyanoformaldehyde.

            ``'formaldehyde',chem_re_flags=re.I`` - Formaldehyde,thioformaldehyde,
                                                    and Cyanoformaldehyde.

            ``' H2CO '`` - Just 1 species, H2CO. The spaces prevent including
                           others.
        parse_chemistry_locally : bool
            Attempt to determine the species ID #'s locally before sending the
            query?  This will prevent queries that have no matching species.
            It also performs a more flexible regular expression match to the
            species IDs.  See the examples in `get_species_ids`
        chem_re_flags : int
            See the `re` module
        energy_min : `None` or float
            Energy range to include.  See energy_type
        energy_max : `None` or float
            Energy range to include.  See energy_type
        energy_type : ``'el_cm1'``, ``'eu_cm1'``, ``'eu_k'``, ``'el_k'``
            Type of energy to restrict.  L/U for lower/upper state energy,
            cm/K for *inverse* cm, i.e. wavenumber, or K for Kelvin
        intensity_lower_limit : `None` or float
            Lower limit on the intensity.  See intensity_type
        intensity_type : `None` or ``'sij'``, ``'cdms_jpl'``, ``'aij'``
            The type of intensity on which to place a lower limit
        transition : str
            e.g. 1-0
        version : ``'v1.0'``, ``'v2.0'``, ``'v3.0'`` or ``'vall'``
            Data version
        exclude : list
            Types of lines to exclude.  Default is:
            (``'potential'``, ``'atmospheric'``, ``'probable'``)
            Can also exclude ``'known'``.
            To exclude nothing, use 'none', not the python object None, since
            the latter is meant to indicate 'leave as default'
        only_astronomically_observed : bool
            Show only astronomically observed species?
        only_NRAO_recommended : bool
            Show only NRAO recommended species?
        line_lists : list
            Options:
            Lovas, SLAIM, JPL, CDMS, ToyaMA, OSU, Recombination, RFI
        line_strengths : list
            * CDMS/JPL Intensity : ls1
            * Sij : ls3
            * Aij : ls4
            * Lovas/AST : ls5
        energy_levels : list
            * E_lower (cm^-1) : "One"
            * E_lower (K) : "Two"
            * E_upper (cm^-1) : "Three"
            * E_upper (K) : "Four"
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

        Returns
        -------
        payload : dict
            Dictionary of the parameters to send to the SPLAT page

        """

        payload = {"searchSpecies": "",
                   "speciesSelectBox": [],
                   "dataVersion": "v3.0",
                   "userInputFrequenciesFrom": [],
                   "userInputFrequenciesTo": [],
                   "userInputFrequenciesUnit": "GHz",
                   "frequencyRedshift": 0,
                   "energyFrom": 0,
                   "energyTo": 0,
                   "energyRangeType": "el_cm-1",
                   "lineIntensity": "None",
                   "lineIntensityLowerLimit": 0,
                   "excludeAtmosSpecies": False,
                   "excludePotentialInterstellarSpecies": False,
                   "excludeProbableInterstellarSpecies": False,
                   "excludeKnownASTSpecies": False,
                   "showOnlyAstronomicallyObservedTransitions": False,
                   "showOnlyNRAORecommendedFrequencies": False,
                   "lineListDisplayJPL": True,
                   "lineListDisplayCDMS": True,
                   "lineListDisplayLovasNIST": True,
                   "lineListDisplaySLAIM": True,
                   "lineListDisplayToyaMA": True,
                   "lineListDisplayOSU": True,
                   "lineListDisplayRecombination": True,
                   "lineListDisplayTopModel": True,
                   "lineListDisplayRFI": True,
                   "lineStrengthDisplayCDMSJPL": True,
                   "lineStrengthDisplaySijMu2": False,
                   "lineStrengthDisplaySij": False,
                   "lineStrengthDisplayAij": False,
                   "lineStrengthDisplayLovasAST": True,
                   "energyLevelOne": True,
                   "energyLevelTwo": False,
                   "energyLevelThree": False,
                   "energyLevelFour": False,
                   "displayObservedTransitions": False,
                   "displayG358MaserTransitions": False,
                   "displayObservationReference": False,
                   "displayObservationSource": False,
                   "displayTelescopeLovasNIST": False,
                   "frequencyErrorLimit": False,
                   "displayHFSIntensity": False,
                   "displayUnresolvedQuantumNumbers": False,
                   "displayUpperStateDegeneracy": False,
                   "displayMoleculeTag": False,
                   "displayQuantumNumberCode": False,
                   "displayLabRef": False,
                   "displayOrderedFrequencyOnly": False,
                   "displayNRAORecommendedFrequencies": False,
                   "displayUniqueSpeciesTag": False,
                   "displayUniqueLineIDNumber": False,
                   "exportType": "current",
                   "exportDelimiter": "tab",
                   "exportLimit": "allRecords",
                   "exportStart": 1,
                   "exportStop": 250}

        if min_frequency is not None and max_frequency is not None:
            # allow setting payload without having *ANY* valid frequencies set
            min_frequency = min_frequency.to(u.GHz, u.spectral())
            max_frequency = max_frequency.to(u.GHz, u.spectral())
            if min_frequency > max_frequency:
                min_frequency, max_frequency = max_frequency, min_frequency

            payload['userInputFrequenciesFrom'] = [min_frequency.value]
            payload['userInputFrequenciesTo'] = [max_frequency.value]

        if chemical_name in ('', {}, (), [], set(), None):
            # include all by default, or whatever default was set
            payload['speciesSelectBox'] = (self.data['speciesSelectBox']
                                           if hasattr(self, 'data')
                                           else [])
        elif chemical_name is not None:
            if parse_chemistry_locally:
                species_ids = self.get_species_ids(species_regex=chemical_name, reflags=chem_re_flags)
                if len(species_ids) == 0:
                    raise ValueError("No matching chemical species found.")
                payload['speciesSelectBox'] = list(species_ids.values())
            else:
                payload['searchSpecies'] = chemical_name

        if energy_min is not None:
            payload['energyFrom'] = float(energy_min)
        if energy_max is not None:
            payload['energyTo'] = float(energy_max)
        if energy_type is not None:
            if energy_type not in self.VALID_ENERGY_TYPES:
                raise ValueError(f'energy_type must be one of {self.VALID_ENERGY_TYPES}')
            payload['energyRangeType'] = energy_type

        if intensity_lower_limit is not None:
            if intensity_type is None:
                raise ValueError("If you specify an intensity lower limit, you must also specify its intensity_type.")
            elif intensity_type not in self.VALID_INTENSITY_TYPES:
                raise ValueError(f'intensity_type must be one of {self.VALID_INTENSITY_TYPES}')
            payload['lineIntensity'] = intensity_type
            payload['lineIntensityLowerLimit'] = intensity_lower_limit

        if version in self.versions:
            payload['dataVersion'] = version
        elif version is not None:
            raise ValueError("Invalid version specified.  Allowed versions "
                             "are {vers}".format(vers=str(self.versions)))

        if exclude is not None:
            if 'potential' in exclude:
                payload['excludePotentialInterstellarSpecies'] = True
            if 'atmospheric' in exclude:
                payload['excludeAtmosSpecies'] = True
            if 'probable' in exclude:
                payload['excludeProbableInterstellarSpecies'] = True
            if 'known' in exclude:
                payload['excludeKnownASTSpecies'] = True

        if only_astronomically_observed:
            payload['showOnlyAstronomicallyObservedTransitions'] = True
        if only_NRAO_recommended:
            payload['showOnlyNRAORecommendedFrequencies'] = True

        if line_lists is not None:
            if type(line_lists) not in (tuple, list):
                raise TypeError("Line lists should be a list of linelist "
                                "names.  See Splatalogue.ALL_LINE_LISTS")
            for L in self.ALL_LINE_LISTS:
                kwd = 'lineListDisplay' + L
                payload[kwd] = L in line_lists

        if line_strengths is not None:
            for LS in line_strengths:
                if LS not in self.VALID_LINE_STRENGTHS:
                    raise ValueError(f"Line strengths must be one of {self.VALID_LINE_STRENGTHS}")
                payload['lineStrengthDisplay' + LS] = True

        if energy_levels is not None:
            for EL in energy_levels:
                if EL not in self.VALID_ENERGY_LEVELS:
                    raise ValueError("Energy levels must be a number spelled out, i.e., "
                                     f"one of {self.VALID_ENERGY_LEVELS}")
                payload['energyLevel' + EL] = True

        for b in ("displayHFSIntensity", "displayUnresolvedQuantumNumbers",
                  "displayUpperStateDegeneracy", "displayMoleculeTag",
                  "displayQuantumNumberCode", "displayLabRef",
                  "displayOrderedFrequencyOnly", "displayNRAORecommendedFrequencies",
                  "displayUniqueLineIDNumber", "displayUniqueSpeciesTag"):
            if b in locals() and locals()[b]:
                payload[b] = True

        if export:
            payload['exportDelimiter'] = 'tab'  # or tab or comma
            payload['exportType'] = 'current'
            payload['exportStart'] = export_start
            payload['exportStop'] = export_stop

        if export_limit is not None:
            payload['exportLimit'] = export_limit
        else:
            payload['exportLimit'] = self.LINES_LIMIT

        payload = {'body': json.dumps(payload),
                   'headers': {'normalizedNames': {}, 'lazyUpdate': None}}

        return payload

    def _validate_kwargs(self, *, min_frequency=None, max_frequency=None,
                         **kwargs):
        """
        Check that min_frequency + max_frequency are specified
        """
        if min_frequency is None or max_frequency is None:
            raise ValueError("Must specify min/max frequency")

    @prepend_docstr_nosections("\n" + _parse_kwargs.__doc__)
    def query_lines_async(self, min_frequency=None, max_frequency=None, *,
                          cache=True, **kwargs):
        """

        Returns
        -------
        response : `requests.Response`
            The response of the HTTP request.

        """
        # have to chomp this kwd here...
        get_query_payload = kwargs.pop('get_query_payload', False)

        self._validate_kwargs(min_frequency=min_frequency,
                              max_frequency=max_frequency, **kwargs)

        data_payload = self._parse_kwargs(min_frequency=min_frequency,
                                          max_frequency=max_frequency,
                                          **kwargs)
        if hasattr(self, 'data'):
            body = self.data.copy()
        else:
            body = self._default_kwargs()

        body.update(json.loads(
            self._parse_kwargs(min_frequency=min_frequency,
                               max_frequency=max_frequency, **kwargs)['body']))
        data_payload['body'] = json.dumps(body)

        if get_query_payload:
            return data_payload

        response = self._request(method='POST',
                                 url=self.QUERY_URL,
                                 json=data_payload,
                                 timeout=self.TIMEOUT,
                                 cache=cache)

        self.response = response

        return response

    def _parse_result(self, response, *, verbose=False):
        """
        Parse a response into an `~astropy.table.Table`

        Parameters
        ----------
        verbose : bool
            Has no effect; kept for API compatibility
        """

        # these are metadata items not intended to be part of the table
        meta_columns = ['orderFreqColName', 'measFreqColName']
        meta = {}

        jdat = response.json()

        result = Table([x for x in jdat if x['species_id'] is not None])

        for key in meta_columns:
            if key in result.colnames:
                meta[key] = result[key][0]
                del result[key]

        result.meta = meta

        return result

    def get_fixed_table(self, *, columns=None):
        """
        Convenience function to get the table with html column names made human
        readable.  It returns only the columns identified with the ``columns``
        keyword.  See the source for the defaults.
        """
        if columns is None:
            columns = ('Species', 'Chemical Name', 'Resolved QNs',
                       'Freq-GHz(rest frame,redshifted)',
                       'Meas Freq-GHz(rest frame,redshifted)',
                       'Log<sub>10</sub> (A<sub>ij</sub>)',
                       'E_U (K)')
        table = clean_column_headings(self.table[columns])
        return table


Splatalogue = SplatalogueClass()
