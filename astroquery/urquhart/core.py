# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import os
import warnings
import itertools
from bs4 import BeautifulSoup
import numpy as np

from astropy import units as u
from astropy import coordinates
from astropy import table

from ..query import BaseQuery
from ..utils import commons
from ..utils import async_to_sync

class UrquhartClass(BaseQuery):

    database_registry = {'atlasgal':'ATLASGAL_SEARCH_RESULTS.cgi',}

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
        Query the server with a set radius

        Parameters
        ----------
        coordinates : `astropy.coordinates.SkyCoord`
            A coordinate object
        radius : `astropy.units.degree` equivalent
            An angular radius
        catalog : str
            One of 'sextractor', 'gaussclump', depending on which catalog you
            wish to search (only appropriate for the ATLASGAL database)
        database : str
            The database name to query.  Must be in
            `UrquhartClass.database_registry`
        get_query_payload : bool
            Return the query data parameters instead of the result
        """
        payload = self._region_args_to_payload(coordinates,
                                               radius=radius,
                                               catalog=catalog)

        if get_query_payload:
            return payload

        result = self.request('POST', os.path.join(self.URQUHART_SERVER,
                                                   self.database_registry[database]),
                              data=payload)

        return result

    def query_region(self, coordinates, table_index=0, **kwargs):
        """
        See query_region_async

        Parameters
        ----------
        table_index : int
            The index of the table to extract from the search result page.  In
            general, this should be 0, but it is possible that some pages are
            restructured to have multiple tables in which case this parameter
            is needed
        """

        result = self.query_region_async(coordinates, **kwargs)

        root = BeautifulSoup(result.content, 'html5lib')
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
        Parse a coordinate object into a data payload
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

    def _get_datapage(self, sourceid, catalog='sextractor', database='atlasgal'):
        """
        Acquire the data page for a given source ID from a given catalog and
        database
        """

        catalog_dict = {'sextractor':'Sextractor',
                          'gaussclump':'GaussClump', }

        payload = {'catalogue_field': catalog_dict[catalog],
                   'text_field_1': sourceid,
                   'gc_flag':''
                  }
        
        result = self.request('POST', os.path.join(self.URQUHART_SERVER,
                                                   self.database_registry[database]),
                              data=payload)

        return result

    def _coord_or_sourceid_to_sourceid(self, sourceid_or_coordinate, radius, catalog):
        if isinstance(sourceid_or_coordinate, coordinates.SkyCoord):
            tbl = self.query_region(sourceid_or_coordinate, radius=radius, catalog=catalog)
            if tbl is None or len(tbl) == 0:
                return None
            elif len(tbl) > 1:
                warnings.warn("Multiple matches found; returning first source: {0}".format(tbl['Name'][0]))

            return tbl['Name'][0]
        else:
            return sourceid_or_coordinate

    def get_spectra_async(self, sourceid_or_coordinate, catalog='sextractor',
                          radius=60*u.arcsec, line_searchstr='molecular_line'):
        """
        Find and download spectra for a specified source

        Parameters
        sourceid_or_coordinate : str or `astropy.coordinates.SkyCoord`
            Either the exact source name from the selected database or a
            coordinate to search around
        radius : `astropy.units.degree` equivalent
            A search radius.  Only relevant if ``sourceid_or_coordinate`` is a
            coordinate
        catalog : 'sextractor' or 'gaussclumps'
            Catalog name
        line_searchstr : str
            A string to search URLs for to identify relevant spectral FITS
            files (NOT a regex)
        """
        sourceid = self._coord_or_sourceid_to_sourceid(sourceid_or_coordinate, radius, catalog)

        datapage = self._get_datapage(sourceid)

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

    get_spectra.__doc__ = get_spectra_async.__doc__

    def get_source_data(self, sourceid_or_coordinate, catalog='sextractor',
                        radius=60*u.arcsec):
        """
        Get the table data for a selected source
        """
        sourceid = self._coord_or_sourceid_to_sourceid(sourceid_or_coordinate, radius, catalog)

        datapage = self._get_datapage(sourceid, catalog=catalog)

        root = BeautifulSoup(datapage.content)

        tables = [self._parse_table(tb)
                  for tb in root.findAll('table')
                  if len(tb.findAll('tr'))>1 and len(tb.findAll('th'))>0]

        return tables

    def _parse_table(self, tb):
        """
        Attempt to parse a Table, which is a BeautifulSoup object containing
        match <th> and <td> rows
        """

        # This parsing can fail if the tables are malformed and have <th> with
        # no surrounding <tr>
        rows = tb.findAll('tr')

        # TERRIBLE HACK TIME
        all_th = tb.findAll('th')
        all_th_inrows = [x for r in rows for x in r.findAll('th')]
        missing_row = [t for t in all_th if t not in all_th_inrows]

        header_rows = [row for row in rows if row.findAll('th')]
        if missing_row:
            mr = BeautifulSoup("<table><tr>{0}</tr></table>".format("".join([x.encode() for x in missing_row])))
            header_rows.append(mr.findAll('table')[0].findAll('tr')[0])

        header_rows_iterable = []
        for hr in header_rows:
            H = [(x.text.strip(), int(x.attrs['colspan']))
                 if 'colspan' in x.attrs else
                 (x.text.strip(),1)
                 for x in hr.findAll('th')]
            header_rows_iterable.append([x for a in H for x in itertools.repeat(a[0],a[1])])

        headers = [" ".join(x).encode('ascii', errors='replace')
                   for x in zip(*header_rows_iterable)]

        #longest_header_row_length = max([len(row) for row in header_rows])
        #matched_header_rows = [row for row in header_rows
        #                       if len(row) == longest_header_row_length]
        #top_header_row = matched_header_rows[0]

        #headers = [x.text.strip().encode('ascii', errors='replace')
        #           for x in top_header_row.findAll('th')]

        for row in rows:
            datarow = row.findAll('td')
            if len(datarow) > 0:
                first_data_row = datarow
                break

        types = [determine_type(x) for x in first_data_row]

        content_rows=[]
        # exclude header row
        for row in rows[1:]:
            if len(row.findAll('th')) > 0:
                # skip header columns 
                continue
            if len(row.findAll('td')) == len(types):
                content = [dt(td.text) for td,dt in zip(row.findAll('td'),types)]
                content_rows.append(content)
            else:
                raise ValueError("Mismatch between n(headers) and n(columns)")

        dtypes = []
        for ii,tp in enumerate(types):
            if tp is str:
                strlen = max([len(x[ii]) for x in content_rows])
                dtypes.append(np.dtype('S{0}'.format(strlen)))
            else:
                dtypes.append(tp)

        tbl = table.Table(names=headers,
                          dtype=dtypes)

        for content in content_rows:
            tbl.add_row(content)

        return tbl


            
def determine_type(x):
    """ Determine a valid numerical type of a string (maybe) """
    try:
        a = float(x.strip())
        try:
            b = int(x.strip())
            if a-x == 0:
                return int
            else:
                return float
        except (TypeError,ValueError):
            return float
    except (TypeError,ValueError):
        return str

Urquhart = UrquhartClass()
