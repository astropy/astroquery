import os

def get_package_data():
    paths = [os.path.join('data', 'vii258.txt'),
             os.path.join('data', 'ii246.txt')]

    return { 'astroquery.vizier.tests': paths}
