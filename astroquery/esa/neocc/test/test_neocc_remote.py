# -*- coding: utf-8 -*-
"""
This module contains all the remote tests. The data for these
tests is requested to ESA NEOCC portal.

* Project: NEOCC portal Python interface
* Property: European Space Agency (ESA)
* Developed by: Elecnor Deimos
* Author: C. Álvaro Arroyo Parejo
* Date: 21-08-2022
"""

import os
import re
import random
import pytest
import requests
import warnings

import numpy as np

from astropy.table import Table
from astropy.time import Time

from astroquery.esa import neocc

# Import BASE URL and TIMEOUT
API_URL = neocc.conf.API_URL
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
TIMEOUT = neocc.conf.TIMEOUT
VERIFICATION = neocc.conf.SSL_CERT_VERIFICATION


@pytest.mark.filterwarnings('ignore:ERFA function *:erfa.core.ErfaWarning')
@pytest.mark.remote_data
class TestLists:
    """Class which contains the unitary tests for lists module.

    Ignore ERFA 'dubious year' warnings because they are expected.
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
        "close_encounter": 'close_encounter2.txt',
        "impacted_objects": 'past_impactors_list',
        "neo_catalogue_current": 'neo_kc.cat',
        "neo_catalogue_middle": 'neo_km.cat'
    }

    # Ignore the FutureWarning that only comes up with the oldest dependencies
    warnings.filterwarnings("ignore", category=FutureWarning,
                            message="Conversion of the second argument of issubdtype*")

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
            assert neocc.lists.get_list_url(element) == self.lists_dict[element]
        # Assert for invalid names
        for elements in bad_names:
            with pytest.raises(KeyError):
                neocc.lists.get_list_url(elements)

    def test_get_list_data(self):
        """Check data obtained is an astropy Table
        """
        # Check pd.Series output
        list_names = ["nea_list", "updated_nea", "monthly_update", "risk_list", "risk_list_special",
                      "close_approaches_upcoming", "close_approaches_recent", "priority_list",
                      "close_encounter", "priority_list_faint", "impacted_objects"]
        for series in list_names:
            assert isinstance(neocc.lists.get_list_data(self.lists_dict[series], series), Table)

    def test_parse_list(self):
        """Check data obtained is an astropy Table
        """
        # Check pd.Series output
        url_list = ["nea_list", "updated_nea", "monthly_update", "risk_list", "risk_list_special",
                    "close_approaches_upcoming", "close_approaches_recent", "priority_list",
                    "close_encounter", "priority_list_faint", "impacted_objects"]

        for url in url_list:
            # Get data from URL
            data_list = requests.get(API_URL + self.lists_dict[url],
                                     timeout=TIMEOUT,
                                     verify=VERIFICATION).content
            # Decode the data using UTF-8
            data_list_d = data_list.decode('utf-8')

            assert isinstance(neocc.lists.parse_list(url, data_list_d), Table)

        # Invalid inputs
        bad_names = ["ASedfe", "%&$", "ÁftR+", 154]
        # Assert for invalid names
        for elements in bad_names:
            with pytest.raises(KeyError):
                neocc.lists.parse_list(elements, data_list_d)

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
            data_list_d = data_list.decode('utf-8')
            # Parse using parse_nea
            new_list = neocc.lists.parse_nea(data_list_d)
            # Assert is a pandas Series
            assert isinstance(new_list, Table)
            # Assert is not empty
            assert len(new_list)

            # List of all NEAs
            if url == "nea_list":

                # Check size of the result
                assert len(new_list) > 20000

                filename = os.path.join(DATA_DIR, "allnea.csv")
                nea_list = Table.read(filename, format="ascii.csv")

                # Check 74 first elements are equal from reference data
                # (since provisional designator may change)
                assert (new_list[:74] == nea_list[:74]).all()
            else:
                # Check date format DDD MMM DD HH:MM:SS UTC YYYY
                assert re.match(r'\w{3} \w{3} \d{2} \d{2}:\d{2}:\d{2} \w{3} \d{4}', new_list["NEA"][0])

    def test_parse_risk(self):
        """Check data: risk_list, risk_list_special
        """
        url_risks = ['risk_list', 'risk_list_special']
        # Columns of risk lists
        risk_columns = ['Object Name', 'Diameter in m', '*=Y',
                        'Date/Time', 'IP max', 'PS max', 'TS',
                        'Vel in km/s', 'First Year', 'Last Year',
                        'IP cum', 'PS cum']
        risk_special_columns = risk_columns[0:8]

        for url in url_risks:
            # Get data from URL
            data_list = requests.get(API_URL + self.lists_dict[url],
                                     timeout=TIMEOUT,
                                     verify=VERIFICATION).content
            # Decode te data using UTF-8
            data_list_d = data_list.decode('utf-8')

            # Parse using parse_risk
            new_list = neocc.lists.parse_risk(data_list_d)
            assert isinstance(new_list, Table)

            if url == 'risk_list':

                # Assert dataframe is not empty, columns names, length
                assert len(new_list)
                assert all([x == y for x, y in zip(new_list.colnames, risk_columns)])
                assert len(new_list) > 1000

                # Assert columns data types
                # Floats
                float_cols = ['Diameter in m', 'IP max', 'PS max', 'Vel in km/s', 'IP cum', 'PS cum']
                assert all([np.issubdtype(new_list[x].dtype, float) for x in float_cols])

                # int64
                int_cols = ['TS', 'First Year', 'Last Year']
                assert all([np.issubdtype(new_list[x].dtype, int) for x in int_cols])

                # String
                str_cols = ['Object Name', '*=Y']
                assert all([np.issubdtype(new_list[x].dtype, str) for x in str_cols])

                # Datetime
                assert isinstance(new_list['Date/Time'], Time)

            else:
                # Assert dataframe is not empty, columns names
                assert len(new_list)
                assert all([x == y for x, y in zip(new_list.colnames, risk_special_columns)])

                # Assert columns data types
                # Floats
                float_cols = ['IP max', 'PS max', 'Vel in km/s']
                assert all([np.issubdtype(new_list[x].dtype, float) for x in float_cols])

                # ints
                int_cols = ['TS', 'Diameter in m']
                assert all([np.issubdtype(new_list[x].dtype, int) for x in int_cols])

                # String
                str_cols = ['Object Name', '*=Y']
                assert all([np.issubdtype(new_list[x].dtype, str) for x in str_cols])

    def test_parse_clo(self):
        """Check data: close_approaches_upcoming,
        close_approaches_recent
        """
        url_close = ['close_approaches_upcoming', 'close_approaches_recent']

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
            data_list_d = data_list.decode('utf-8')

            # Parse using parse_clo
            new_list = neocc.lists.parse_clo(data_list_d)
            assert isinstance(new_list, Table)

            # Assert dataframe is not empty, columns names and length
            assert len(new_list)
            assert all([x == y for x, y in zip(new_list.colnames, close_columns)])
            assert len(new_list) > 10

            # Assert columns data types
            # Floats
            float_cols = ['Miss Distance in au', 'Miss Distance in LD', 'Diameter in m',
                          'H', 'Max Bright', 'Rel. vel in km/s']
            assert all([np.issubdtype(new_list[x].dtype, float) for x in float_cols])

            # int64
            assert np.issubdtype(new_list['Miss Distance in km'].dtype, int)

            # Object
            str_cols = ['Object Name', '*=Yes']
            assert all([np.issubdtype(new_list[x].dtype, str) for x in str_cols])

            # Datetime
            assert isinstance(new_list['Date'], Time)

    def test_parse_pri(self):
        """Check data: priority_list, priority_list_faint
        """
        url_priority = ['priority_list', 'priority_list_faint']
        # Columns of priority lists
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
            data_list_d = data_list.decode('utf-8')
            # Parse using parse_pri
            new_list = neocc.lists.parse_pri(data_list_d)

            # Assert is an astropy table
            assert isinstance(new_list, Table)

            # Assert table is not empty, columns names and length
            assert len(new_list)
            assert all([x == y for x, y in zip(new_list.colnames, priority_columns)])
            assert len(new_list) > 100

            # Assert columns data types
            # Floats
            float_cols = ['R.A. in arcsec', 'Decl. in deg', 'V in mag']
            assert all([np.issubdtype(new_list[x].dtype, float) for x in float_cols])

            # int64
            int_cols = ['Priority', 'Elong. in deg', 'Sky uncert.']
            assert all([np.issubdtype(new_list[x].dtype, int) for x in int_cols])

            # Object
            assert np.issubdtype(new_list["Object"].dtype, str)

            # Datetime
            assert isinstance(new_list['End of Visibility'], Time)

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
        data_list_d = data_list.decode('utf-8')
        # Parse using parse_encounter
        new_list = neocc.lists.parse_encounter(data_list_d)

        # Assert is a pandas DataFrame
        assert isinstance(new_list, Table)

        # Assert dataframe is not empty, columns names and length
        assert len(new_list)
        assert all([x == y for x, y in zip(new_list.colnames, encounter_columns)])
        assert len(new_list) > 100000

        # Assert columns data types
        # Floats
        float_cols = encounter_columns[3:]
        assert all([np.issubdtype(new_list[x].dtype, float) for x in float_cols])

        # Str
        str_cols = ['Name/desig', 'Planet']
        assert all([np.issubdtype(new_list[x].dtype, str) for x in str_cols])

        # Datetime
        assert isinstance(new_list['Date'], Time)

    def test_parse_impacted(self):
        """Check data: impacted_objects
        """
        url = 'impacted_objects'
        # Get data from URL
        data_list = requests.get(API_URL + self.lists_dict[url],
                                 timeout=TIMEOUT,
                                 verify=VERIFICATION).content

        # Decode the data using UTF-8
        data_list_d = data_list.decode('utf-8')

        # Parse using parse_impacted
        new_list = neocc.lists.parse_impacted(data_list_d)

        # Assert is an astropy Table
        assert isinstance(new_list, Table)

        # Assert Table is not empty and length
        # Assert Table is not empty, columns names and length
        assert len(new_list) != 0
        assert len(new_list) < 100

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
            data_list_d = data_list.decode('utf-8')

            # Parse using parse_neo_catalogue
            new_list = neocc.lists.parse_neo_catalogue(data_list_d)

            # Assert is an astropy Table
            assert isinstance(new_list, Table)

            # Assert dataframe is not empty, columns names and length
            assert len(new_list)
            assert all([x == y for x, y in zip(new_list.colnames, cat_columns)])
            assert len(new_list) > 10000

            # Assert columns data types
            # Floats
            float_cols = ['Epoch (MJD)', 'a', 'e', 'i',
                          'long. node', 'arg. peric.', 'mean anomaly',
                          'absolute magnitude', 'slope param.']
            assert all([np.issubdtype(new_list[x].dtype, float) for x in float_cols])

            # Object
            assert np.issubdtype(new_list['Name'].dtype, str)

            # Int
            assert np.issubdtype(new_list['non-grav param.'].dtype, int)


@pytest.mark.filterwarnings('ignore:ERFA function *:erfa.core.ErfaWarning')
@pytest.mark.remote_data
class TestTabs:
    """Class which contains the unitary tests for tabs module.
    """
    path_nea = os.path.join(DATA_DIR, 'allnea.csv')
    nea_list = Table.read(path_nea, format="ascii.csv")

    # Ignore the FutureWarning that only comes up with the oldest dependencies
    warnings.filterwarnings("ignore", category=FutureWarning,
                            message="Conversion of the second argument of issubdtype*")

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
        rnd_object = random.choice(self.nea_list["NEA"])

        # Tabs to test
        object_tabs = ['impacts', 'close_approaches',
                       'observations', 'orbit_properties', '&cefrgfe',
                       4851]

        # Possible additional argument
        orbital_element = ['keplerian', 'equinoctial']
        orbit_epoch = ['present', 'middle']

        # Iterate to obtain all possible urls
        for tab in object_tabs:
            if tab == 'orbit_properties':
                for element in orbital_element:
                    for epoch in orbit_epoch:
                        with pytest.raises(ValueError):
                            neocc.tabs.get_object_url(rnd_object, tab,
                                                      orbital_elements=None,
                                                      orbit_epoch=epoch)
            elif tab in ['&cefrgfe', 4851]:
                with pytest.raises(KeyError):
                    neocc.tabs.get_object_url(rnd_object, tab)
            else:
                assert neocc.tabs.get_object_url(rnd_object, tab) ==\
                    str(rnd_object).replace(' ', '%20') +\
                    tab_dict[tab]

    def test_get_object_data(self):
        """Test for obtaining the content of a URL.
        """
        # Choose a random object from stored nea list
        rnd_object = random.choice(self.nea_list["NEA"])

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
                        url = neocc.tabs.get_object_url(rnd_object, tab,
                                                        orbital_elements=element,
                                                        orbit_epoch=epoch)
                        assert isinstance(neocc.tabs.get_object_data(url), bytes)
            else:
                url = neocc.tabs.get_object_url(rnd_object, tab)
                assert isinstance(neocc.tabs.get_object_data(url), bytes)

    @classmethod
    def test_tabs_names(cls):
        """Test is a invalid name
        """
        # Invalid inputs
        bad_names = ["ASedfe", "%&$", "ÁftR+", 154]
        for element in bad_names:
            with pytest.raises(KeyError):
                neocc.neocc.query_object(name='433', tab=element)

    def test_tabs_summary(self):
        """Check data: summary tab
        """
        # Check value error if empty
        with pytest.raises(ValueError):
            neocc.neocc.query_object(name='foo', tab='summary')

        # Choose a random object from stored nea list
        rnd_object = random.choice(self.nea_list["NEA"])

        # Request summary and check types
        result_list = neocc.neocc.query_object(name=rnd_object, tab='summary')
        assert isinstance(result_list, list)
        summary = result_list[0]
        assert isinstance(summary, Table)
        assert 'Discovery Date' in summary.meta.keys()
        assert 'Observatory' in summary.meta.keys()

        # Assert size of physical properties file
        assert len(summary)
        summary_cols = ['Physical Properties', 'Value', 'Units']
        assert all([x == y for x, y in zip(summary.colnames, summary_cols)])

        # Assert dtype
        assert all([np.issubdtype(summary[x].dtype, str) for x in summary_cols])

        # Check specific asteroids that will remain inmutable
        ast_summ1 = neocc.neocc.query_object(name='433', tab='summary')[0]
        assert ast_summ1.meta["Observatory"] == 'Berlin (1835-1913)'
        assert ast_summ1.meta["Discovery Date"] == '1898-08-13'

        # Check asteroid with no observatory nor discovery date
        # This object may change
        ast_summ2 = neocc.neocc.query_object(name='2006BV4', tab='summary')[0]
        assert "Observatory" not in ast_summ2.meta
        assert "Discovery Date" not in ast_summ2.meta
