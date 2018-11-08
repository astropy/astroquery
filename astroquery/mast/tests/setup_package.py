import os


def get_package_data():
    paths_test = [os.path.join('data', '*.json'),
                  os.path.join('data', '*.extjs'),
                  os.path.join('data', '*.zip')]

    return {'astroquery.mast.tests': paths_test}
