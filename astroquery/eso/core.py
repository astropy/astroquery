import time
import requests
import webbrowser
import keyring
import getpass
import lxml.html as html
from cStringIO import StringIO

from astropy.table import Table
from astropy.io import ascii

from ..query import QueryWithLogin
from . import ROW_LIMIT

class EsoClass(QueryWithLogin):
    
    ROW_LIMIT = ROW_LIMIT()
    
    def __init__(self):
        self.session = requests.Session()
        self._instrument_list = None
        self._survey_list = None
    
    def _activate_form(self, response, form_index=0, inputs={}):
        #Extract form from response
        root = html.document_fromstring(response.content)
        form = root.forms[form_index]
        #Construct base url
        if "://" in form.action:
            url = form.action
        elif form.action[0] == "/":
            url = '/'.join(response.url.split('/',3)[:3]) + form.action
        else:
            url = response.url.rsplit('/',1)[0] + '/' + form.action
        #Identify payload format
        if form.method == 'GET':
            fmt = 'get' #get(url, params=payload)
        elif form.method == 'POST':
            if 'enctype' in form.attrib:
                if form.attrib['enctype'] == 'multipart/form-data':
                    fmt = 'multipart/form-data' #post(url, files=payload)
                elif form.attrib['enctype'] == 'application/x-www-form-urlencoded':
                    fmt = 'application/x-www-form-urlencoded' #post(url, data=payload)
            else:
                fmt = 'post' #post(url, params=payload)
        #Extract payload from form
        payload = []
        for key in form.inputs.keys():
            value = None
            is_file = False
            if isinstance(form.inputs[key], html.InputElement):
                value = form.inputs[key].value
                if 'type' in form.inputs[key].attrib:
                    is_file = (form.inputs[key].attrib['type'] == 'file')
            elif isinstance(form.inputs[key], html.SelectElement):
                if isinstance(form.inputs[key].value, html.MultipleSelectOptions):
                    value = []
                    for v in form.inputs[key].value:
                        value += [v]
                else:
                    value = form.inputs[key].value
                    if value is None:
                        value = form.inputs[key].value_options[0]
            if key in inputs.keys():
                value = "{}".format(inputs[key])
            if value is not None:
                if fmt == 'multipart/form-data':
                    if is_file:
                        payload += [(key, ('', '', 'application/octet-stream'))]
                    else:
                        if type(value) is list:
                            for v in value:
                                payload += [(key, ('', v))]
                        else:
                            payload += [(key, ('', value))]
                else:
                    if type(value) is list:
                        for v in value:
                            payload += [(key, v)]
                    else:
                        payload += [(key, value)]
        #Send payload
        if fmt == 'get':
            response = self.session.get(url, params=payload)
        elif fmt == 'post':
            response = self.session.post(url, params=payload)
        elif fmt == 'multipart/form-data':
            response = self.session.post(url, files=payload)
        elif fmt == 'application/x-www-form-urlencoded':
            response = self.session.post(url, data=payload)
        return response
    
    def _download_file(self, url):
        local_filename = url.split('/')[-1]
        print("Downloading {}...".format(local_filename))
        r = self.session.get(url, stream=True)
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024): 
                if chunk:
                    f.write(chunk)
                    f.flush()
        return local_filename
    
    def login(self, username):
        #Get password from keyring or prompt
        password_from_keyring = keyring.get_password("astroquery:www.eso.org", username)
        if password_from_keyring is None:
            password = getpass.getpass("{}, enter your ESO password:\n".format(username))
        else:
            password = password_from_keyring
        #Authenticate
        print("Authenticating {} on www.eso.org...".format(username))
        login_response = self.session.get("https://www.eso.org/sso/login")
        login_result_response = self._activate_form(login_response, form_index=-1, inputs={'username': username, 'password':password})
        root = html.document_fromstring(login_result_response.content)
        authenticated = (len(root.find_class('error')) == 0)
        if authenticated:
            print("Authentication successful!")
        else:
            print("Authentication failed!")
        #When authenticated, save password in keyring if needed
        if authenticated and password_from_keyring is None:
            keyring.set_password("astroquery:www.eso.org", username, password)
        return authenticated
    
    def list_instruments(self):
        """ List all the available instruments in the ESO archive.
        
        Returns
        -------
        instrument_list : list of strings
        
        """
        if self._instrument_list is None:
            instrument_list_response = self.session.get("http://archive.eso.org/cms/eso-data/instrument-specific-query-forms.html")
            root = html.document_fromstring(instrument_list_response.content)
            self._instrument_list = []
            for element in root.xpath("//div[@id='col3']//a[@href]"):
                if "http://archive.eso.org/wdb/wdb/eso" in element.attrib["href"]:
                    instrument = element.attrib["href"].split("/")[-2]
                    if instrument not in self._instrument_list:
                        self._instrument_list += [instrument]
        return self._instrument_list

    def list_surveys(self):
        """ List all the available surveys (phase 3) in the ESO archive.
        
        Returns
        -------
        survey_list : list of strings
        
        """
        if self._survey_list is None:
            survey_list_response = self.session.get("http://archive.eso.org/wdb/wdb/adp/phase3_main/form")
            root = html.document_fromstring(survey_list_response.content)
            self._survey_list = []
            for select in root.xpath("//select[@name='phase3_program']"):
                for element in select.xpath('option'):
                    survey = element.text_content().strip()
                    if survey not in self._survey_list and 'Any' not in survey:
                        self._survey_list.append(survey)
        return self._survey_list

    def query_survey(self, survey, **kwargs):
        """ Query survey Phase 3 data contained in the ESO archive.
        
        Parameters
        ----------
        survey : string
            Name of the survey to query, one of the names returned by `list_surveys()`.
        
        Returns
        -------
        table : `astropy.table.Table`
            A table representing the data available in the archive for the specified survey,
            matching the constraints specified in `kwargs`. The number of rows returned is capped
            by the ROW_LIMIT configuration item.
        
        """
        if survey not in self.list_surveys():
            raise ValueError("Survey %s is not in the survey list." % survey)
        url = "http://archive.eso.org/wdb/wdb/adp/phase3_main/form"
        survey_form = self.session.get(url)
        query_dict = kwargs
        query_dict["wdbo"] = "csv/download"
        query_dict['phase3_program'] = survey
        if self.ROW_LIMIT >= 0:
            query_dict["max_rows_returned"] = self.ROW_LIMIT
        else:
            query_dict["max_rows_returned"] = 10000
        survey_response = self._activate_form(survey_form, form_index=0, inputs=query_dict)
        table = ascii.read(StringIO(survey_response.content),format='csv',comment='#',delimiter=',',header_start=1)
        return table
    
    def query_instrument(self, instrument, open_form=False, **kwargs):
        """ Query instrument specific raw data contained in the ESO archive.
        
        Parameters
        ----------
        instrument : string
            Name of the instrument to query, one of the names returned by `list_instruments()`.
        open_form : bool
            If set to true, this will open in your browser the query form for the given instrument,
            and return None.
        
        Returns
        -------
        table : `astropy.table.Table`
            A table representing the data available in the archive for the specified instrument,
            matching the constraints specified in `kwargs`. The number of rows returned is capped
            by the ROW_LIMIT configuration item.
        
        """
        url = "http://archive.eso.org/wdb/wdb/eso/{}/form".format(instrument)
        if open_form:
            webbrowser.open(url)
            table = None
        else:
            instrument_form = self.session.get(url)
            query_dict = kwargs
            query_dict["wdbo"] = "votable"
            if self.ROW_LIMIT >= 0:
                query_dict["max_rows_returned"] = self.ROW_LIMIT
            else:
                query_dict["max_rows_returned"] = 10000
            instrument_response = self._activate_form(instrument_form, form_index=0, inputs=query_dict)
            table = Table.read(StringIO(instrument_response.content))
        return table
    
    def get_header(self, product_ids):
        """ Get the headers associated to a list of data product IDs
        
        Parameters
        ----------
        product_ids : list of strings
            List of data product IDs
        
        Returns
        -------
        result : list of dict
            List of headers, where each header is represented as a dictionary
        """
        if not isinstance(product_ids, list):
            product_ids = [product_ids]
        result = []
        for dp_id in product_ids:
            response = self.session.get("http://archive.eso.org/hdr?DpId={0}".format(dp_id))
            root = html.document_fromstring(response.text)
            hdr = root.xpath("//pre")[0].text
            header = {}
            for key_value in hdr.split('\n'):
                if "=" in key_value:
                    [key,value] = key_value.split('=',1)
                    header[key.strip()] = unicode(value.split('/',1)[0].strip())
                elif key_value.find("END") == 0:
                    break
            result += [header]
        return result
    
    def data_retrieval(self, datasets):
        """ Retrieve a list of datasets form the ESO archive.
        
        Parameters
        ----------
        datasets : list of strings
            List of datasets strings to retrieve from the archive.
        
        Returns
        -------
        files : list of strings
            List of files that have been locally downloaded from the archive.
        
        """
        data_retrieval_form = self.session.get("http://archive.eso.org/cms/eso-data/eso-data-direct-retrieval.html")
        data_confirmation_form = self._activate_form(data_retrieval_form, form_index=-1, inputs={"list_of_datasets": "\n".join(datasets)})
        data_download_form = self._activate_form(data_confirmation_form, form_index=-1)
        root = html.document_fromstring(data_download_form.content)
        state = root.xpath("//span[@id='requestState']")[0].text
        while state != 'COMPLETE':
            time.sleep(2.0)
            data_download_form = self.session.get(data_download_form.url)
            root = html.document_fromstring(data_download_form.content)
            state = root.xpath("//span[@id='requestState']")[0].text
        files = []
        for fileId in root.xpath("//input[@name='fileId']"):
            fileLink = fileId.attrib['value'].split()[1]
            fileLink = fileLink.replace("/api","").replace("https://","http://")
            files += [self._download_file(fileLink)]
        print("Done!")
        return files


Eso = EsoClass()
