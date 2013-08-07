import os

def get_package_data():
    paths_test = [os.path.join('data', '*.imfits'),
                  os.path.join('data', '*.html')]

    return {'astroquery.nrao.tests': paths_test}
