import os

def get_package_data():
    paths_test = [os.path.join('data', '*.html')]
    return {'astroquery.nist.tests': paths_test}
