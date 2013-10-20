import os
import requests
try:
    import htmllib
except ImportError:
    # python 3 compatibility
    import html.parser as htmllib

from astropy.table import Table

from ..query import QueryWithLogin
from . import MULTIDARK_SERVER, MULTIDARK_TIMEOUT

__all__ = ['MultiDark']


class MultiDark(QueryWithLogin):
    """
    TODO: document
    """

    BASE_URL = MULTIDARK_SERVER()
    LOGIN_URL = BASE_URL + "MyDB"
    TIMEOUT = MULTIDARK_TIMEOUT()

    public_databases = ("miniMDR1", "Sp3D")
    private_databases = ("Bolshoi","MDPL","MDR1","miniMDR1","Sp3D")
    #table_info_query = "select * from MDR1.information_schema.tables"

    def __init__(self,username="multidark_public",password=None):
        self.username = username
        self.password = password
        self.login(username,password)

    def login(self,username,password):
        """
        Login to non-public data as a known user

        Parameters
        ----------
        username : string
        password : string
        """

        # Construct cookie holder, URL openenr, and retrieve login page
        self.session = requests.session()

        credentials = {'user': username, 'passwd': password}
        response = self.session.post(MultiDark.LOGIN_URL, data=credentials)
        if not response.ok:
            self.session = None
            response.raise_for_status()
        if 'FAILED to log in' in response.content:
            self.session = None
            raise Exception("Unable to log in with your given credentials.\n"
                            "Please try again.\n"
                            "Note: Public credentials can be used, though databse access is limited.\n"
                            "Use the following for default public access:"
                            "username=multidark_public"
                            "password= ")
        
    def logged_in(self):
        """
        Determine whether currently logged in.
        """
        if self.session == None:
            return False
        for cookie in self.session.cookies:
            if cookie.is_expired():
                return False
        return True

    
