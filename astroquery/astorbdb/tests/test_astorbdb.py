# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import os

from astroquery.utils.mocks import MockResponse
import astropy.units as u
from astropy.tests.helper import assert_quantity_allclose
from astropy.time import Time
from .. import AstInfo, AstInfoClass

# files in data/ for different query types
DATA_FILES = {'1':
              {'designations':'ceres_desig.dat',
               'elements':'ceres_elements.dat',
               'orbit':'ceres_orbit.dat',
               'albedos':'ceres_albedos.dat',
               'colors':'ceres_colors.dat',
               'taxonomies':'ceres_taxonomies.dat',
               'lightcurves':'ceres_lightcurves.dat',
               'dynamical-family':'ceres_dynfamily.dat',
               'escape-routes':'ceres_escaperoutes.dat'
               },
              'Apophis':
              {'designations':'apophis_desig.dat',
               'elements':'apophis_elements.dat',
               'orbit':'apophis_orbit.dat',
               'albedos':'apophis_albedos.dat',
               'colors':'apophis_colors.dat',
               'taxonomies':'apophis_taxonomies.dat',
               'lightcurves':'apophis_lightcurves.dat',
               'dynamical-family':'apophis_dynfamily.dat',
               'escape-routes':'apophis_escaperoutes.dat'
               },
              'Toutatis':
              {'designations':'toutatis_desig.dat',
               'elements':'toutatis_elements.dat',
               'orbit':'toutatis_orbit.dat',
               'albedos':'toutatis_albedos.dat',
               'colors':'toutatis_colors.dat',
               'taxonomies':'toutatis_taxonomies.dat',
               'lightcurves':'toutatis_lightcurves.dat',
               'dynamical-family':'toutatis_dynfamily.dat',
               'escape-routes':'toutatis_escaperoutes.dat'
               },
              'Beagle':
              {'designations':'beagle_desig.dat',
               'elements':'beagle_elements.dat',
               'orbit':'beagle_orbit.dat',
               'albedos':'beagle_albedos.dat',
               'colors':'beagle_colors.dat',
               'taxonomies':'beagle_taxonomies.dat',
               'lightcurves':'beagle_lightcurves.dat',
               'dynamical-family':'beagle_dynfamily.dat',
               'escape-routes':'beagle_escaperoutes.dat'
               },
              '2060':
              {'designations':'chiron_desig.dat',
               'elements':'chiron_elements.dat',
               'orbit':'chiron_orbit.dat',
               'albedos':'chiron_albedos.dat',
               'colors':'chiron_colors.dat',
               'taxonomies':'chiron_taxonomies.dat',
               'lightcurves':'chiron_lightcurves.dat',
               'dynamical-family':'chiron_dynfamily.dat',
               'escape-routes':'chiron_escaperoutes.dat'
               },
              '3200':
              {'designations':'phaethon_desig.dat',
               'elements':'phaethon_elements.dat',
               'orbit':'phaethon_orbit.dat',
               'albedos':'phaethon_albedos.dat',
               'colors':'phaethon_colors.dat',
               'taxonomies':'phaethon_taxonomies.dat',
               'lightcurves':'phaethon_lightcurves.dat',
               'dynamical-family':'phaethon_dynfamily.dat',
               'escape-routes':'phaethon_escaperoutes.dat'
               },
              '3556':
              {'designations':'lixiaohua_desig.dat',
               'elements':'lixiaohua_elements.dat',
               'orbit':'lixiaohua_orbit.dat',
               'albedos':'lixiaohua_albedos.dat',
               'colors':'lixiaohua_colors.dat',
               'taxonomies':'lixiaohua_taxonomies.dat',
               'lightcurves':'lixiaohua_lightcurves.dat',
               'dynamical-family':'lixiaohua_dynfamily.dat',
               'escape-routes':'lixiaohua_escaperoutes.dat'
               },
              '300163':
              {'designations':'300163_desig.dat',
               'elements':'300163_elements.dat',
               'orbit':'300163_orbit.dat',
               'albedos':'300163_albedos.dat',
               'colors':'300163_colors.dat',
               'taxonomies':'300163_taxonomies.dat',
               'lightcurves':'300163_lightcurves.dat',
               'dynamical-family':'300163_dynfamily.dat',
               'escape-routes':'300163_escaperoutes.dat'
               },
              '2024 ON':
              {'designations':'2024on_desig.dat',
               'elements':'2024on_elements.dat',
               'orbit':'2024on_orbit.dat',
               'albedos':'2024on_albedos.dat',
               'colors':'2024on_colors.dat',
               'taxonomies':'2024on_taxonomies.dat',
               'lightcurves':'2024on_lightcurves.dat',
               'dynamical-family':'2024on_dynfamily.dat',
               'escape-routes':'2024on_escaperoutes.dat'
               },
              'Ceres':
              {'designations':'ceres_missing_value_desig.dat',
               'elements':'ceres_missing_value_elements.dat',
               'orbit':'ceres_missing_value_orbit.dat',
               'albedos':'ceres_missing_value_albedos.dat',
               'colors':'ceres_missing_value_colors.dat',
               'taxonomies':'ceres_missing_value_taxonomies.dat',
               'lightcurves':'ceres_missing_value_lightcurves.dat',
               'dynamical-family':'ceres_missing_value_dynfamily.dat',
               'escape-routes':'ceres_missing_value_escaperoutes.dat'
               }
              }

