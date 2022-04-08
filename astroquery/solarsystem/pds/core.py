
# 1. standard library imports
import numpy as np
from collections import OrderedDict
import re

# 2. third party imports
from astropy.time import Time
from astropy import table
from astropy.io import ascii
from bs4 import BeautifulSoup

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
    
    def __init__(self, planet=None, obs_time=None):
        '''Instantiate Planetary Ring Node query
        
        Parameters
        ----------
        planet : str, required. one of Jupiter, Saturn, Uranus, or Neptune
            Name, number, or designation of the object to be queried.
        obs_time : str, in JD or MJD format. If no obs_time is provided, the current
            time is used.
        '''
        
        super().__init__()
        self.planet = planet
        if self.planet is not None:
            self.planet = self.planet.lower()
            if self.planet not in ['mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']:
                raise ValueError("illegal value for 'planet' parameter (must be 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', or 'Pluto'")
        
        self.obs_time = obs_time
        
        
    def __str__(self):
        '''
        String representation of RingNodeClass object instance'
        
        Examples
        --------
        >>> from astroquery.solarsystem.pds import RingNode
        >>> uranus = Horizons(planet='Uranus',
        ...                 obs_time='2017-01-01 00:00
        >>> print(uranus)  # doctest: +SKIP
        PDSRingNode instance "Uranus"; obs_time=2017-01-01 00:00
        '''
        return ('PDSRingNode instance \"{:s}\"; obs_time={:s}').format(
                    str(self.planet),
                    str(self.obs_time))
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
        ...                 obs_time='2017-01-01 00:00
        >>> eph = obj.ephemeris()  # doctest: +SKIP
        >>> print(eph)  # doctest: +SKIP
            table here...
        '''
        
        URL = conf.pds_server
        #URL = 'https://pds-rings.seti.org/cgi-bin/tools/viewer3_xxx.pl?'
        
        # check for required information
        if self.planet is None:
            raise ValueError("'planet' parameter not set. Query aborted.")
        if self.obs_time is None:
            self.obs_time = Time.now().jd
            
        '''    
        https://pds-rings.seti.org/cgi-bin/tools/viewer3_xxx.pl?abbrev=jup&ephem=000+JUP365+%2B+DE440&time=2021-10-07+07%3A25&fov=10&fov_unit=Jupiter+radii&center=body&center_body=Jupiter&center_ansa=Main+Ring&center_ew=east&center_ra=&center_ra_type=hours&center_dec=&center_star=&viewpoint=observatory&observatory=Earth%27s+center&latitude=&longitude=&lon_dir=east&altitude=&moons=516+All+inner+moons+%28J1-J5%2CJ14-J16%29&rings=Main+%26+Gossamer&torus_inc=6.8&torus_rad=422000&extra_ra=&extra_ra_type=hours&extra_dec=&extra_name=&title=&labels=Small+%286+points%29&moonpts=0&blank=No&meridians=Yes&output=HTML
        '''
    
        # configure request_payload for ephemeris query
        # start with successful query and incrementally de-hardcode stuff
        # thankfully, adding extra planet-specific keywords here does not break query for other planets
        request_payload = OrderedDict([
            ('abbrev', self.planet[:3]),
            ('ephem', conf.planet_defaults[self.planet]['ephem']), # change hardcoding for other planets
            ('time', self.obs_time),
            ('fov', 10), #for now do not care about the diagram. next few hardcoded
            ('fov_unit', self.planet.capitalize()+' radii'),
            ('center', 'body'), 
            ('center_body', self.planet.capitalize()),
            ('center_ansa', conf.planet_defaults[self.planet]['center_ansa']),
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
            ('rings',conf.planet_defaults[self.planet]['rings']), # check if this works for other planets
            ('arcmodel','#3 (820.1121 deg/day)'), # check if this works for other planets 
            ('extra_ra',''), # diagram stuff. next few can be hardcoded
            ('extra_ra_type','hours'),
            ('extra_dec',''),
            ('extra_name',''),
            ('title',''),
            ('labels','Small (6 points)'),
            ('moonpts','0'),
            ('blank', 'No'),
            ('opacity', 'Transparent'),
            ('peris', 'None'),
            ('peripts', '4'),
            ('arcpts', '4'),
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
        
        Parameters
        ----------
        self : HorizonsClass instance
        src : list
            raw response from server


        Returns
        -------
        data : `astropy.Table`
        '''
        
        self.raw_response = src
        soup = BeautifulSoup(src, 'html.parser')
        text = soup.get_text()
        #print(repr(text))
        textgroups = re.split('\n\n|\n \n', text)
        ringtable = None
        for group in textgroups:
            group = group.strip(', \n')
            
            #input parameters. only thing needed is obs_time
            if group.startswith('Observation'): 
                obs_time = group.split('\n')[0].split('e: ')[-1].strip(', \n')
                self.obs_time = obs_time

            #minor body table part 1
            elif group.startswith('Body'): 
                group = 'NAIF '+group #fixing lack of header for NAIF ID
                bodytable = ascii.read(group, format='fixed_width',
                            col_starts=(0, 4, 18, 35, 54, 68, 80, 91),
                            col_ends=  (4, 18, 35, 54, 68, 80, 91, 102),
                            names = ('NAIF ID', 'Body', 'RA', 'Dec', 'RA (deg)', 'Dec (deg)', 'dRA', 'dDec')
                            )
            #minor body table part 2    
            elif group.startswith('Sub-'): 
                group = '\n'.join(group.split('\n')[1:]) #fixing two-row header
                group = 'NAIF'+group[4:]
                bodytable2 = ascii.read(group, format='fixed_width',
                            col_starts=(0, 4, 18, 28, 37, 49, 57, 71),
                            col_ends=  (4, 18, 28, 37, 49, 57, 71, 90),
                            names = ('NAIF ID', 'Body', 'sub_obs_lon', 'sub_obs_lat', 'sub_sun_lon', 'sub_sun_lat', 'phase', 'distance')
                            )
                ## to do: add units!!
            
            #ring plane data    
            elif group.startswith('Ring s'): 
                lines = group.split('\n')
                for line in lines:
                    l = line.split(':')
                    if 'Ring sub-solar latitude' in l[0]:
                        [sub_sun_lat, sub_sun_lat_min, sub_sun_lat_max] = [float(s.strip(', \n()')) for s in re.split('\(|to', l[1])]
                        systemtable = table.Table([['sub_sun_lat','sub_sun_lat_max','sub_sun_lat_min'],
                                                 [sub_sun_lat, sub_sun_lat_max, sub_sun_lat_min]],
                                                 names = ('Parameter', 'Value'))

                    elif 'Ring plane opening angle' in l[0]:
                        systemtable.add_row(['opening_angle', float(re.sub('[a-zA-Z]+', '', l[1]).strip(', \n()'))])
                    elif 'Ring center phase angle' in l[0]:
                        systemtable.add_row(['phase_angle', float(l[1].strip(', \n'))])
                    elif 'Sub-solar longitude' in l[0]:
                        systemtable.add_row(['sub_sun_lon', float(re.sub('[a-zA-Z]+', '', l[1]).strip(', \n()'))])
                    elif 'Sub-observer longitude' in l[0]:
                        systemtable.add_row(['sub_obs_lon', float(l[1].strip(', \n'))])
                    else:
                        pass
                ## to do: add units?
            
            #basic info about the planet        
            elif group.startswith('Sun-planet'): 
                lines = group.split('\n')
                for line in lines:
                    l = line.split(':')
                    if 'Sun-planet distance (AU)' in l[0]:
                        systemtable.add_row(['d_sun_AU', float(l[1].strip(', \n'))])
                    elif 'Observer-planet distance (AU)' in l[0]:
                        systemtable.add_row(['d_obs_AU', float(l[1].strip(', \n'))])
                    elif 'Sun-planet distance (km)' in l[0]:
                        systemtable.add_row(['d_sun_km', float(l[1].split('x')[0].strip(', \n'))*1e6])
                    elif 'Observer-planet distance (km)' in l[0]:
                        systemtable.add_row(['d_obs_km', float(l[1].split('x')[0].strip(', \n'))*1e6])
                    elif 'Light travel time' in l[0]:
                        systemtable.add_row(['light_time', float(l[1].strip(', \n'))])
                    else:
                        pass
                    
                ## to do: add units?
                
            # --------- below this line, planet-specific info ------------ 
            # Uranus individual rings data   
            elif group.startswith('Ring    '): 
                ringtable = ascii.read('     '+group, format='fixed_width',
                            col_starts=(5, 18, 29),
                            col_ends=  (18, 29, 36),
                            names = ('ring', 'pericenter', 'ascending node')
                            )
            
            # Saturn F-ring data - NEEDS TESTING
            elif group.startswith('F Ring'):
                lines = group.split('\n')
                for line in lines:
                    l = line.split(':')
                    if 'F Ring pericenter' in l[0]:
                        peri = float(re.sub('[a-zA-Z]+', '', l[1]).strip(', \n()'))
                    elif 'F Ring ascending node' in l[0]:
                        ascn = float(l[1].strip(', \n'))
                ringtable = table.Table([['F'], [peri], [ascn]], names=('ring', 'pericenter', 'ascending node'))
            
            # Neptune ring arcs data - NEEDS TESTING  
            elif group.startswith('Courage'): 
                lines = group.split('\n')
                for i in range(len(lines)):
                    l = lines[i].split(':')
                    ring = l[0].split('longitude')[0].strip(', \n')
                    [min_angle, max_angle] = [float(s.strip(', \n')) for s in re.sub('[a-zA-Z]+', '', l[1]).strip(', \n()').split()]
                    if i == 0:
                        ringtable = table.Table([[ring], [min_angle], [max_angle]], names=('ring', 'min_angle', 'max_angle'))
                    else:
                        ringtable.add_row([ring, min_angle, max_angle])
                
            else:
                pass
        
        # concatenate minor body table    
        bodytable = table.join(bodytable, bodytable2)
        
        return systemtable, bodytable, ringtable
                  
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
            systemtable, bodytable, ringtable = self._parse_ringnode(response.text)
        except:
            try:
                self._last_query.remove_cache_file(self.cache_location)
            except OSError:
                # this is allowed: if `cache` was set to False, this
                # won't be needed
                pass
            raise
        return systemtable, bodytable, ringtable #astropy table, astropy table, astropy table
 
RingNode = RingNodeClass()   

if __name__ == "__main__":
    
    # single basic query
    neptune = RingNodeClass('Neptune', '2019-10-28 00:00')
    systemtable, bodytable, ringtable = neptune.ephemeris()
    
    '''
    # basic query for all six targets
    for major_body in ['mars', 'jupiter', 'uranus', 'saturn', 'neptune', 'pluto']:
        nodequery = RingNode(major_body, '2022-05-03 00:00')
        systemtable, bodytable, ringtable = nodequery.ephemeris()
        
        print(' ')
        print(' ')
        print('~'*40)
        print(major_body)
        print('~'*40)
        print(systemtable)
        print(bodytable)
        print(ringtable)
     '''
    
    