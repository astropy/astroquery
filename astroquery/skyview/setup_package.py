import os


def get_package_data():
    return {'astroquery.skyview.tests': [os.path.join('data', '*.html')]}
