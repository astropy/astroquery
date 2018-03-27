# Licensed under a 3-clause BSD style license - see LICENSE.rst


def get_package_data():
    return {
        'astroquery.vo_conesearch.validator': ['data/*.txt'],
        'astroquery.vo_conesearch.validator.tests': ['data/*.json',
                                                     'data/*.xml',
                                                     'data/*.out']}


def requires_2to3():
    return False
