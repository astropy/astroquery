import os
import requests
try:
    import htmllib
except ImportError:
    # python 3 compatibility
    import html.parser as htmllib

from astropy.table import Table
import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable
from astropy.io import fits
import astropy.utils.data as aud

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
        if 'FAILED to log in' in response.content: # change the error message
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

    #def table_info(self,database):
    #    if self.username !="multidark_public":
            

    
    def _multidark_send_request(self, url, request_payload) :
        """
        Helper function that sends the query request via a session or simple HTTP
        GET request.

        Parameters
        ----------
        url : str
            The url to send the request to.
        request_payload : dict
            The dict of parameters for the GET request

        Returns
        -------
        response : `requests.Response` object
            The response for the HTTP GET request
        """
        if hasattr(self, 'session') and self.logged_in():
            response = self.session.get(url, params=request_payload, timeout=MultiDark.TIMEOUT)
        else:
            response = commons.send_request(url, request_payload, MultiDark.TIMEOUT, request_type='GET')
        return response


     def _parse_result(self, response, verbose=False):
        """
        Parses the raw HTTP response and returns it as an `astropy.table.Table`.

        Parameters
        ----------
        response : `requests.Response`
            The HTTP response object
        verbose : bool, optional
            Defaults to false. When true it will display warnings whenever the VOtable
            returned from the service doesn't conform to the standard.

        Returns
        -------
        table : `astropy.table.Table`
        """
        table_links = self.extract_urls(response.content)
        # keep only one link that is not a webstart
        if len(table_links) == 0:
            raise Exception("No VOTable found on returned webpage!")
        table_link = [link for link in table_links if "8080" not in link][0]
        with aud.get_readable_fileobj(table_link) as f:
            content = f.read()

        if not verbose:
            commons.suppress_vo_warnings()

        try:
            tf = tempfile.NamedTemporaryFile()
            tf.write(content.encode('utf-8'))
            tf.flush()
            first_table = votable.parse(tf.name, pedantic=False).get_first_table()
            table = first_table.to_table()
            if len(table) == 0:
                warnings.warn("Query returned no results, so the table will be empty")
            return table
        except Exception as ex:
            self.response = content
            self.table_parse_error = ex
            raise TableParseError("Failed to parse UKIDSS votable! The raw response can be found "
                                  "in self.response, and the error in self.table_parse_error.")

