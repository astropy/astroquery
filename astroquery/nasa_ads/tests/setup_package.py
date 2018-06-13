import os


def get_package_data():
    paths_test = [os.path.join('data', '*.txt')]

    return {'astroquery.module.tests': paths_test}
