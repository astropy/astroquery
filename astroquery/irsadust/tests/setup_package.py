import os

def get_package_data():
    return { 'astroquery.irsadust.tests': [os.path.join('t', '*.xml'),
                                    os.path.join('t', '*.fits'),
                                    os.path.join('t', '*.tbl'),
                                    os.path.join('t', '*.txt')]}

