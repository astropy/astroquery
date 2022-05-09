import os


def get_package_data():
    paths = [os.path.join("data", "*.html")]  # etc, add other extensions

    return {"astroquery.solarsystem.pds.tests": paths}
