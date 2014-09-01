# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import time
import sys
import os.path
import webbrowser
import getpass
import warnings
import keyring
import numpy as np
from bs4 import BeautifulSoup

from astropy.extern.six import BytesIO
from astropy.extern import six
from astropy.table import Table, Column
from astropy import log

from ..exceptions import LoginError, RemoteServiceError
from ..utils import schema, system_tools
from ..query import QueryWithLogin, suspend_cache
from . import conf

__doctest_skip__ = ['EsoClass.*']

def _check_response(content):
    """
    Check the response from an ESO service query for various types of error

    If all is OK, return True
    """
    if "NETWORKPROBLEM" in content:
        raise RemoteServiceError("The query resulted in a network "
                                 "problem; the service may be offline.")
    elif "# No data returned !" not in content:
        return True


class EsoClass(QueryWithLogin):

    ROW_LIMIT = conf.row_limit

    def __init__(self):
        super(EsoClass, self).__init__()
        self._instrument_list = None
        self._survey_list = None

    def _activate_form(self, response, form_index=0, inputs={}, cache=True,
                       method=None):
        """
        Parameters
        ----------
        method: None or str
            Can be used to override the form-specified method
        """
        # Extract form from response
        root = BeautifulSoup(response.content, 'html5lib')
        form = root.find_all('form')[form_index]
        # Construct base url
        form_action = form.get('action')
        if "://" in form_action:
            url = form_action
        elif form_action.startswith('/'):
            url = '/'.join(response.url.split('/', 3)[:3]) + form_action
        else:
            url = response.url.rsplit('/', 1)[0] + '/' + form_action
        # Identify payload format
        fmt = None
        form_method = form.get('method').lower()
        if form_method == 'get':
            fmt = 'get'  # get(url, params=payload)
        elif form_method == 'post':
            if 'enctype' in form.attrs:
                if form.attrs['enctype'] == 'multipart/form-data':
                    fmt = 'multipart/form-data'  # post(url, files=payload)
                elif form.attrs['enctype'] == 'application/x-www-form-urlencoded':
                    fmt = 'application/x-www-form-urlencoded'  # post(url, data=payload)
            else:
                fmt = 'post'  # post(url, params=payload)
        # Extract payload from form
        payload = []
        for form_elem in form.find_all(['input', 'select', 'textarea']):
            value = None
            is_file = False
            tag_name = form_elem.name
            key = form_elem.get('name')
            if tag_name == 'input':
                if 'type' in form_elem.attrs:
                    is_file = form_elem.get('type') == 'file'
                if form_elem.has_attr('checked'):
                    if form_elem.has_attr('value'):
                        value = form_elem.get('value')
                    else:
                        value = 'on'
                else:
                    value = form_elem.get('value')
            elif tag_name == 'select':
                if form_elem.get('multiple') is not None:
                    value = []
                    for option in form_elem.select('option[value]'):
                        if option.get('selected') is not None:
                            value.append(option.get('value'))
                else:
                    for option in form_elem.select('option[value]'):
                        if option.get('selected') is not None:
                            value = option.get('value')
                    # select the first option field if none is selected
                    if value is None:
                        value = form_elem.select('option[value]')[0].get('value')

            if key in inputs:
                value = str(inputs[key])
            if (key is not None) and (value is not None):
                if fmt == 'multipart/form-data':
                    if is_file:
                        payload.append(
                            (key, ('', '', 'application/octet-stream')))
                    else:
                        if type(value) is list:
                            for v in value:
                                payload.append((key, ('', v)))
                        else:
                            payload.append((key, ('', value)))
                else:
                    if type(value) is list:
                        for v in value:
                            payload.append((key, v))
                    else:
                        payload.append((key, value))

        # for future debugging
        self._payload = payload

        if method is not None:
            fmt = method

        # Send payload
        if fmt == 'get':
            response = self._request("GET", url, params=payload, cache=cache)
        elif fmt == 'post':
            response = self._request("POST", url, params=payload, cache=cache)
        elif fmt == 'multipart/form-data':
            response = self._request("POST", url, files=payload, cache=cache)
        elif fmt == 'application/x-www-form-urlencoded':
            response = self._request("POST", url, data=payload, cache=cache)

        return response

    def _login(self, username):
        # Get password from keyring or prompt
        password_from_keyring = keyring.get_password("astroquery:www.eso.org", username)
        if password_from_keyring is None:
            if __IPYTHON__:
                log.warn("You may be using an ipython notebook:"
                         " the password form will appear in your terminal.")
            password = getpass.getpass("{0}, enter your ESO password:\n".format(username))
        else:
            password = password_from_keyring
        # Authenticate
        log.info("Authenticating {0} on www.eso.org...".format(username))
        # Do not cache pieces of the login process
        login_response = self._request("GET", "https://www.eso.org/sso/login", cache=False)
        login_result_response = self._activate_form(login_response,
                                                    form_index=-1,
                                                    inputs={'username': username,
                                                            'password': password})
        root = BeautifulSoup(login_result_response.content, 'html5lib')
        authenticated = not root.select('.error')
        if authenticated:
            log.info("Authentication successful!")
        else:
            log.exception("Authentication failed!")
        # When authenticated, save password in keyring if needed
        if authenticated and password_from_keyring is None:
            keyring.set_password("astroquery:www.eso.org", username, password)
        return authenticated

    def list_instruments(self, cache=True):
        """ List all the available instruments in the ESO archive.

        Returns
        -------
        instrument_list : list of strings
        cache : bool
            Cache the response for faster subsequent retrieval

        """
        if self._instrument_list is None:
            instrument_list_response = self._request("GET",
                                                     "http://archive.eso.org/cms/eso-data/instrument-specific-query-forms.html",
                                                     cache=cache)
            root = BeautifulSoup(instrument_list_response.content, 'html5lib')
            self._instrument_list = []
            for element in root.select("div[id=col3] a[href]"):
                href = element.attrs["href"]
                if u"http://archive.eso.org/wdb/wdb/eso" in href:
                    instrument = href.split("/")[-2]
                    if instrument not in self._instrument_list:
                        self._instrument_list.append(instrument)
        return self._instrument_list

    def list_surveys(self, cache=True):
        """ List all the available surveys (phase 3) in the ESO archive.

        Returns
        -------
        survey_list : list of strings
        cache : bool
            Cache the response for faster subsequent retrieval

        """
        if self._survey_list is None:
            survey_list_response = self._request("GET",
                                                 "http://archive.eso.org/wdb/wdb/adp/phase3_main/form",
                                                 cache=cache)
            root = BeautifulSoup(survey_list_response .content, 'html5lib')
            self._survey_list = []
            for select in root.select("select[name=phase3_program]"):
                for element in select.select('option'):
                    survey = element.text.strip()
                    if survey not in self._survey_list and 'Any' not in survey:
                        self._survey_list.append(survey)
        return self._survey_list

    def query_survey(self, survey, cache=True, **kwargs):
        """
        Query survey Phase 3 data contained in the ESO archive.

        Parameters
        ----------
        survey : string
            Name of the survey to query, one of the names returned by
            `list_surveys()`.
        cache : bool
            Cache the response for faster subsequent retrieval

        Returns
        -------
        table : `~astropy.table.Table` or `None`
            A table representing the data available in the archive for the
            specified survey, matching the constraints specified in ``kwargs``.
            The number of rows returned is capped by the ROW_LIMIT
            configuration item. `None` is returned when the query has no
            results.

        """

        if survey not in self.list_surveys():
            raise ValueError("Survey %s is not in the survey list." % survey)
        url = "http://archive.eso.org/wdb/wdb/adp/phase3_main/form"
        survey_form = self._request("GET", url, cache=cache)
        query_dict = kwargs
        query_dict["wdbo"] = "csv/download"
        query_dict['phase3_program'] = survey
        if self.ROW_LIMIT >= 0:
            query_dict["max_rows_returned"] = self.ROW_LIMIT
        else:
            query_dict["max_rows_returned"] = 10000
        survey_response = self._activate_form(survey_form, form_index=0,
                                              inputs=query_dict, cache=cache)

        content = survey_response.text
        byte_content = survey_response.content
        if _check_response(content):
            try:
                table = Table.read(BytesIO(byte_content), format="ascii.csv",
                                   guess=False, header_start=1)
            except Exception as ex:
                # astropy 0.3.2 raises an anonymous exception; this is
                # intended to prevent that from causing real problems
                if 'No reader defined' in ex.args[0]:
                    table = Table.read(BytesIO(byte_content), format="ascii",
                                       delimiter=',', guess=False,
                                       header_start=1)
                else:
                    raise ex
            return table
        else:
            warnings.warn("Query returned no results")

    def query_instrument(self, instrument, column_filters={}, columns=[],
                         open_form=False, help=False, cache=True, **kwargs):
        """
        Query instrument specific raw data contained in the ESO archive.

        Parameters
        ----------
        instrument : string
            Name of the instrument to query, one of the names returned by
            `list_instruments()`.
        column_filters : dict
            Constraints applied to the query.
        columns : list of strings
            Columns returned by the query.
        open_form : bool
            If `True`, opens in your default browser the query form
            for the requested instrument.
        help : bool
            If `True`, prints all the parameters accepted in
            `column_filters` and `columns` for the requested `instrument`.
        cache : bool
            Cache the response for faster subsequent retrieval

        Returns
        -------
        table : `~astropy.table.Table`
            A table representing the data available in the archive for the
            specified instrument, matching the constraints specified in
            ``kwargs``. The number of rows returned is capped by the
            ROW_LIMIT configuration item.

        """

        url = "http://archive.eso.org/wdb/wdb/eso/{0}/form".format(instrument)
        table = None
        if open_form:
            webbrowser.open(url)
        elif help:
            self._print_help(url)
        else:
            instrument_form = self._request("GET", url, cache=cache)
            query_dict = {}
            query_dict.update(column_filters)
            # TODO: replace this with individually parsed kwargs
            query_dict.update(kwargs)
            query_dict["wdbo"] = "csv/download"

            # Default to returning the DP.ID since it is needed for header acquisition
            query_dict['tab_dp_id'] = (kwargs.pop('tab_dp_id')
                                       if 'tab_db_id' in kwargs
                                       else 'on')

            for k in columns:
                query_dict["tab_" + k] = True
            if self.ROW_LIMIT >= 0:
                query_dict["max_rows_returned"] = self.ROW_LIMIT
            else:
                query_dict["max_rows_returned"] = 10000
            instrument_response = self._activate_form(instrument_form,
                                                      form_index=0,
                                                      inputs=query_dict, cache=cache)
            text = instrument_response.text
            byte_content = instrument_response.content
            if _check_response(text):
                content = []
                # The first line is garbage, don't know why
                for line in byte_content.split(b'\n')[1:]:
                    if len(line) > 0:  # Drop empty lines
                        if line[0:1] != b'#':  # And drop comments
                            content += [line]
                content = b'\n'.join(content)
                try:
                    table = Table.read(BytesIO(content), format="ascii.csv", comment='^#')
                except Exception as ex:
                    # astropy 0.3.2 raises an anonymous exception; this is
                    # intended to prevent that from causing real problems
                    if 'No reader defined' in ex.args[0]:
                        table = Table.read(BytesIO(content), format="ascii",
                                           delimiter=',')
                    else:
                        raise ex
                return table
            else:
                warnings.warn("Query returned no results")


    def get_headers(self, product_ids, cache=True):
        """
        Get the headers associated to a list of data product IDs

        This method returns a `~astropy.table.Table` where the rows correspond
        to the provided data product IDs, and the columns are from each of
        the Fits headers keywords.

        Note: The additional column ``'DP.ID'`` found in the returned table
        corresponds to the provided data product IDs.

        Parameters
        ----------
        product_ids : either a list of strings or a `~astropy.table.Column`
            List of data product IDs.

        Returns
        -------
        result : `~astropy.table.Table`
            A table where: columns are header keywords, rows are product_ids.

        """
        _schema_product_ids = schema.Schema(schema.Or(Column, [schema.Or(*six.string_types)]))
        _schema_product_ids.validate(product_ids)
        # Get all headers
        result = []
        for dp_id in product_ids:
            response = self._request("GET",
                                     "http://archive.eso.org/hdr?DpId={0}".format(dp_id),
                                     cache=cache)
            root = BeautifulSoup(response.content, 'html5lib')
            hdr = root.select('pre')[0].text
            header = {'DP.ID': dp_id}
            for key_value in hdr.split('\n'):
                if "=" in key_value:
                    key, value = key_value.split('=', 1)
                    key = key.strip()
                    value = value.split('/', 1)[0].strip()
                    if key[0:7] != "COMMENT":  # drop comments
                        if value == "T":  # Convert boolean T to True
                            value = True
                        elif value == "F":  # Convert boolean F to False
                            value = False
                        # Convert to string, removing quotation marks
                        elif value[0] == "'":
                            value = value[1:-1]
                        elif "." in value:  # Convert to float
                            value = float(value)
                        else:  # Convert to integer
                            value = int(value)
                        header[key] = value
                elif key_value.startswith("END"):
                    break
            result.append(header)
        # Identify all columns
        columns = []
        column_types = []
        for header in result:
            for key in header:
                if key not in columns:
                    columns.append(key)
                    column_types.append(type(header[key]))
        # Add all missing elements
        for i in range(len(result)):
            for (column, column_type) in zip(columns, column_types):
                if column not in result[i]:
                    result[i][column] = column_type()
        # Return as Table
        return Table(result)

    def data_retrieval(self, datasets):
        """
        DEPRECATED: see `retrieve_datasets`
        """

        warnings.warn("data_retrieval has been replaced with retrieve_data",
                      DeprecationWarning)

    def retrieve_data(self, datasets, cache=True):
        """
        Retrieve a list of datasets form the ESO archive.

        Parameters
        ----------
        datasets : list of strings or string
            List of datasets strings to retrieve from the archive.
        cache : bool
            Cache the retrieval forms (not the data - they are downloaded
            independent of this keyword)

        Returns
        -------
        files : list of strings
            List of files that have been locally downloaded from the archive.

        Examples
        --------
        >>> dptbl = Eso.query_instrument('apex', pi_coi='ginsburg')
        >>> dpids = [row['DP.ID'] for row in dptbl if 'Map' in row['Object']]
        >>> files = Eso.retrieve_data(dpids)

        """
        datasets_to_download = []
        files = []

        if isinstance(datasets, six.string_types):
            datasets = [datasets]
        if not isinstance(datasets, (list, tuple, np.ndarray)):
            raise TypeError("Datasets must be given as a list of strings.")

        # First: Detect datasets already downloaded
        for dataset in datasets:
            if os.path.splitext(dataset)[1].lower() in ('.fits', '.tar'):
                local_filename = dataset
            else:
                local_filename = dataset + ".fits"

            if self.cache_location is not None:
                local_filename = os.path.join(self.cache_location,
                                              local_filename)
            if os.path.exists(local_filename):
                log.info("Found {0}.fits...".format(dataset))
                files.append(local_filename)
            elif os.path.exists(local_filename + ".Z"):
                log.info("Found {0}.fits.Z...".format(dataset))
                files.append(local_filename + ".Z")
            else:
                datasets_to_download.append(dataset)

        valid_datasets = [self.verify_data_exists(ds) for ds in datasets_to_download]
        if not all(valid_datasets):
            invalid_datasets = [ds for ds, v in zip(datasets_to_download, valid_datasets) if not v]
            raise ValueError("The following data sets were not found on the ESO servers: {0}".format(invalid_datasets))

        # Second: Download the other datasets
        if datasets_to_download:
            data_retrieval_form = self._request("GET",
                                                "http://archive.eso.org/cms/eso-data/eso-data-direct-retrieval.html",
                                                cache=cache)
            log.info("Staging request...")
            with suspend_cache(self):  # Never cache staging operations
                inputs = {"list_of_datasets": "\n".join(datasets_to_download)}
                data_confirmation_form = self._activate_form(data_retrieval_form,
                                                             form_index=-1,
                                                             inputs=inputs)
                root = BeautifulSoup(data_confirmation_form.content, 'html5lib')
                login_button = root.select('input[value=LOGIN]')
                if login_button:
                    raise LoginError("Not logged in."
                                     "  You must be logged in to download data.")
                # TODO: There may be another screen for Not Authorized; that
                # should be included too
                data_download_form = self._activate_form(data_confirmation_form,
                                                         form_index=-1)
                log.info("Staging form is at {0}".format(data_download_form.url))
                root = BeautifulSoup(data_download_form.content, 'html5lib')
                state = root.select('span[id=requestState]')[0].text
                t0 = time.time()
                while state not in ('COMPLETE', 'ERROR'):
                    time.sleep(2.0)
                    data_download_form = self._request("GET",
                                                       data_download_form.url,
                                                       cache=False)
                    root = BeautifulSoup(data_download_form.content, 'html5lib')
                    state = root.select('span[id=requestState]')[0].text
                    print("{0:20.0f}s elapsed".format(time.time()-t0), end='\r')
                    sys.stdout.flush()
                if state == 'ERROR':
                    raise RemoteServiceError("There was a remote service error;"
                                             " perhaps the requested file could not be found?")
            log.info("Downloading files...")
            for fileId in root.select('input[name=fileId]'):
                fileLink = fileId.attrs['value'].split()[1]
                fileLink = fileLink.replace("/api", "").replace("https://", "http://")
                filename = self._request("GET", fileLink, save=True)
                files.append(system_tools.gunzip(filename))
        log.info("Done!")
        return files

    def verify_data_exists(self, dataset):
        """
        Given a data set name, return 'True' if ESO has the file and 'False'
        otherwise
        """
        url = 'http://archive.eso.org/wdb/wdb/eso/eso_archive_main/query'
        payload = {'dp_id': dataset,
                   'ascii_out_mode':'true',
                  }
        # Never cache this check as it is verifying the existence of remote content
        response = self._request("POST", url, params=payload, cache=False)

        content = response.text

        return 'No data returned' not in content

    def query_apex_quicklooks(self, project_id, help=False, open_form=False,
                              cache=True, **kwargs):
        """
        APEX data are distributed with quicklook products identified with a
        different name than other ESO products.  This query tool searches by
        project ID or any other supported keywords.

        Examples
        --------
        >>> tbl = Eso.query_apex_quicklooks('E-093.C-0144A')
        >>> files = Eso.retrieve_data(tbl['Product ID'])
        """

        apex_query_url = 'http://archive.eso.org/wdb/wdb/eso/apex_product/form'

        table = None
        if open_form:
            webbrowser.open(apex_query_url)
        elif help:
            return self._print_help(apex_query_url)
        else:

            payload = {'dp_id':project_id, 'wdbo':'csv/download'}

            apex_form = self._request("GET", apex_query_url, cache=cache)
            apex_response = self._activate_form(apex_form, form_index=0,
                                                inputs=payload, cache=cache,
                                                method='application/x-www-form-urlencoded')

            content = apex_response.text
            byte_content = apex_response.content
            if _check_response(content):
                try:
                    table = Table.read(BytesIO(byte_content), format="ascii.csv",
                                       guess=False, header_start=1)
                except Exception as ex:
                    # astropy 0.3.2 raises an anonymous exception; this is
                    # intended to prevent that from causing real problems
                    if 'No reader defined' in ex.args[0]:
                        table = Table.read(BytesIO(byte_content), format="ascii",
                                           delimiter=',', guess=False,
                                           header_start=1)
                    else:
                        raise ex
            else:
                raise RemoteServiceError("Query returned no results")

            return table


    def _print_help(self, url):
        """
        Download a form and print it in a quasi-human-readable way
        """
        log.info("List of the column_filters parameters accepted by the {0} instrument query.".format(instrument))
        log.info("The presence of a column in the result table can be controlled if prefixed with a [ ] checkbox.")
        log.info("The default columns in the result table are shown as already ticked: [x].")

        result_string = []

        resp = self._request("GET", url, cache=cache)
        doc = BeautifulSoup(resp.content, 'html5lib')
        form = doc.select("html > body > form > pre")[0]
        for section in form.select("table"):
            section_title = "".join(section.stripped_strings)
            section_title = "\n".join(["", section_title, "-"*len(section_title)])
            result_string.append(section_title)
            checkbox_name = ""
            checkbox_value = ""
            for tag in section.next_siblings:
                if tag.name == u"table":
                    break
                elif tag.name == u"input":
                    if tag.get(u'type') == u"checkbox":
                        checkbox_name = tag['name']
                        checkbox_value = u"[x]" if ('checked' in tag.attrs) else u"[ ]"
                        name = ""
                        value = ""
                    else:
                        name = tag['name']
                        value = ""
                elif tag.name == u"select":
                    options = []
                    for option in tag.select("option"):
                        options += ["{0} ({1})".format(option['value'], "".join(option.stripped_strings))]
                    name = tag[u"name"]
                    value = ", ".join(options)
                else:
                    name = ""
                    value = ""
                if u"tab_" + name == checkbox_name:
                    checkbox = checkbox_value
                else:
                    checkbox = "   "
                if name != u"":
                    result_string.append("{0} {1}: {2}".format(checkbox, name, value))

        print("\n".join(result_string))
        return result_string

Eso = EsoClass()
