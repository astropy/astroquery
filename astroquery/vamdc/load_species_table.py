# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy import log
from ..splatalogue.load_species_table import SpeciesLookuptable


def species_lookuptable():

    log.info("Loading molecular line ID database")

    from vamdclib import nodes
    from vamdclib import request as r

    nl = nodes.Nodelist()
    nl.findnode('cdms')
    cdms = nl.findnode('cdms')

    request = r.Request(node=cdms)

    # Retrieve all species from CDMS
    result = request.getspecies()
    molecules = result.data['Molecules']

    lookuptable = SpeciesLookuptable({molecules[key].OrdinaryStructuralFormula: key
                                      for key in molecules})

    return lookuptable
