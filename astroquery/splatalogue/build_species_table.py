# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Support module for splatalogue.  Requires bs4, and is therefore not intended
for users / not part of the core package.

:author: Adam Ginsburg <adam.g.ginsburg@gmail.com>
"""
import json
import os
import requests

from . import conf


def data_path(filename: str):
    """
    Build the path to save a file.  Note that this path is part of the
    astroquery source code, not the astropy cache directory, as the existence
    of the file is a prerequisite for performing queries.

    Parameters
    ----------
    filename : str
        Name of the file (generally should be splat-species.json)

    Returns
    -------
    str
        Full path to the cache directory
    """
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def get_json_species_ids(*, outfile='splat-species.json', base_url=conf.base_url):
    """
    Uses BeautifulSoup to scrape the NRAO Splatalogue species
    selector form, and caches the result as JSON. The file
    is saved to the ``astropy`` cache.

    Parameters
    ----------
    outfile : str, optional
        Name of the output JSON, by default 'splat-species.json'

    Returns
    -------
    str
        Formatted string representation of the JSON object
    """
    import bs4

    result = requests.get(f'{base_url}/b.php')
    page = bs4.BeautifulSoup(result.content, 'html5lib')
    # The ID needs to be checked periodically if Splatalogue is updated
    sid = page.find_all('select', attrs={'id': 'speciesselectbox'})[0]

    species_types = set()
    for kid in sid.children:
        if hasattr(kid, 'attrs') and 'class' in kid.attrs:
            species_types.add(kid['class'][0])

    species = dict((k, {}) for k in species_types)

    for kid in sid.children:
        if hasattr(kid, 'attrs') and 'class' in kid.attrs:
            species[kid['class'][0]][kid['value']] = kid.text

    with open(data_path(outfile), 'w') as f:
        json.dump(species, f)

    return json.dumps(species)


if __name__ == "__main__":
    get_json_species_ids()
