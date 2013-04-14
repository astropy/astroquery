# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Download of Fermi LAT (Large Area Telescope) data"""
import requests
import urllib
import re
import time

__all__ = ['FermiLAT_Query', 'FermiLAT_DelayedQuery']

class FermiLAT_Query(object):

    request_url = 'http://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/LATDataQuery.cgi'
    result_url_re = re.compile('The results of your query may be found at <a href="(http://fermi.gsfc.nasa.gov/.*?)"')

    def __call__(self, name_or_coords, coordsys='J2000', searchradius='', obsdates='', timesys='Gregorian',
            energyrange_MeV='', LATdatatype='Photon', spacecraftdata=True):
        """
        Query the FermiLAT database

        Parameters
        ----------
        name_or_coords : str
            An object name or coordinate specification
        coordsys : 'J2000' or 'B1950' or 'Galactic'
            The coordinate system associated with name
        searchradius : str
            The search radius around the object/coordinates specified (will be
            converted to string if specified as number)
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
        The URL of the page with the results (still need to scrape this page to download the data: easy for wget)
        """

        payload = {'shapefield':str(searchradius),
                   'coordsystem':coordsys,
                   'coordfield':name_or_coords,
                   'destination':'query',
                   'timefield':obsdates,
                   'timetype': timesys,
                   'energyfield':energyrange_MeV,
                   'photonOrExtendedOrNone': LATdatatype,
                   'spacecraft':'on' if spacecraftdata else 'off'}

        result = requests.post(self.request_url, data=payload)
        re_result = self.result_url_re.findall(result)

        if len(re_result) == 0:
            raise ValueError("Results did not contain a result url... something went awry (that hasn't been tested yet)")
        else:
            result_url = re_result[0]

        return result_url

class FermiLAT_DelayedQuery(object):

    fitsfile_re = re.compile('<a href="(.*?)">Available</a>')

    timeout = 30 # minutes

    check_frequency = 1 # minutes

    def __call__(self, result_url, check_frequency=1, verbose=False):
        self.result_url = result_url
        
        page_loaded = False

        elapsed_time = 0

        while not(page_loaded):
            page_loaded = fitsfile_urls = self._check_page()
            time.sleep(check_frequency * 60)
            elapsed_time += check_frequency
            # update progressbar here...

        if verbose:
            print "Query completed in %0.1f minutes" % (elapsed_time)

        return fitsfile_urls

    def _check_page(self):
        result_page = urllib.urlopen(self.result_url)

        pagedata = result_page.read()

        fitsfile_urls = self.fitsfile_re.findall(pagedata)

        if len(fitsfile_urls) == 0:
            return False
        else:
            return fitsfile_urls

