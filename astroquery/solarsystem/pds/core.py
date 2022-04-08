
# 1. standard library imports
import numpy as np
from collections import OrderedDict

# 2. third party imports
from astropy.time import Time
from astropy.table import Table, Column

# 3. local imports - use relative imports
# commonly required local imports shown below as example
# all Query classes should inherit from BaseQuery.
## CHANGE TO RELATIVE IMPORTS ONCE THIS ALL WORKS RIGHT
from astroquery.query import BaseQuery
# import configurable items declared in __init__.py, e.g. hardcoded dictionaries
from __init__ import conf
from astroquery.utils import async_to_sync


@async_to_sync
class RingNodeClass(BaseQuery):
    '''
    for querying the Planetary Ring Node ephemeris tools
    <https://pds-rings.seti.org/tools/>
    
    '''
    
    TIMEOUT = conf.timeout
    
    def __init__(self, planet=None, obstime=None):
        '''Instantiate Planetary Ring Node query
        
        Parameters
        ----------
        planet : str, required. one of Jupiter, Saturn, Uranus, or Neptune
            Name, number, or designation of the object to be queried.
        obstime : str, in JD or MJD format. If no obstime is provided, the current
            time is used.
        '''
        
        super().__init__()
        self.planet = planet
        if self.planet is not None:
            self.planet = self.planet.lower()
            if self.planet not in ['jupiter', 'saturn', 'uranus', 'neptune']:
                raise ValueError("illegal value for 'planet' parameter (must be Jupiter, Saturn, Uranus, or Neptune")
        
        self.obstime = obstime
        
        
    def __str__(self):
        '''
        String representation of RingNodeClass object instance'
        
        Examples
        --------
        >>> from astroquery.solarsystem.pds import RingNode
        >>> uranus = Horizons(planet='Uranus',
        ...                 obstime='2017-01-01 00:00
        >>> print(uranus)  # doctest: +SKIP
        PDSRingNode instance "Uranus"; obstime=2017-01-01 00:00
        '''
        return ('PDSRingNode instance \"{:s}\"; obstime={:s}').format(
                    str(self.planet),
                    str(self.obstime))
    # --- pretty stuff above this line, get it working below this line ---  
    
    def ephemeris_async(self, 
                        get_query_payload=False,
                        get_raw_response=False, 
                        cache=True):
        '''
        send query to server
        
        note this interacts with utils.async_to_sync to be called as ephemeris()
        
        Returns
        -------
        response : `requests.Response`
            The response of the HTTP request.
        
        Examples
        --------
        >>> from astroquery.planetary.pds import RingNode
        >>> uranus = Horizons(planet='Uranus',
        ...                 obstime='2017-01-01 00:00
        >>> eph = obj.ephemeris()  # doctest: +SKIP
        >>> print(eph)  # doctest: +SKIP
            table here...
        '''
        
        URL = conf.pds_server
        #URL = 'https://pds-rings.seti.org/cgi-bin/tools/viewer3_xxx.pl?'
        
        # check for required information
        if self.planet is None:
            raise ValueError("'planet' parameter not set. Query aborted.")
        if self.obstime is None:
            self.obstime = Time.now().jd
    
        # configure request_payload for ephemeris query
        # start with successful query and incrementally de-hardcode stuff
        request_payload = OrderedDict([
            ('abbrev', self.planet[:3]),
            ('ephem', conf.planet_defaults[self.planet]['ephem']), # change hardcoding for other planets
            ('time', self.obstime),
            ('fov', 10), #for now do not care about the diagram. next few hardcoded
            ('fov_unit', self.planet.capitalize()+' radii'),
            ('center', 'body'), 
            ('center_body', self.planet.capitalize()),
            ('center_ansa', 'Epsilon Ring'),
            ('center_ew', 'east'),
            ('center_ra', ''),
            ('center_ra_type', 'hours'),
            ('center_dec', ''),
            ('center_star', ''),
            ('viewpoint', 'observatory'), # de-hardcode later!
            ('observatory', "Earth's center"), # de-hardcode later!
            ('latitude',''), # de-hardcode later!
            ('longitude',''), # de-hardcode later!
            ('lon_dir',''), # de-hardcode later!
            ('altitude',''), # de-hardcode later!
            ('moons',conf.planet_defaults[self.planet]['moons']), # change hardcoding for other planets
            ('rings','All rings'), # check if this works for other planets
            ('extra_ra',''), # diagram stuff. next few can be hardcoded
            ('extra_ra_type','hours'),
            ('extra_dec',''),
            ('extra_name',''),
            ('title',''),
            ('labels','Small (6 points)'),
            ('moonpts','0'),
            ('blank', 'No'),
            ('peris', 'None'),
            ('peripts', '4'),
            ('meridians', 'Yes'),
            ('output', 'html')
        ])
        
        # return request_payload if desired
        if get_query_payload:
            return request_payload

        # set return_raw flag, if raw response desired
        if get_raw_response:
            self.return_raw = True
        
        # query and parse
        response = self._request('GET', URL, params=request_payload,
                                timeout=self.TIMEOUT, cache=cache)                       
        self.uri = response.url
        
        ## questions
        # where does the Horizons one actually call the parser? I don't get it... is parse_response somehow put inside self._request? need to look at base class.
        # I guess this is supposed to return response as requests.Request object
        # but then when is parse_response used?
        # how does the Horizons one know to call ephemerides_async when it asks for ephemerides()?
        
        return response
        
    def _parse_ringnode(self, src):
        '''
        Routine for parsing data from ring node
        '''
        
        self.raw_response = src
        
        
        
        return src
                  
    def _parse_result(self, response, verbose = None):
        '''
        Routine for managing parser calls
        note this MUST be named exactly _parse_result so it interacts with async_to_sync properly
        
        Parameters
        ----------
        self :  RingNodeClass instance
        response : string
            raw response from server
        
        Returns
        -------
        data : `astropy.Table`
        '''
        self.last_response = response
        try:
            data = self._parse_ringnode(response.text)
        except:
            try:
                self._last_query.remove_cache_file(self.cache_location)
            except OSError:
                # this is allowed: if `cache` was set to False, this
                # won't be needed
                pass
            raise
        return data #astropy table
 
RingNode = RingNodeClass()   

if __name__ == "__main__":
    
    uranus = RingNodeClass('Uranus', '2019-10-28 00:00')
    response = uranus.ephemeris()
    print(response)
    