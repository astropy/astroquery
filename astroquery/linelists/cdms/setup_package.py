# Licensed under a 3-clause BSD style license - see LICENSE.rst


import os


def get_package_data():

    paths_test = [os.path.join('data', '028503 CO, v=0.data'),
                  os.path.join('data', '117501 HC7S.data'),
                  os.path.join('data', '099501 HC7N, v=0.data'),
                  os.path.join('data', 'post_response.html'),
                  ]

    paths_data = [os.path.join('data', 'catdir.cat'),
                  os.path.join('data', 'partfunc.cat')]

    return {'astroquery.linelists.cdms.tests': paths_test,
            'astroquery.linelists.cdms': paths_data, }
