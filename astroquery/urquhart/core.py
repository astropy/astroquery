# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
from collections import CaseInsensitiveDict
import os

from astropy import units as u
from astropy import coordinates

from ..query import BaseQuery
from ..utils import commons

class UrquhartClass(BaseQuery):

    _urls = CaseInsensitiveDict({'atlasgal':'ATLASGAL_DATABASE.cgi',
                                 'atlasgal_datapage':'ATLASGAL_SEARCH_RESULTS.cgi'})

    def __init__(self, timeout=60,
                 url='http://atlasgal.mpifr-bonn.mpg.de/cgi-bin/'):
        """
        """
        self.TIMEOUT = timeout
        self.URQUHART_SERVER = url


    def query_region_async(self, coordinates, radius=60*u.arcsec,
                           catalog='sextractor',
                           get_query_payload=False,
                           table_index=0,
                           database='atlasgal'):
        """

        Parameters
        ----------
        catalog : str
            One of 'sextractor', 'gaussclump'
        """
        payload = self._region_args_to_payload(coordinates,
                                               radius=radius,
                                               catalog=catalog)

        if get_query_payload:
            return payload

        result = self.request('POST', os.path.join(self.URQUHART_SERVER,
                                                   self._urls[database]),
                              data=payload)

        root = BeautifulSoup(response.content)
        tables = root.findAll('table')[table_index]
        rows = tables.findAll('tr')

        dtypes = (np.dtype('S18'), np.dtype('S18'), np.dtype('S18'), float, float)
        types = (str, str, str, float, float)

        tbl = table.Table(names=['Name', 'RA', 'Dec', 'Offset', 'Peak Flux'],
                          dtype=dtypes)

        for row in rows:
            if len(row.findAll('td')) >= len(types):
                content = [dt(td.text) for td,dt in zip(row.findAll('td'),types)]
                tbl.add_row(content)

        return tbl


    def _region_args_to_payload(self, coordinates, radius=60*u.arcsec, catalog='sextractor'):
        """
        """
        # Example:
        # http://atlasgal.mpifr-bonn.mpg.de/cgi-bin/ATLASGAL_SEARCH_RESULTS.cgi?text_field_1=19.482+%2B0.173&radius_field=60&catalogue_field=GaussClump+%28GCSC%29

        catalogue_dict = CaseInsensitiveDict({'sextractor':'Sextractor',
                                              'gaussclump':'GaussClump', })


        payload = {'catalogue_field': catalogue_dict[catalog],
                   'radius_field': radius.to(u.arcsec).value,
                   'text_field_1': '{0:f} {1:+f}'.format(coordinates.galactic.l.deg,
                                                         coordinates.galactic.b.deg)
                  }

        return payload

    def get_datapage(self, sourceid, catalogue='sextractor', database='atlasgal_datapage'):
        """
        http://atlasgal.mpifr-bonn.mpg.de/cgi-bin/ATLASGAL_SEARCH_RESULTS.cgi?text_field_1=G019.4717%2B0.1702&catalogue_field=GaussClump&gc_flag=
        """

        payload = {'catalogue_field': catalogue_dict[catalog],
                   'text_field_1': sourceid,
                   'gc_flag':''
                  }
        
        result = self.request('POST', os.path.join(self.URQUHART_SERVER,
                                                   self._urls[database]),
                              data=payload)

        return result

    def get_spectra_async(self, sourceid_or_coordinate, catalogue='sextractor',
                          radius=60*u.arcsec, line_searchstr='molecular_line'):
        """
        """
        if isinstance(sourceid_or_coordinate, coordinates.SkyCoord):
            tbl = self.query(sourceid_or_coordinate, radius=radius, catalogue=catalogue)
            if len(tbl) > 1:
                warnings.warn("Multiple matches found; returning first source: {0}".format(tbl['Name'][0]))
            elif len(tbl) == 0:
                return None

            sourceid = tbl['Name'][0]
        else:
            sourceid = sourceid_or_coordinate

        datapage = self.get_datapage(sourceid)

        line_links = [x for x in root.findAll('a')
                      if (line_searchstr in x.get('href') and
                          x.get('href').endswith('fits'))]

        return [commons.FileContainer(U) for U in line_links]

    def get_spectra(self, *args, **kwargs):
        line_fileobjs = self.get_spectra_async(*args, **kwargs)

        return [obj.get_fits() for obj in line_fileobjs]

Urquhart = UrquhartClass()
