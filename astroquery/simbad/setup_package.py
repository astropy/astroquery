# Licensed under a 3-clause BSD style license - see LICENSE.rst

from pathlib import Path


def get_package_data():
    paths_test = [str(Path('data') / 'query_bibcode.data'),
                  str(Path('data') / 'query_bibobj.data'),
                  str(Path('data') / 'query_cat.data'),
                  str(Path('data') / 'query_coo.data'),
                  str(Path('data') / 'query_id.data'),
                  str(Path('data') / 'query_error.data'),
                  str(Path('data') / 'query_*.data'),
                  str(Path('data') / 'm1.data'),
                  ]

    paths_core = [str(Path('data') / 'query_criteria_fields.json'),
                  str(Path('data') / 'votable_fields_notes.json'),
                  str(Path('data') / 'votable_fields_table.txt'),
                  str(Path('data') / 'votable_fields_dict.json'),
                  ]

    return {'astroquery.simbad.tests': paths_test,
            'astroquery.simbad': paths_core,
            }
