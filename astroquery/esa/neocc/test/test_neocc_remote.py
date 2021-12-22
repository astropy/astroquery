# -*- coding: utf-8 -*-
"""
This module contains all the remote tests. The data for these
tests is requested to ESA NEOCC portal.

* Project: NEOCC portal Python interface
* Property: European Space Agency (ESA)
* Developed by: Elecnor Deimos
* Author: C. Álvaro Arroyo Parejo
* Date: 02-11-2021

© Copyright [European Space Agency][2021]
All rights reserved
"""


import io
import os
import re

import random
import pytest
import pandas as pd
import pandas.testing as pdtesting
import pandas.api.types as ptypes
import requests

from astroquery.esa.neocc.__init__ import conf
from astroquery.esa.neocc import neocc, lists, tabs

import astropy

# Import BASE URL and TIMEOUT
API_URL = conf.API_URL
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
TIMEOUT = conf.TIMEOUT
VERIFICATION = conf.SSL_CERT_VERIFICATION

@astropy.tests.helper.remote_data
class TestLists:
    """Class which contains the unitary tests for lists module.
    """
    # Dictionary for lists
    lists_dict = {
        "nea_list": 'allneo.lst',
        "updated_nea": 'updated_nea.lst',
        "monthly_update": 'monthly_update.done',
        "risk_list": 'esa_risk_list',
        "risk_list_special": 'esa_special_risk_list',
        "close_approaches_upcoming": 'esa_upcoming_close_app',
        "close_approaches_recent": 'esa_recent_close_app',
        "priority_list": 'esa_priority_neo_list',
        "priority_list_faint": 'esa_faint_neo_list',
        "close_encounter" : 'close_encounter2.txt',
        "impacted_objects" : 'impactedObjectsList.txt',
        "neo_catalogue_current" : 'neo_kc.cat',
        "neo_catalogue_middle" : 'neo_km.cat'
        }

    def test_get_list_url(self):
        """Test for checking the URL termination for requested lists.
        Check invalid list name raise KeyError.
        """
        # Valid inputs
        valid_names = ["nea_list", "updated_nea", "monthly_update",
                       "risk_list", "risk_list_special",
                       "close_approaches_upcoming",
                       "close_approaches_recent",
                       "priority_list", "priority_list_faint",
                       "close_encounter", "impacted_objects"]
        # Invalid inputs
        bad_names = ["ASedfe", "%&$", "ÁftR+", 154]
        # Assert for valid names
        for element in valid_names:
            assert lists.get_list_url(element) == \
                   self.lists_dict[element]
        # Assert for invalid names
        for elements in bad_names:
            with pytest.raises(KeyError):
                lists.get_list_url(elements)


    def test_get_list_data(self):
        """Check data obtained is pandas.DataFrame or pandas.Series
        """
        # Check pd.Series output
        list_series = ["nea_list", "updated_nea", "monthly_update"]
        for series in list_series:
            assert isinstance(lists.get_list_data(self.\
                              lists_dict[series], series), pd.Series)
        # Check pd.DataFrame output
        list_dfs = ["risk_list", "risk_list_special",
                    "close_approaches_upcoming",
                    "close_approaches_recent", "priority_list",
                    "close_encounter", "priority_list_faint",
                    "impacted_objects"]
        for dfs in list_dfs:
            assert isinstance(lists.get_list_data(self.\
                              lists_dict[dfs], dfs), pd.DataFrame)


    def test_parse_list(self):
        """Check data obtained is pandas.DataFrame or pandas.Series
        """
        # Check pd.Series output
        url_series = ["nea_list", "updated_nea", "monthly_update"]
        for url in url_series:
            # Get data from URL
            data_list = requests.get(API_URL + self.lists_dict[url],
                                     timeout=TIMEOUT,
                                     verify=VERIFICATION).content
            # Decode the data using UTF-8
            data_list_d = io.StringIO(data_list.decode('utf-8'))

            assert isinstance(lists.parse_list(url, data_list_d),
                                                    pd.Series)
        # Check pd.DataFrame output
        url_dfs = ["risk_list", "risk_list_special",
                   "close_approaches_upcoming",
                   "close_approaches_recent", "priority_list",
                   "close_encounter", "priority_list_faint",
                   "impacted_objects"]
        for url in url_dfs:
            # Get data from URL
            data_list = requests.get(API_URL + self.lists_dict[url],
                                     timeout=TIMEOUT,
                                     verify=VERIFICATION).content
            # Decode the data using UTF-8
            data_list_d = io.StringIO(data_list.decode('utf-8'))

            assert isinstance(lists.parse_list(url, data_list_d),
                                                    pd.DataFrame)
        # Invalid inputs
        bad_names = ["ASedfe", "%&$", "ÁftR+", 154]
        # Assert for invalid names
        for elements in bad_names:
            with pytest.raises(KeyError):
                lists.parse_list(elements, data_list_d)


    def test_parse_nea(self):
        """Check data: nea list, updated nea list and monthly update
        """
        url_series = ["nea_list", "updated_nea", "monthly_update"]
        for url in url_series:
            # Get data from URL
            data_list = requests.get(API_URL + self.lists_dict[url],
                                     timeout=TIMEOUT,
                                     verify=VERIFICATION).content
            # Decode the data using UTF-8
            data_list_d = io.StringIO(data_list.decode('utf-8'))
            # Parse using parse_nea
            new_list = lists.parse_nea(data_list_d)
            # Assert is a pandas Series
            assert isinstance(new_list, pd.Series)
            # Assert is not empty
            assert not new_list.empty
            # List of all NEAs
            if url == "nea_list":
                filename = os.path.join(DATA_DIR, self.lists_dict[url])
                content = open(filename, 'r')
                nea_list = pd.read_csv(content, header=None)
                # Remove whitespaces
                nea_list = nea_list[0].str.strip().replace(r'\s+', ' ',
                                                           regex=True)\
                                      .str.replace('# ', '')
                # Check size of the data frame
                assert len(new_list.index) > 20000
                # Check 74 first elements are equal from reference
                # data (since provisional designator may change)
                pdtesting.assert_series_equal(new_list[0:74], nea_list[0:74])
            else:
                # Check date format DDD MMM DD HH:MM:SS UTC YYYY
                assert re.match(r'\w{3} \w{3} \d{2} \d{2}:\d{2}:\d{2} '
                                r'\w{3} \d{4}', new_list.iloc[0])


    def test_parse_risk(self):
        """Check data: risk_list, risk_list_special
        """
        url_risks = ['risk_list', 'risk_list_special']
        # Columns of risk lists
        risk_columns = ['Object Name', 'Diameter in m', '*=Y',
                        'Date/Time', 'IP max', 'PS max', 'TS',
                        'Vel in km/s', 'First year', 'Last year',
                        'IP cum', 'PS cum']
        risk_special_columns = risk_columns[0:8]

        for url in url_risks:
            # Get data from URL
            data_list = requests.get(API_URL + self.lists_dict[url],
                                     timeout=TIMEOUT,
                                     verify=VERIFICATION).content
            # Decode the data using UTF-8
            data_list_d = io.StringIO(data_list.decode('utf-8'))
            # Parse using parse_nea
            new_list = lists.parse_risk(data_list_d)
            # Assert is a pandas DataFrame
            assert isinstance(new_list, pd.DataFrame)

            if url == 'risk_list':
                # Assert dataframe is not empty, columns names, length
                assert not new_list.empty
                assert (new_list.columns == risk_columns).all()
                assert len(new_list.index) > 1000
                # Assert columns data types
                # Floats
                float_cols = ['Diameter in m', 'IP max', 'PS max',
                              'Vel in km/s', 'IP cum', 'PS cum']
                assert all(ptypes.is_float_dtype(new_list[cols1])\
                    for cols1 in float_cols)
                # int64
                int_cols = ['TS', 'First year', 'Last year']
                assert all(ptypes.is_int64_dtype(new_list[cols2])\
                    for cols2 in int_cols)
                # Object
                object_cols = ['Object Name', '*=Y']
                assert all(ptypes.is_object_dtype(new_list[cols3])\
                    for cols3 in object_cols)
                # Datetime
                assert ptypes.is_datetime64_ns_dtype(
                        new_list['Date/Time'])

            else:
            # Currently risk special list is empty
                assert new_list.empty
                assert (new_list.columns == risk_special_columns).all()


    def test_parse_clo(self):
        """Check data: close_approaches_upcoming,
        close_approaches_recent
        """
        url_close = ['close_approaches_upcoming',
                   'close_approaches_recent']
        # Columns of close approaches lists
        close_columns = ['Object Name', 'Date',
                         'Miss Distance in km', 'Miss Distance in au',
                         'Miss Distance in LD', 'Diameter in m',
                         '*=Yes', 'H', 'Max Bright',
                         'Rel. vel in km/s']

        for url in url_close:
            # Get data from URL
            data_list = requests.get(API_URL + self.lists_dict[url],
                                     timeout=TIMEOUT,
                                     verify=VERIFICATION).content
            # Decode the data using UTF-8
            data_list_d = io.StringIO(data_list.decode('utf-8'))
            # Parse using parse_nea
            new_list = lists.parse_clo(data_list_d)
            # Assert is a pandas DataFrame
            assert isinstance(new_list, pd.DataFrame)
            # Assert dataframe is not empty, columns names and length
            assert not new_list.empty
            assert (new_list.columns == close_columns).all()
            assert len(new_list.index) > 100
            # Assert Connection Error. In case of internal server error
            # the request provided an empty file
            foo_error = io.StringIO('This site cant be reached\n'
                                    'domain.com regused to connect\n'
                                    'Search Google for domain\n'
                                    'ERR_CONNECTION_REFUSED')
            with pytest.raises(ConnectionError):
                lists.parse_clo(foo_error)

            # Assert columns data types
            # Floats
            float_cols = ['Miss Distance in au',
                          'Miss Distance in LD', 'Diameter in m', 'H',
                          'Max Bright', 'Rel. vel in km/s']
            assert all(ptypes.is_float_dtype(new_list[cols1])\
                for cols1 in float_cols)
            # int64
            assert ptypes.is_int64_dtype(new_list['Miss Distance in km'])
            # Object
            object_cols = ['Object Name', '*=Yes']
            assert all(ptypes.is_object_dtype(new_list[cols3])\
                for cols3 in object_cols)
            # Datetime
            assert ptypes.is_datetime64_ns_dtype(new_list['Date'])


    def test_parse_pri(self):
        """Check data: priority_list, priority_list_faint
        """
        url_priority = ['priority_list', 'priority_list_faint']
        # Columns of close approaches lists
        priority_columns = ['Priority', 'Object',
                            'R.A. in arcsec', 'Decl. in deg',
                            'Elong. in deg', 'V in mag', 'Sky uncert.',
                            'End of Visibility']

        for url in url_priority:
            # Get data from URL
            data_list = requests.get(API_URL + self.lists_dict[url],
                                     timeout=TIMEOUT,
                                     verify=VERIFICATION).content
            # Decode the data using UTF-8
            data_list_d = io.StringIO(data_list.decode('utf-8'))
            # Parse using parse_nea
            new_list = lists.parse_pri(data_list_d)
            # Assert is a pandas DataFrame
            assert isinstance(new_list, pd.DataFrame)
            # Assert dataframe is not empty, columns names and length
            assert not new_list.empty
            assert (new_list.columns == priority_columns).all()
            assert len(new_list.index) > 100
            # Assert columns data types
            # Floats
            float_cols = ['R.A. in arcsec', 'Decl. in deg',
                          'V in mag']
            assert all(ptypes.is_float_dtype(new_list[cols1])\
                for cols1 in float_cols)
            # int64
            int_cols = ['Priority', 'Elong. in deg', 'Sky uncert.']
            assert all(ptypes.is_int64_dtype(new_list[cols2])\
                for cols2 in int_cols)
            # Object
            assert ptypes.is_object_dtype(new_list['Object'])
            # Datetime
            assert ptypes.is_datetime64_ns_dtype(
                       new_list['End of Visibility'])


    def test_parse_encounter(self):
        """Check data: close_encounter
        """
        url = 'close_encounter'
        # Columns of close approaches lists
        encounter_columns = ['Name/desig', 'Planet', 'Date',
                             'Time approach', 'Time uncert',
                             'Distance', 'Minimum distance',
                             'Distance uncertainty', 'Width',
                             'Stretch', 'Probability', 'Velocity',
                             'Max Mag']

        # Get data from URL
        data_list = requests.get(API_URL + self.lists_dict[url],
                                 timeout=TIMEOUT,
                                 verify=VERIFICATION).content
        # Decode the data using UTF-8
        data_list_d = io.StringIO(data_list.decode('utf-8'))
        # Parse using parse_nea
        new_list = lists.parse_encounter(data_list_d)
        # Assert is a pandas DataFrame
        assert isinstance(new_list, pd.DataFrame)
        # Assert dataframe is not empty, columns names and length
        assert not new_list.empty
        assert (new_list.columns == encounter_columns).all()
        assert len(new_list.index) > 100000
        # Assert columns data types
        # Floats
        float_cols = encounter_columns[3:]
        assert all(ptypes.is_float_dtype(new_list[cols1])\
            for cols1 in float_cols)
        # Object
        object_cols = ['Name/desig', 'Planet']
        assert all(ptypes.is_object_dtype(new_list[cols2])\
            for cols2 in object_cols)
        # Datetime
        assert ptypes.is_datetime64_ns_dtype(new_list['Date'])
        # Assert Connection Error. In case of internal server error
        # the request provided an empty file
        foo_error = io.StringIO('This site cant be reached\n'
                                'domain.com regused to connect\n'
                                'Search Google for domain\n'
                                'ERR_CONNECTION_REFUSED')
        with pytest.raises(ConnectionError):
            lists.parse_encounter(foo_error)


    def test_parse_impacted(self):
        """Check data: impacted_objects
        """
        url = 'impacted_objects'
        # Get data from URL
        data_list = requests.get(API_URL + self.lists_dict[url],
                                 timeout=TIMEOUT,
                                 verify=VERIFICATION).content
        # Decode the data using UTF-8
        data_list_d = io.StringIO(data_list.decode('utf-8'))
        # Parse using parse_nea
        new_list = lists.parse_impacted(data_list_d)
        # Assert is a pandas DataFrame
        assert isinstance(new_list, pd.DataFrame)
        # Assert dataframe is not empty and length
        assert not new_list.empty
        assert len(new_list.index) < 100
        # Assert columns data types
        # Object
        assert ptypes.is_object_dtype(new_list[0])
        # Datetime
        assert ptypes.is_datetime64_ns_dtype(new_list[1])


    def test_parse_neo_catalogue(self):
        """Check data: close_encounter
        """
        url_cat = ['neo_catalogue_current',
                   'neo_catalogue_middle']
        # Columns of close approaches lists
        cat_columns = ['Name', 'Epoch (MJD)', 'a', 'e', 'i',
                       'long. node', 'arg. peric.', 'mean anomaly',
                       'absolute magnitude', 'slope param.',
                       'non-grav param.']
        for url in url_cat:
            # Get data from URL
            data_list = requests.get(API_URL + self.lists_dict[url],
                                     timeout=TIMEOUT,
                                     verify=VERIFICATION).content
            # Decode the data using UTF-8
            data_list_d = io.StringIO(data_list.decode('utf-8'))
            # Parse using parse_nea
            new_list = lists.parse_neo_catalogue(data_list_d)
            # Assert is a pandas DataFrame
            assert isinstance(new_list, pd.DataFrame)
            # Assert dataframe is not empty, columns names and length
            assert not new_list.empty
            assert (new_list.columns == cat_columns).all()
            assert len(new_list.index) > 10000
            # Assert columns data types
            # Floats
            float_cols = ['Epoch (MJD)', 'a', 'e', 'i',
                        'long. node', 'arg. peric.', 'mean anomaly',
                        'absolute magnitude', 'slope param.']
            assert all(ptypes.is_float_dtype(new_list[cols1])\
                for cols1 in float_cols)
            # Object
            assert ptypes.is_object_dtype(new_list['Name'])
            # Int
            assert ptypes.is_int64_dtype(new_list['non-grav param.'])

