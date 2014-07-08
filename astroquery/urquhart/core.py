# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import os
import warnings
from bs4 import BeautifulSoup
import numpy as np

from astropy import units as u
from astropy import coordinates
from astropy import table

from ..query import BaseQuery
from ..utils import commons
from ..utils import async_to_sync

class UrquhartClass(BaseQuery):

    _urls = {'atlasgal':'ATLASGAL_SEARCH_RESULTS.cgi',
             'atlasgal_datapage':'ATLASGAL_SEARCH_RESULTS.cgi'}

    def __init__(self, timeout=60,
                 url='http://atlasgal.mpifr-bonn.mpg.de/cgi-bin/'):
        """
        """
        super(UrquhartClass, self).__init__()
        self.TIMEOUT = timeout
        self.URQUHART_SERVER = url
        self.ROOT_SERVER = 'http://atlasgal.mpifr-bonn.mpg.de/'


    def query_region_async(self, coordinates, radius=60*u.arcsec,
                           catalog='sextractor',
                           get_query_payload=False,
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

        return result

    def query_region(self, coordinates, table_index=0, **kwargs):
        """
        """

        result = self.query_region_async(coordinates, **kwargs)

        root = BeautifulSoup(result.content)
        if any(['There are no ATLASGAL sources within the search radius.' in x.text
                for x in root.findAll('h3')]):
            return None
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

        catalog_dict = {'sextractor':'Sextractor',
                          'gaussclump':'GaussClump', }


        payload = {'catalogue_field': catalog_dict[catalog],
                   'radius_field': radius.to(u.arcsec).value,
                   'text_field_1': '{0:f} {1:+f}'.format(coordinates.galactic.l.deg,
                                                         coordinates.galactic.b.deg)
                  }

        return payload

    def get_datapage(self, sourceid, catalog='sextractor', database='atlasgal_datapage'):
        """
        http://atlasgal.mpifr-bonn.mpg.de/cgi-bin/ATLASGAL_SEARCH_RESULTS.cgi?text_field_1=G019.4717%2B0.1702&catalogue_field=GaussClump&gc_flag=
        """

        catalog_dict = {'sextractor':'Sextractor',
                          'gaussclump':'GaussClump', }

        payload = {'catalogue_field': catalog_dict[catalog],
                   'text_field_1': sourceid,
                   'gc_flag':''
                  }
        
        result = self.request('POST', os.path.join(self.URQUHART_SERVER,
                                                   self._urls[database]),
                              data=payload)

        return result

    def get_spectra_async(self, sourceid_or_coordinate, catalog='sextractor',
                          radius=60*u.arcsec, line_searchstr='molecular_line'):
        """
        http://atlasgal.mpifr-bonn.mpg.de/atlasgal_images/molecular_line_data/atlasgal_cohrs/AGAL019.472+00.171_12CO_COHRS.fits
        http://atlasgal.mpifr-bonn.mpg.de//atlasgal_images/molecular_line_data/atlasgal_cohrs/AGAL019.472+00.171_12CO_COHRS.fits
        """
        if isinstance(sourceid_or_coordinate, coordinates.SkyCoord):
            tbl = self.query_region(sourceid_or_coordinate, radius=radius, catalog=catalog)
            if tbl is None or len(tbl) == 0:
                return None
            elif len(tbl) > 1:
                warnings.warn("Multiple matches found; returning first source: {0}".format(tbl['Name'][0]))

            sourceid = tbl['Name'][0]
        else:
            sourceid = sourceid_or_coordinate

        datapage = self.get_datapage(sourceid)

        root = BeautifulSoup(datapage.content)
        
        line_links = [self.ROOT_SERVER + x.get('href')
                      for x in root.findAll('a')
                      if (line_searchstr in x.get('href') and
                          x.get('href').endswith('fits'))]

        return [commons.FileContainer(U) for U in line_links]

    def get_spectra(self, *args, **kwargs):
        line_fileobjs = self.get_spectra_async(*args, **kwargs)

        if line_fileobjs is None:
            return None

        return [obj.get_fits() for obj in line_fileobjs]

Urquhart = UrquhartClass()
