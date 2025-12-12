# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import os

from astroquery.utils.mocks import MockResponse
import astropy.units as u
from astropy.tests.helper import assert_quantity_allclose
from astropy.time import Time
from .. import AstInfo, AstInfoClass

# files in data/ for different query types
DATA_FILES = {'Apophis':
              {'designations': 'apophis_desig.dat',
               'elements': 'apophis_elements.dat',
               'albedos': 'apophis_albedos.dat',
               'colors': 'apophis_colors.dat',
               'taxonomies': 'apophis_taxonomies.dat',
               'lightcurves': 'apophis_lightcurves.dat',
               'dynamical-family': 'apophis_dynfamily.dat',
               'escape-routes': 'apophis_escaperoutes.dat'
               },
              'Beagle':
              {'designations': 'beagle_desig.dat',
               'elements': 'beagle_elements.dat',
               'albedos': 'beagle_albedos.dat',
               'colors': 'beagle_colors.dat',
               'taxonomies': 'beagle_taxonomies.dat',
               'lightcurves': 'beagle_lightcurves.dat',
               'dynamical-family': 'beagle_dynfamily.dat',
               'escape-routes': 'beagle_escaperoutes.dat'
               },
              '3556':
              {'designations': 'lixiaohua_desig.dat',
               'elements': 'lixiaohua_elements.dat',
               'albedos': 'lixiaohua_albedos.dat',
               'colors': 'lixiaohua_colors.dat',
               'taxonomies': 'lixiaohua_taxonomies.dat',
               'lightcurves': 'lixiaohua_lightcurves.dat',
               'dynamical-family': 'lixiaohua_dynfamily.dat',
               'escape-routes': 'lixiaohua_escaperoutes.dat'
               },
              'Ceres':
              {'designations': 'ceres_missing_value_desig.dat',
               'elements': 'ceres_missing_value_elements.dat',
               'albedos': 'ceres_missing_value_albedos.dat',
               'colors': 'ceres_missing_value_colors.dat',
               'taxonomies': 'ceres_missing_value_taxonomies.dat',
               'lightcurves': 'ceres_missing_value_lightcurves.dat',
               'dynamical-family': 'ceres_missing_value_dynfamily.dat',
               'escape-routes': 'ceres_missing_value_escaperoutes.dat'
               }
              }

ALBEDOS = {'Apophis': None,
           'Beagle': 0.065,
           '3556': 0.042,
           }

COLORS = {'Apophis': None,
          'Beagle': 0.431,
          '3556': None,
          }

DESIGS = {'Apophis': 'Apophis',
          'Beagle': 'Beagle',
          '3556': 'Lixiaohua',
          }

DYNFAMILY = {'Apophis': None,
             'Beagle': 'Themis',
             '3556': 'Lixiaohua',
             }

ELEMENTS = {'Apophis': 0.7460876463977817 * u.au,
            'Beagle': 2.741852545719269 * u.au,
            '3556': 2.493684653191043 * u.au,
            }

ESCAPEROUTES = {'Apophis': 0.87852,
                'Beagle': None,
                '3556': None,
                }

LIGHTCURVES = {'Apophis': 30.56 * u.h,
               'Beagle': 7.035 * u.h,
               '3556': None,
               }

TAXONOMIES = {'Apophis': 'Sq',
              'Beagle': 'C',
              '3556': None,
              }


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# monkeypatch replacement request function
def nonremote_request(self, method_name, **kwargs):

    path_elements = kwargs['url'].split('/')

    query_type = path_elements[-1]

    if query_type in ['designations', 'elements']:
        object_name = path_elements[-2]
    else:
        object_name = path_elements[-3]

    with open(data_path(DATA_FILES[object_name][query_type]), 'rb') as f:
        if query_type in ['designations', 'elements']:
            response = MockResponse(content=f.read(), url=self.URL + object_name + '/' + query_type)
        else:
            response = MockResponse(content=f.read(), url=self.URL + object_name + '/data/' + query_type)

    return response


# use a pytest fixture to create a dummy 'requests.get' function,
# that mocks(monkeypatches) the actual 'requests.get' function:
@pytest.fixture
def patch_request(request):
    mp = request.getfixturevalue('monkeypatch')

    mp.setattr(AstInfoClass, '_request',
               nonremote_request)
    return mp


# --------------------------------- actual test functions