@astropy.tests.helper.remote_data
class TestTabs:
    """Class which contains the unitary tests for tabs module.
    """
    path_nea = 'test/data/allneo.lst'
    nea_list = pd.read_csv(path_nea, header=None)
    nea_list = nea_list[0].str.strip().replace(r'\s+', ' ',
                                               regex=True)\
                                      .str.replace('# ', '')

    def test_get_object_url(self):
        """Test for checking the URL termination for requested object tab.
        Check invalid list name raise KeyError.
        """
        # Dictionary for tabs
        tab_dict = {
                "impacts": '.risk',
                "close_approaches": '.clolin',
                "observations": '.rwo',
                "physical_properties": '.phypro',
                "orbit_properties": ['.ke0', '.ke1', '.eq0', '.eq1']
                }
        # Choose a random object from stored nea list
        rnd_object = random.choice(self.nea_list)
        # Tabs to test
        object_tabs = ['impacts', 'close_approaches',
                       'observations', 'orbit_properties', '&cefrgfe',
                       4851]
        # Possible additional argument
        orbit_epoch = ['present', 'middle']
        # Iterate to obtain all possible urls
        for tab in object_tabs:
            if tab == 'orbit_properties':
                for epoch in orbit_epoch:
                    with pytest.raises(ValueError):
                        tabs.get_object_url(rnd_object, tab,
                        orbital_elements=None, orbit_epoch=epoch)
            elif tab in ['&cefrgfe', 4851]:
                with pytest.raises(KeyError):
                    tabs.get_object_url(rnd_object, tab)
            else:
                assert tabs.get_object_url(rnd_object, tab) ==\
                    str(rnd_object).replace(' ', '%20') +\
                    tab_dict[tab]


    def test_get_object_data(self):
        """Test for obtaining the content of a URL.
        """
        # Choose a random object from stored nea list
        rnd_object = random.choice(self.nea_list)
        # Tabs used in url function
        object_tabs = ['impacts', 'close_approaches',
                       'observations', 'orbit_properties',
                       'physical_properties']
        # Possible additional argument
        orbital_element = ['keplerian', 'equinoctial']
        orbit_epoch = ['present', 'middle']
        # Iterate to obtain all possible urls
        for tab in object_tabs:
            if tab == 'orbit_properties':
                for element in orbital_element:
                    for epoch in orbit_epoch:
                        url = tabs.get_object_url(rnd_object, tab,
                        orbital_elements=element, orbit_epoch=epoch)
                        assert isinstance(tabs.get_object_data(url),
                                          bytes)
            else:
                url = tabs.get_object_url(rnd_object, tab)
                assert isinstance(tabs.get_object_data(url), bytes)

    @classmethod
    def test_get_indexess(cls):
        """Test for obtaining the proper indexes of a DataFrame.
        """
        test_data = {'col1': [1, float(2), 'str1', '&'],
                     'col2': [3, 4.0, 'str2', 1],
                     3: ['str3', 0, int(2), '%']}
        data =  pd.DataFrame(test_data)
        assert tabs.get_indexes(data, 'str1') == [(2, 'col1')]
        assert tabs.get_indexes(data, 'str1')[0] == (2, 'col1')
        assert tabs.get_indexes(data, 1) == [(0, 'col1'), (3, 'col2')]
        assert tabs.get_indexes(data, 4.0) == [(1, 'col2')]
        # Assert can work with different types
        assert tabs.get_indexes(data, 2) == [(1, 'col1'), (2, 3)]
        assert bool(tabs.get_indexes(data, None)) is False

    @classmethod
    def test_tabs_names(cls):
        """Test is a invalid name
        """
        # Invalid inputs
        bad_names = ["ASedfe", "%&$", "ÁftR+", 154]
        for element in bad_names:
            with pytest.raises(KeyError):
                neocc.query_object(name='433', tab=element)


    def test_tabs_summary(self):
        """Check data: summary tab
        """
        # Check value error if empty
        with pytest.raises(ValueError):
            neocc.query_object(name='foo', tab='summary')
        # Choose a random object from stored nea list
        rnd_object = random.choice(self.nea_list)
        # Request summary and check types
        summary = neocc.query_object(name=rnd_object, tab='summary')
        dict_attributes = {
            'discovery_date'        : str,
            'observatory'           : str,
            'physical_properties'   : pd.DataFrame
            }
        for attribute in dict_attributes:
            # Check attributes exist and their type
            assert hasattr(summary, attribute)
            # Add type str in tuple for those objects whose
            # observations are strings
            assert isinstance(getattr(summary, attribute),
                              dict_attributes[attribute])
        # Assert size of physical properties file
        assert not summary.physical_properties.empty
        assert summary.physical_properties.shape == (4, 3)
        summary_cols = ['Physical Properties', 'Value', 'Units']
        assert (summary.physical_properties.columns ==\
                summary_cols).all()
        # Assert dtype
        assert all(ptypes.is_object_dtype(summary.\
            physical_properties[cols1]) for cols1 in summary_cols)
        # Check specific asteroids that will remain inmutable
        ast_summ1 = neocc.query_object(name='433', tab='summary')
        assert ast_summ1.observatory == 'Berlin (1835-1913)'
        assert ast_summ1.discovery_date == '1898-08-13'
        # Check asteroid with no observatory nor discovery date
        # This object may change
        ast_summ2 = neocc.query_object(name='2006BV4', tab='summary')
        assert ast_summ2.observatory ==\
            'Observatory is not available'
        assert ast_summ2.discovery_date ==\
            'Discovery date is not available'
