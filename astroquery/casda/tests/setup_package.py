import os


def get_package_data():
    paths_test = [os.path.join('data', '*.xml')]

    return {'astroquery.module.tests': paths_test}