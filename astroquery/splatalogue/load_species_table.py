# Licensed under a 3-clause BSD style license - see LICENSE.rst
import json
import re
from .build_species_table import data_path


class SpeciesLookuptable(dict):

    def find(self, s, flags=0, return_dict=True,):
        """
        Search dictionary keys for a regex match to string s

        Parameters
        ----------
        s : str
            String to compile as a regular expression
        return_dict : bool
            Return a dictionary if true or just the matching values if false
        flags : int
            re (regular expression) flags

        Returns
        -------
        Subset of parent dictionary if return_dict, else list of values
        corresponding to matches
        """

        R = re.compile(s, flags)

        out = SpeciesLookuptable(dict((k, v) for k, v in self.items()
                                      if R.search(k)))

        if return_dict:
            return out
        else:
            return out.values()


def species_lookuptable(filename='species.json'):
    with open(data_path(filename), 'r') as f:
        J = json.load(f)

    lookuptable = SpeciesLookuptable(dict((v, k) for d in J.values()
                                          for k, v in d.items()))

    return lookuptable
