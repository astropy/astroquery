# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os


def get_package_data():
    paths_test = [os.path.join('data', 'query_bibcode.data'),
             os.path.join('data', 'query_bibobj.data'),
             os.path.join('data', 'query_cat.data'),
             os.path.join('data', 'query_coo.data'),
             os.path.join('data', 'query_id.data'),
             os.path.join('data', 'query_error.data')
                  ]

    paths_core = [os.path.join('data', 'votable_fields_notes.json'),
                  os.path.join('data', 'votable_fields_table.txt'),
                  os.path.join('data', 'votable_fields_dict.json')
                  ]

    return {
        'astroquery.simbad.tests': paths_test,
        'astroquery.simbad': paths_core
    }
