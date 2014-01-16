import requests
import keyring
import getpass
import re
import lxml.html as html

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

Eso = EsoClass()
