
import math
import numpy as np
from astropy.extern.six import BytesIO
from astropy.table import Table
from astropy.io import ascii
from ..query import BaseQuery


class MiriadeClass(BaseQuery):
    
    body_number = {}
    body_number['mercury'] = 1
    body_number['venus']   = 2
    body_number['mars']    = 4
    body_number['jupiter'] = 5
    body_number['saturn']  = 6
    body_number['uranus']  = 7
    body_number['neptune'] = 8
    body_number['moon']    = 10
    body_number['sun']     = 11
    
    def __init__(self):
        super(MiriadeClass, self).__init__()
        self.observatory_codes = None
    
    def _observatory_codes(self):
        if self.observatory_codes is None:
            self.observatory_codes = ascii.read(BytesIO(self._request("GET", "http://www.minorplanetcenter.net/iau/lists/ObsCodes.html").content),
                                                format='fixed_width',
                                                col_starts=[0,4,13,21,30], col_ends=[3,12,20,29,100],
                                                header_start=1, data_start=2, data_end=-1)
        return self.observatory_codes
    
    def observatory_coordinates(self, observatory):
        results = Table(np.array([], dtype=self._observatory_codes().dtype))
        for obs in self.observatory_codes:
            if observatory.lower() in obs['Name'].lower():
                results.add_row(obs)
        if len(results) == 0:
            raise(Exception("Observatory {0} not found!".format(observatory)))
        elif len(results) > 1:
            raise(Exception("Observatory {0} not precise enough! Choose one of the following:\n{1}".format(observatory, results['Name'])))
        else:
            longitude = (-results[0]['Long.']+180.0)%360.0-180.0
            latitude = math.atan2(results[0]['sin'], results[0]['cos'])*180.0/math.pi
            return longitude, latitude
    
    def query_rise_transit_set(self, epoch, body, position, computation_number=1):
        longitude, latitude = self.observatory_coordinates(position)
        params = {}
        params['-ep'] = epoch
        params['-body'] = MiriadeClass.body_number[body.lower()]
        params['-nbd'] = computation_number
        params['-long'] = longitude
        params['-lat'] = latitude
        params['-mime'] = 'votable'
        params['-from'] = 'astroquery'
        response = self._request("GET", "http://vo.imcce.fr/webservices/miriade/rts_query.php", params)
        table = Table.read(BytesIO(response.content))
        return table

Miriade = MiriadeClass()
