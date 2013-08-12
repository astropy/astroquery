import os

def get_package_data():
    paths_test = [os.path.join('data', '*.xml')]
    return {'astroquery.irsa.tests': paths_test}
