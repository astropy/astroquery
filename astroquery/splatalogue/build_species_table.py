# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Support module for splatalogue.  Requires bs4, and is therefore not intended
for users / not part of the core package.

:author: Adam Ginsburg <adam.g.ginsburg@gmail.com>
"""
import json
import os
import requests


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def get_json_species_ids(outfile='species.json'):
    """
    Load the NRAO Splatalogue form and parse the inputs into a JSON object
    """
    import bs4

    result = requests.get('https://www.cv.nrao.edu/php/splat/b.php')
    page = bs4.BeautifulSoup(result.content, 'html5lib')
    sid = page.findAll('select', attrs={'id': 'sid'})[0]

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
