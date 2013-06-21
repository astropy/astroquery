import os

def get_package_data():
    paths = [os.path.join('data', 'datam31'),
             os.path.join('data', 'datamulti')]
    return { 'astroquery.simbad.tests': paths}
