import os


def get_package_data():
    return {'astroquery.xmatch.tests': [os.path.join('data', '*.html')]}
