# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import os.path
import warnings

from ..utils.process_asyncs import async_to_sync
from ..query import BaseQuery
from . import conf
from . load_species_table import species_lookuptable

__doctest_skip__ = ['VamdcClass.*']


@async_to_sync
class VamdcClass(BaseQuery):

    TIMEOUT = conf.timeout
    CACHE_LOCATION = conf.cache_location

    def __init__(self, doimport=True):
        super(VamdcClass, self).__init__()

        if not doimport:
            # this is a hack to allow the docstrings to be produced without
            # importing the necessary modules
            return

        from vamdclib import nodes as vnodes
        from vamdclib import request as vrequest
        from vamdclib import results as vresults
        from vamdclib import specmodel

        self._vnodes = vnodes
        self._vrequest = vrequest
        self._vresults = vresults

        self._nl = vnodes.Nodelist()
        self._cdms = self._nl.findnode('cdms')

        self.specmodel = specmodel

    @property
    def species_lookuptable(self, cache=True):
        """
        As a property, you can't turn off caching....
        """
        if not hasattr(self, '_lut'):
            self._lut = species_lookuptable(cache=cache)

        return self._lut

    def query_molecule(self, molecule_name, chem_re_flags=0, cache=True):
        """
        Query for the VAMDC data for a specific molecule

        Parameters
        ----------
        molecule_name: str
            The common name (including unicode characters) or the ordinary
            molecular formula (e.g., CH3OH for Methanol) of the molecule.
        chem_re_flags: int
            The re (regular expression) flags for comparison of the molecule
            name with the lookuptable keys
        cache: bool
            Use the astroquery cache to store/recover the result

        Returns
        -------
        result: ``vamdclib.request.Result``
            A vamdclib Result object that has a data attribute.  The result
            object has dictionary-like entries but has more functionality built
            on top of that
        """

        myhash = "{0}_re{1}".format(molecule_name, chem_re_flags)
        myhashpath = os.path.join(self.CACHE_LOCATION,
                                  myhash)
        if os.path.exists(myhashpath) and cache:
            with open(myhashpath, 'rb') as fh:
                xml = fh.read()
            result = self._vresults.Result(xml=xml)
            result.populate_model()
        else:
            species_id_dict = self.species_lookuptable.find(molecule_name,
                                                            flags=chem_re_flags)
            if len(species_id_dict) == 1:
                species_id = list(species_id_dict.values())[0]
            else:
                raise ValueError("Too many species matched: {0}"
                                 .format(species_id_dict))

            request = self._vrequest.Request(node=self._cdms)
            query_string = "SELECT ALL WHERE VAMDCSpeciesID='%s'" % species_id
            request.setquery(query_string)
            result = request.dorequest()

            if cache:
                with open(myhashpath, 'wb') as fh:
                    xml = fh.write(result.Xml)

        return result

        # example use of specmodel; return to this later...
        # Q = self.specmodel.calculate_partitionfunction(result.data['States'],
        #                                  temperature=tex)[species_id]


try:
    Vamdc = VamdcClass()
except ImportError:
    warnings.warn("vamdclib could not be imported; the vamdc astroquery module "
                  "will not work")
    Vamdc = VamdcClass(doimport=False)
