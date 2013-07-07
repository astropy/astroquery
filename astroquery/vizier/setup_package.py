import os

def get_package_data():
    paths_test = [os.path.join('data', 'vii258.txt'),
                  os.path.join('data', 'ii246.txt')]

    paths_core = [os.path.join('data', 'inverse_dict.json'),
                  os.path.join('data', 'keywords_dict.json')]

    return {
            'astroquery.vizier.tests': paths_test,
            'astroquery.vizier': paths_core
           }
