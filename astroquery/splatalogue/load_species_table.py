# Licensed under a 3-clause BSD style license - see LICENSE.rst
import json
import re
import os

from astroquery.splatalogue.build_species_table import data_path, get_json_species_ids


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


def species_lookuptable(filename='splat-species.json', recache=False):
    """
    Function to format the species ID results from scraping Splatalogue
    into a ``SpeciesLookuptable`` object.

    The first step is to check whether or not a cached result exists;
    if not, we run the scraping routine and use this result. Otherwise,
    load and use the cached result.

    The ``recache`` flag can be used to force a refresh of the local
    cache.

    Parameters
    ----------
    filename : str, optional
        Name of the file cache, by default 'splat-species.json'
    recache : bool, optional
        If True, force refreshing of the JSON cache, by default False

    Returns
    -------
    ``lookuptable``
        ``SpeciesLookuptable`` object
    """
    file_cache = data_path(filename)
    # check to see if the file exists; if not, we run the
    # scraping routine
    if recache or not os.path.isfile(file_cache):
        J = get_json_species_ids(filename)
    else:
        with open(data_path(filename), 'r') as f:
            J = json.load(f)
    lookuptable = SpeciesLookuptable(dict((v, k) for d in J.values()
                                          for k, v in d.items()))

    return lookuptable