def test_object_queries(patch_request):
    for objectname in ALBEDOS.keys():

        astinfo = AstInfo.albedos(objectname)
        if astinfo != []:
            assert_quantity_allclose(astinfo[0]['albedo'],
                                     ALBEDOS[objectname])

        astinfo = AstInfo.colors(objectname)
        if astinfo != []:
            assert_quantity_allclose(astinfo[0]['color'],
                                     COLORS[objectname])

        astinfo = AstInfo.designations(objectname)
        if astinfo != []:
            assert astinfo['primary_designation'] == DESIGS[objectname]

        astinfo = AstInfo.dynamical_family(objectname)
        if astinfo != []:
            assert astinfo[0]['family'] == DYNFAMILY[objectname]

        astinfo = AstInfo.elements(objectname)
        if astinfo != []:
            assert_quantity_allclose(astinfo['q'],
                                     ELEMENTS[objectname])

        astinfo = AstInfo.escape_routes(objectname)
        if astinfo != []:
            assert_quantity_allclose(astinfo[0]['p_nu6_complex'],
                                     ESCAPEROUTES[objectname])

        astinfo = AstInfo.lightcurves(objectname)
        if astinfo != []:
            assert_quantity_allclose(astinfo[0]['period'],
                                     LIGHTCURVES[objectname])

        astinfo = AstInfo.taxonomies(objectname)
        if astinfo != []:
            assert astinfo[0]['taxonomy'] == TAXONOMIES[objectname]

        astinfo = AstInfo.all_astinfo(objectname)
        if astinfo != []:
            assert astinfo['designations']['primary_designation'] == DESIGS[objectname]


def test_missing_value(patch_request):
    """test whether a missing value causes an error"""

    astinfo = AstInfo.albedos('Ceres')
    assert astinfo[0]['albedo'] is None

    astinfo = AstInfo.colors('Ceres')
    assert astinfo[0]['color'] is None

    astinfo = AstInfo.designations('Ceres')
    assert astinfo['name'] is None

    astinfo = AstInfo.dynamical_family('Ceres')
    assert astinfo is None

    astinfo = AstInfo.elements('Ceres')
    assert astinfo['a'] is None

    astinfo = AstInfo.escape_routes('Ceres')
    assert astinfo is None

    astinfo = AstInfo.lightcurves('Ceres')
    assert astinfo[0]['period'] is None

    astinfo = AstInfo.taxonomies('Ceres')
    assert astinfo[0]['taxonomy'] is None


def test_quantities(patch_request):
    """Make sure query returns quantities"""

    astinfo = AstInfo.albedos('Beagle')
    assert isinstance(astinfo[0]['diameter'], u.Quantity)
    assert astinfo[0]['diameter'].unit == u.km

    astinfo = AstInfo.colors('Beagle')
    assert isinstance(astinfo[0]['jd'], Time)

    astinfo = AstInfo.elements('Beagle')
    assert isinstance(astinfo['a'], u.Quantity)
    assert astinfo['a'].unit == u.au

    astinfo = AstInfo.escape_routes('Apophis')
    assert isinstance(astinfo[0]['epoch'], Time)

    astinfo = AstInfo.lightcurves('Beagle')
    assert isinstance(astinfo[0]['period'], u.Quantity)
    assert astinfo[0]['period'].unit == u.h


def test_urls(patch_request):
    """Make sure URL query request returns URLs"""

    astinfo = AstInfo.albedos('Beagle', get_uri=True)
    assert astinfo[0]['query_uri'] == 'https://asteroid.lowell.edu/api/asteroids/Beagle/data/albedos'

    astinfo = AstInfo.colors('Beagle', get_uri=True)
    assert astinfo[0]['query_uri'] == 'https://asteroid.lowell.edu/api/asteroids/Beagle/data/colors'

    astinfo = AstInfo.designations('Beagle', get_uri=True)
    assert astinfo['query_uri'] == 'https://asteroid.lowell.edu/api/asteroids/Beagle/designations'

    astinfo = AstInfo.dynamical_family('Beagle', get_uri=True)
    assert astinfo[0]['query_uri'] == 'https://asteroid.lowell.edu/api/asteroids/Beagle/data/dynamical-family'

    astinfo = AstInfo.elements('Beagle', get_uri=True)
    assert astinfo['query_uri'] == 'https://asteroid.lowell.edu/api/asteroids/Beagle/elements'

    astinfo = AstInfo.escape_routes('Beagle', get_uri=True)
    assert astinfo[0]['query_uri'] == 'https://asteroid.lowell.edu/api/asteroids/Beagle/data/escape-routes'

    astinfo = AstInfo.lightcurves('Beagle', get_uri=True)
    assert astinfo[0]['query_uri'] == 'https://asteroid.lowell.edu/api/asteroids/Beagle/data/lightcurves'

    astinfo = AstInfo.taxonomies('Beagle', get_uri=True)
    assert astinfo[0]['query_uri'] == 'https://asteroid.lowell.edu/api/asteroids/Beagle/data/taxonomies'

    astinfo = AstInfo.all_astinfo('Beagle', get_uri=True)
    assert astinfo['query_uri']['albedos'] == 'https://asteroid.lowell.edu/api/asteroids/Beagle/data/albedos'
