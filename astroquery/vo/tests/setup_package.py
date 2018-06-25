import os


def get_package_data():
    paths_test = [os.path.join('data', '*.json')] + [os.path.join('data', '*.pkl')]

    return {'astroquery.vo.tests': paths_test}
