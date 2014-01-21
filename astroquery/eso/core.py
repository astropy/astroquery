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
        files_dict = []
        for key in form.inputs.keys():
            if 'type' in form.inputs[key].attrib.keys():
                typ = form.inputs[key].attrib['type']
            else:
                typ = None
            if typ == 'file':
                if form.inputs[key].value is None:
                    files_dict += [(key, ("", "", "application/octet-stream"))]
            else:
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
            url = response.url.rsplit('/',1)[0] + '/' + form.action
        if form.method == 'GET':
            response = self.session.get(url, params=form_dict)
        elif form.method == 'POST':
            if 'enctype' in form.attrib:
                if form.attrib['enctype'] == 'multipart/form-data':
                    response = self.session.post(url, data=form_dict, files=files_dict)
                else:
                    raise Exception("Not implemented: enctype={}".format(form.attrib['enctype']))
            else:
                response = self.session.post(url, params=form_dict)
        else:
            raise Exception("Unknown form method: {}".format(form.method))
        return response
    
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
    
    def query_instrument(self, instrument, **kwargs):
        instrument_form = self.session.get("http://archive.eso.org/wdb/wdb/eso/{}/form".format(instrument))
        query_dict = kwargs
        query_dict["wdbo"] = "votable"
        instrument_response = self._activate_form(instrument_form, form_index=0, inputs=query_dict)
        table = Table.read(StringIO(instrument_response.content))
        return table


Eso = EsoClass()
