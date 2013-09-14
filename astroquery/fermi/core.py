# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Download of Fermi LAT (Large Area Telescope) data"""
from __future__ import print_function
import re
import time
from ..query import BaseQuery
from ..utils.class_or_instance import class_or_instance
from ..utils import commons, async_to_sync
import astropy.units as u

from . import FERMI_URL,FERMI_TIMEOUT,FERMI_RETRIEVAL_TIMEOUT

__all__ = ['FermiLAT', 'GetFermilatDatafile','get_fermilat_datafile']

@async_to_sync
class FermiLAT(BaseQuery):
    """
    TODO: document
    """

    request_url = FERMI_URL()
    result_url_re = re.compile('The results of your query may be found at <a href="(http://fermi.gsfc.nasa.gov/.*?)"')
    TIMEOUT = FERMI_TIMEOUT()

    @class_or_instance
    def query_object_async(self, *args, **kwargs):
        """
        Query the FermiLAT database

        Returns
        -------
        The URL of the page with the results (still need to scrape this page to download the data: easy for wget)
        """

        payload = self._parse_args(*args,**kwargs)

        if kwargs.get('get_query_payload'):
            return payload

        result = commons.send_request(self.request_url,
                                      payload,
                                      self.TIMEOUT)

        # text returns unicode, content returns unencoded (?)
        re_result = self.result_url_re.findall(result.text)

        if len(re_result) == 0:
            raise ValueError("Results did not contain a result url... something went awry (that hasn't been tested yet)")
        else:
            result_url = re_result[0]

        return result_url

    @class_or_instance
    def _parse_args(self, name_or_coords, searchradius='', obsdates='', timesys='Gregorian',
                    energyrange_MeV='', LATdatatype='Photon', spacecraftdata=True):
        """
        Parameters
        ----------
        name_or_coords : str
            An object name or coordinate specification
        searchradius : str
            The search radius in degrees around the object/coordinates
            specified (will be converted to string if specified as number).
            Must be in the range [1,60]
            .. warning::
                Defaults to 1 degree if left blank
        obsdates : str
            Observation dates.
        timesys: 'Gregorian' or 'MET' or 'MJD'
            Time system associated with obsdates
        energyrange_MeV: str
            Energy range in MeV

        Returns
        -------
        Requests payload in a dictionary
        """


        payload = {'shapefield':str(searchradius),
                   'coordsystem':'J2000',
                   'coordfield':_parse_coordinates(name_or_coords),
                   'destination':'query',
                   'timefield':obsdates,
                   'timetype': timesys,
                   'energyfield':energyrange_MeV,
                   'photonOrExtendedOrNone': LATdatatype,
                   'spacecraft':'on' if spacecraftdata else 'off'}

        return payload

    @class_or_instance
    def _parse_result(self,result,verbose=False,**kwargs):
        """
        Use get_fermilat_datafile to download a result URL
        """
        return get_fermilat_datafile(result)

def _parse_coordinates(coordinates):
    try:
        c = commons.parse_coordinates(coordinates)
        # now c has some subclass of astropy.coordinate
        # get ra, dec and frame
        return _fermi_format_coords(c)
    except (u.UnitsException, TypeError):
        raise Exception("Coordinates not specified correctly")

def _fermi_format_coords(c):
    c = c.fk5
    return "{0:0.5f},{1:0.5f}".format(c.ra.degree,c.dec.degree)

class GetFermilatDatafile(object):
    """
    TODO: document
    TODO: Fail with useful failure messages on genuine failures
    (this doesn't need to be implemented as a class)
    """

    fitsfile_re = re.compile('<a href="(.*?)">Available</a>')

    TIMEOUT = FERMI_RETRIEVAL_TIMEOUT()

    check_frequency = 1  # minutes

    def __call__(self, result_url, check_frequency=1, verbose=False):
        self.result_url = result_url

        page_loaded = False

        elapsed_time = 0

        while not(page_loaded):
            page_loaded = fitsfile_urls = self._check_page()
            if page_loaded: 
                # don't wait an extra N minutes for success
                break
            time.sleep(check_frequency * 60)
            elapsed_time += check_frequency
            # update progressbar here...

        if verbose:
            print("Query completed in %0.1f minutes" % (elapsed_time))

        return fitsfile_urls

    def _check_page(self):
        result_page = commons.send_request(self.result_url,
                                           None,
                                           self.TIMEOUT)

        pagedata = result_page.content

        fitsfile_urls = self.fitsfile_re.findall(pagedata)

        if len(fitsfile_urls) == 0:
            return False
        else:
            return fitsfile_urls

get_fermilat_datafile = GetFermilatDatafile()
