import os


def get_package_data():
    paths_test = [os.path.join('data', '*.json')] + [os.path.join('data', '*.pkl')] +  [os.path.join('data', '*.ecsv')]

    return {'astroquery.vo.tests': paths_test}
