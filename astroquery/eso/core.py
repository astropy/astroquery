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
    
    def authenticate(self, username, password):
        print("Authenticating {} on www.eso.org...".format(username))
        #Get the login page
        login_response = self.session.get("https://www.eso.org/sso/login")
        #Fill the login form
        root = html.document_fromstring(login_response.content)
        form = root.forms[-1]
        form.fields['username'] = username
        form.fields['password'] = password
        #Post the form payload to login
        login_result_response = self.session.post("https://www.eso.org/sso/login", params=form.form_values())
        #Check success
        root = html.document_fromstring(login_result_response.content)
        result = (len(root.find_class('error')) == 0)
        if result:
            print("Authentication successful!")
        else:
            print("Authentication failed!")
        return result
    
    def login(self, username):
        password = keyring.get_password("astroquery:www.eso.org", username)
        if password is None:
            password = getpass.getpass("{}, enter your ESO password:\n".format(username))
            if self.authenticate(username, password):
                keyring.set_password("astroquery:www.eso.org", username, password)
        else:
            self.authenticate(username, password)
    
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
