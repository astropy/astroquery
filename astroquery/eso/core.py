import requests
import keyring
import getpass
import re
import lxml.html as html
from cStringIO import StringIO

from astropy.table import Table

from ..query import QueryWithLogin

class EsoClass(QueryWithLogin):
    
    def __init__(self):
        self.session = requests.Session()
    
    def _activate_form(self, response, form_index=0, inputs={}):
        root = html.document_fromstring(response.content)
        form = root.forms[form_index]
        #form_dict = dict(form.form_values())
        form_dict = {}
        for key in form.inputs.keys():
            if (form.inputs[key].value != '') and (form.inputs[key].value != None):
                form_dict[key] = form.inputs[key].value
            if isinstance(form.inputs[key], html.SelectElement):
                form_dict[key] = form.inputs[key].value_options[0]
        #
        for key in inputs.keys():
            form_dict[key] = inputs[key]
        if "://" in form.action:
            url = form.action
        elif form.action[0] == "/":
            url = '/'.join(response.url.split('/',3)[:3]) + form.action
        else:
            url = response.url.rsplit('/',1)[0] + form.action
        if form.method == 'GET':
            response = self.session.get(url, params=form_dict)
        elif form.method == 'POST':
            if 'enctype' in form.attrib:
                if form.attrib['enctype'] == 'multipart/form-data':
                    response = self.session.post(url, data=form_dict, files={})
                else:
                    raise Exception("Not implemented!")
            else:
                response = self.session.post(url, params=form_dict)
        else:
            raise Exception("Unknown form method: {}".format(form.method))
        return response
    
    def authenticate(self, username, password):
        print("Authenticating {} on www.eso.org...".format(username))
        #Get the login page
        login_response = self.session.get("https://www.eso.org/sso/login")
        #Fill the login form
        login_result_response = self._activate_form(login_response, form_index=-1, inputs={'username': username, 'password':password})
        #Check success
        root = html.document_fromstring(login_result_response.content)
        result = (len(root.find_class('error')) == 0)
        if result:
            print("Authentication successful!")
        else:
            print("Authentication failed!")
        return result
    
    def login(self, username):
        #Get password from keyring or prompt
        password_from_keyring = keyring.get_password("astroquery:www.eso.org", username)
        if password_from_keyring is None:
            password = getpass.getpass("{}, enter your ESO password:\n".format(username))
        else:
            password = password_from_keyring
        #Authenticate
        authenticated = self.authenticate(username, password)
        #When authenticated, save password in keyring if needed
        if authenticated and password_from_keyring is None:
            keyring.set_password("astroquery:www.eso.org", username, password)
        return authenticated
    
    def query_instrument(self, instrument, **kwargs):
        url_base = "http://archive.eso.org"
        url_form = "/wdb/wdb/eso/{}/form".format(instrument)
        url_query = "/wdb/wdb/eso/{}/query".format(instrument)
        instrument_form = self.session.get(url_base+url_form)
        root = html.document_fromstring(instrument_form.content)
        form = root.forms[0]
        for keyword in kwargs.keys():
            if keyword in form.fields.keys():
                form.fields[keyword] = "{}".format(kwargs[keyword])
        query_dict = {}
        for key in form.inputs.keys():
            if (form.inputs[key].value != '') and (form.inputs[key].value != None):
                query_dict[key] = form.inputs[key].value
            if isinstance(form.inputs[key], html.SelectElement):
                query_dict[key] = form.inputs[key].value_options[0]
        query_dict["wdbo"] = "votable"
        instrument_response = self.session.get(url_base+url_query, params=query_dict)
        table = Table.read(StringIO(instrument_response.content))
        return table


Eso = EsoClass()
