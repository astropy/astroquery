

import os.path


def get_package_data():
    return {'astroquery.atomic.tests': [os.path.join('data', '*.html')]}
