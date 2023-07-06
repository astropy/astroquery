import os


def get_package_data():
    paths_test = [os.path.join("data", "*.json"), os.path.join("data", "*.fits")]

    return {"astroquery.mocserver.tests": paths_test}
