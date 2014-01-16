import requests
import keyring
import getpass
import re
from bs4 import BeautifulSoup as bs

from ..query import QueryWithLogin

class EsoClass(QueryWithLogin):
    
    def __init__(self):
        self.session = requests.Session()
    
    def authenticate(self, username, password):
        print("Authenticating {} on www.eso.org...".format(username))
        #Get the login page
        login_response = self.session.get("https://www.eso.org/sso/login")
        #Extract all the inputs to the login form into the form_payload dictionary
        soup = bs(login_response.content)
        form = soup.find('form', attrs={'action':re.compile("^login")}).find_all('input',attrs={'name':True})
        form_payload = {}
        for form_input in form:
            form_payload[form_input.attrs.get('name')] = form_input.attrs.get('value')
        #Update the username and password inputs
        form_payload.update({'username': username})
        form_payload.update({'password': password})
        #Post the form payload to login
        login_result_response = self.session.post("https://www.eso.org/sso/login", params=form_payload)
        #Check success
        soup = bs(login_result_response.content)
        result = (soup.find('div', attrs={'class':'error'}) is None)
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