ALBEDOS = {'1':0.087,
           'Apophis':None,
           'Toutatis':0.405,
           'Beagle':0.065,
           '2060':0.11,
           '3200':0.16,
           '3556':0.042,
           '300163':None,
           '2024 ON':None
          }

COLORS = {'1':0.377,
           'Apophis':None,
           'Toutatis':-0.566,
           'Beagle':0.431,
           '2060':0.334,
           '3200':0.54,
           '3556':None,
           '300163':1.26,
           '2024 ON':None
          }

DESIGS = {'1':"Ceres",
           'Apophis':"Apophis",
           'Toutatis':"Toutatis",
           'Beagle':"Beagle",
           '2060':"Chiron",
           '3200':"Phaethon",
           '3556':"Lixiaohua",
           '300163':"2006 VW139",
           '2024 ON':"2024 ON"
          }

DYNFAMILY = {'1':None,
             'Apophis':None,
             'Toutatis':None,
             'Beagle':"Themis",
             '2060':None,
             '3200':None,
             '3556':"Lixiaohua",
             '300163':None,
             '2024 ON':None
            }

ELEMENTS = {'1':2.546883130334219 * u.au,
            'Apophis':0.7460876463977817 * u.au,
            'Toutatis':0.9543335929799223 * u.au,
            'Beagle':2.741852545719269 * u.au,
            '2060':8.525493361792556 * u.au,
            '3200':0.14015636489876157 * u.au,
            '3556':2.493684653191043 * u.au,
            '300163':2.440748125244917 * u.au,
            '2024 ON':1.006933657057601 * u.au
           }

ESCAPEROUTES = {'1':None,
                'Apophis':0.87852,
                'Toutatis':0.22495,
                'Beagle':None,
                '2060':None,
                '3200':0.64189,
                '3556':None,
                '300163':None,
                '2024 ON':0.53245
               }

LIGHTCURVES = {'1':9.07417 * u.h,
               'Apophis':30.56 * u.h,
               'Toutatis':176 * u.h,
               'Beagle':7.035 * u.h,
               '2060':5.918 * u.h,
               '3200':3.604 * u.h,
               '3556':None,
               '300163':3240 * u.h,
               '2024 ON':None
              }

ORBITS = {'1':223.748 * u.yr,
          'Apophis':18.068 * u.yr,
          'Toutatis':48.588 * u.yr,
          'Beagle':116.943 * u.yr,
          '2060':129.695 * u.yr,
          '3200':41.237 * u.yr,
          '3556':59.856 * u.yr,
          '300163':22.461 * u.yr,
          '2024 ON':11.644 * u.yr
         }

