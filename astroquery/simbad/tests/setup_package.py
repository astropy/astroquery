import os

def get_package_data():
    paths = [os.path.join('data', 'query_bibcode.data'),
             os.path.join('data', 'query_bibobj.data'),
             os.path.join('data', 'query_cat.data'),
             os.path.join('data', 'query_coo.data'),
             os.path.join('data', 'query_id.data'),
             os.path.join('data', 'query_error.data')
             ]

    return {'astroquery.simbad.tests': paths}
