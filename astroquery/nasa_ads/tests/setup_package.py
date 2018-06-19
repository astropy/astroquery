import os


def get_package_data():
    paths_test = [os.path.join('data', '*.txt')]

    return {'astroquery.nasa_ads.tests': paths_test}