TAXONOMIES = {'1':"G",
              'Apophis':"Sq",
              'Toutatis':"S",
              'Beagle':"C",
              '2060':"B",
              '3200':"F",
              '3556':None,
              '300163':None,
              '2024 ON':None
             }

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# monkeypatch replacement request function
def nonremote_request(self, method_name, **kwargs):

    path_elements = kwargs['url'].split('/')

    query_type = path_elements[-1]

    if query_type in ['designations','elements','orbit']:
        object_name = path_elements[-2]
    else:
        object_name = path_elements[-3]

    with open(data_path(DATA_FILES[object_name][query_type]), 'rb') as f:
        response = MockResponse(content=f.read(), url=self.URL)
    return response


# use a pytest fixture to create a dummy 'requests.get' function,
# that mocks(monkeypatches) the actual 'requests.get' function:
@pytest.fixture
def patch_request(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(AstInfoClass, '_request',
               nonremote_request)
    return mp


# --------------------------------- actual test functions

def test_object_queries(patch_request):
    for objectname in ALBEDOS.keys():

        astinfo = AstInfo.albedos(objectname)
        if astinfo != []:
            assert_quantity_allclose(astinfo[0]["albedo"],
                                        ALBEDOS[objectname])

        astinfo = AstInfo.colors(objectname)
        if astinfo != []:
            assert_quantity_allclose(astinfo[0]["color"],
                                        COLORS[objectname])

        astinfo = AstInfo.designations(objectname)
        if astinfo != []:
            assert astinfo["primary_designation"] == DESIGS[objectname]

        astinfo = AstInfo.dynamicalfamily(objectname)
        if astinfo != []:
            assert astinfo[0]["family"] == DYNFAMILY[objectname]

        astinfo = AstInfo.elements(objectname)
        if astinfo != []:
            assert_quantity_allclose(astinfo["q"],
                                        ELEMENTS[objectname])

        astinfo = AstInfo.escaperoutes(objectname)
        if astinfo != []:
            assert_quantity_allclose(astinfo[0]["p_nu6_complex"],
                                        ESCAPEROUTES[objectname])

        astinfo = AstInfo.lightcurves(objectname)
        if astinfo != []:
            assert_quantity_allclose(astinfo[0]["period"],
                                        LIGHTCURVES[objectname])

        astinfo = AstInfo.orbit(objectname)
        if astinfo != []:
            assert_quantity_allclose(astinfo["arc"],
                                        ORBITS[objectname])

        astinfo = AstInfo.taxonomies(objectname)
        if astinfo != []:
            assert astinfo[0]["taxonomy"] == TAXONOMIES[objectname]



def test_missing_value(patch_request):
    """test whether a missing value causes an error"""

    astinfo = AstInfo.albedos("Ceres")
    assert astinfo[0]['albedo'] is None

    astinfo = AstInfo.colors("Ceres")
    assert astinfo[0]['color'] is None

    astinfo = AstInfo.designations("Ceres")
    assert astinfo['name'] is None

    astinfo = AstInfo.dynamicalfamily("Ceres")
    assert astinfo is None

    astinfo = AstInfo.elements("Ceres")
    assert astinfo['a'] is None

    astinfo = AstInfo.escaperoutes("Ceres")
    assert astinfo is None

    astinfo = AstInfo.lightcurves("Ceres")
    assert astinfo[0]['period'] is None

    astinfo = AstInfo.orbit("Ceres")
    assert astinfo['ephname'] is None

    astinfo = AstInfo.taxonomies("Ceres")
    assert astinfo[0]['taxonomy'] is None


def test_quantities(patch_request):
    """Make sure query returns quantities"""

    astinfo = AstInfo.albedos("1")
    assert isinstance(astinfo[0]['diameter'], u.Quantity)
    assert astinfo[0]['diameter'].unit == u.km

    astinfo = AstInfo.elements("1")
    assert isinstance(astinfo['a'], u.Quantity)
    assert astinfo['a'].unit == u.au

    astinfo = AstInfo.orbit("1")
    assert isinstance(astinfo['arc'], u.Quantity)
    assert astinfo['arc'].unit == u.yr

    astinfo = AstInfo.colors("1")
    assert isinstance(astinfo[0]['jd'], Time)

    astinfo = AstInfo.lightcurves("1")
    assert isinstance(astinfo[0]['period'], u.Quantity)
    assert astinfo[0]['period'].unit == u.h

    astinfo = AstInfo.escaperoutes("3200")
    assert isinstance(astinfo[0]['epoch'], Time)
