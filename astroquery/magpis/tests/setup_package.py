import os

def get_package_data():
    paths_test = [os.path.join('data', '*.fits')]

    return {'astroquery.magpis.tests': paths_test}
