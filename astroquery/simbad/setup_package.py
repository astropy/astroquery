# Licensed under a 3-clause BSD style license - see LICENSE.rst

from pathlib import Path


def get_package_data():
    paths_test = [str(Path('data') / 'simbad_output_options.xml'),
                  str(Path("data") / "simbad_basic_columns.xml"),
                  str(Path("data") / "simbad_linked_to_basic.xml")]

    paths_core = [str(Path('data') / 'query_criteria_fields.json')]

    return {'astroquery.simbad.tests': paths_test,
            'astroquery.simbad': paths_core,
            }
