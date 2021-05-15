# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astroquery import log
import os
import json
from ..splatalogue.load_species_table import SpeciesLookuptable
from . import Conf


def species_lookuptable(cache=True):
    """
    Get a lookuptable from chemical name + OrdinaryStructuralFormula to VAMDC
    id
    """

    if not os.path.exists(Conf.cache_location):
        os.makedirs(Conf.cache_location)

    lut_path = os.path.join(Conf.cache_location,
                            'species_lookuptable.json')
    if os.path.exists(lut_path) and cache:
        log.info("Loading cached molecular line ID database")
        with open(lut_path, 'r') as fh:
            lutdict = json.load(fh)
        lookuptable = SpeciesLookuptable(lutdict)
    else:
        log.info("Loading molecular line ID database")

        from vamdclib import nodes as vnodes
        from vamdclib import request as vrequest

        nl = vnodes.Nodelist()
        nl.findnode('cdms')
        cdms = nl.findnode('cdms')

        request = vrequest.Request(node=cdms)

        # Retrieve all species from CDMS
        result = request.getspecies()
        molecules = result.data['Molecules']

        lutdict = {"{0} {1}".format(molecules[key].ChemicalName,
                                    molecules[key].OrdinaryStructuralFormula):
                   molecules[key].VAMDCSpeciesID
                   for key in molecules}
        lookuptable = SpeciesLookuptable(lutdict)
        if cache:
            with open(lut_path, 'w') as fh:
                json.dump(lookuptable, fh)

    return lookuptable
