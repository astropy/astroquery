import os

def get_package_data():
    paths_core = [os.path.join('data', 'keywords_dict.json')]

    return {
            'astroquery.ned': paths_core
           }
