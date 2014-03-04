import requests

# Astropy imports
from astropy.table import Table
import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable
from astropy.io import fits
import astropy.utils.data as aud

# Astroquery imports
from ..utils import commons
from ..query import QueryWithLogin
from . import COSMOSIM_SERVER, COSMOSIM_TIMEOUT

import pdb

__all__ = ['CosmoSim']

class CosmoSim(QueryWithLogin):
    """
    TO DO: documentation
    """

    QUERY_URL = COSMOSIM_SERVER()
    TIMEOUT = COSMOSIM_TIMEOUT()

    def __init__(self,username=None,password=None):
        self.username = username
        self.password = password
        self.login(username,password)

    def login(self,username,password):
        """
        TO DO: documentation
        """
        
        self.session = requests.session()
        response = self.session.post(CosmoSim.QUERY_URL,auth=(self.username,self.password))

        pdb.set_trace()

        if not response.ok:
            self.session = None
            response.raise_for_status()

    # will check to see if using private or public credentials
    def logged_in(self):
        """
        TO DO: documentation
        """
        print 'Need to implement when public default parameters (if any) are known...'

    @class_or_instance
    def sql_query(self, query_string):
        """
        TO DO: documentation
        """

        request_payload = {}

    @class_or_instance
    def _cosmosim_send_request(self,url,request_payload):
        """
        Internal function which sends the sql query request.

        Parameters
        ----------
        url : str
            The url to send the request to.
        request_payload : dict
            A dictionary of parameters for the POST request

        Returns
        -------
        response: `requests.Response` object
            The response for the HTTP POST request
        """
        
        if hasattr(self,'session'):
            response = self.session.post(url,data=re)
