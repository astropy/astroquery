import requests
import re

result_url_re = re.compile('The results of your query may be found at <a href="(http://fermi.gsfc.nasa.gov/.*?)"')

class FermiLAT_Query(object):

    request_url = 'http://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/LATDataQuery.cgi'

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

        re_result = result_url_re.findall(result)

        if len(re_result) == 0:
            raise ValueError("Results did not contain a result url... something went awry (that hasn't been tested yet)")
        else:
            result_url = re_result[0]

        return result_url
