# Licensed under a 3-clause BSD style license - see LICENSE.rst
import json
import re
import base64
import numpy as np
import requests
from copy import copy
from astropy.extern import six
from astropy.tests.helper import catch_warnings
from astropy.logger import log
from astropy.table import Table, Column
from astropy.coordinates import Angle, IllegalSecondWarning
from astropy import cosmology
from . import TEVCAT_SERVER, TEVCAT_TIMEOUT

__all__ = ['get_tevcat']

__doctest_skip__ = ['*']


def get_tevcat(with_notes=False):
    """Get TeVCat catalog as a table.

    Parameters
    ----------
    with_notes : bool
        Add the ``notes`` column.

    Returns
    -------
    table : `~astropy.table.Table`
        TeVCat catalog table

    Examples
    --------
    >>> from astroquery.tevcat import get_tevcat
    >>> table = get_tevcat()
    """
    tevcat = _TeVCat()

    tevcat._download_data()
    tevcat._extract_version()
    tevcat._extract_data()
    tevcat._make_table(with_notes=with_notes)

    return tevcat.table


class _TeVCat(object):
    """TeVCat info ( http://tevcat.uchicago.edu/ )"""

    def _download_data(self):
        """Gets the data and sets the 'data' and 'version' attributes"""
        log.info('Downloading {0} with timeout {1} sec (should be ~ 0.5 MB)'
                 ''.format(TEVCAT_SERVER(), TEVCAT_TIMEOUT()))
        self.response = requests.get(TEVCAT_SERVER(), timeout=TEVCAT_TIMEOUT())
        self.text = self.response.text

    def _extract_version(self):
        """"Extract the version number from the html"""
        pattern = 'Current Catalog Version:\s*(.*)\s*'
        matches = re.search(pattern, self.text)
        self.version = matches.group(1)

    def _extract_data(self):
        """Extract the data dict from the html"""
        pattern = 'var jsonData = atob\("(.*)"\);'
        matches = re.search(pattern, self.text)
        data1 = matches.group(1)
        data2 = base64.b64decode(data1)
        # The following line in necessary on Python 3 to get the escaping of
        # quotes in URLs in the `notes` fields right (simply converting to string
        # will results in an error in `json.loads`.
        # http://stackoverflow.com/questions/14453152/convering-double-backslash-to-single-backslash-in-python-3
        # http://stackoverflow.com/questions/21023162/python-3-pythonic-way-to-get-the-string-literal-representation-of-bytes
        # https://docs.python.org/3.4/library/base64.html
        data3 = data2.decode('utf8')
        data = json.loads(data3)
        # Keep the full data for debugging
        self._data = data
        # Store the useful parts
        self._sources = data['sources']
        self._catalogs = data['catalogs']

    def _make_table(self, with_notes=False):
        """Convert the data into a table object"""

        # This is the table that will contain the TeVCat
        table = Table()
        table.meta['name'] = 'TeVCat'
        table.meta['version'] = self.version

        # This is a temp table that has mostly columns of type "object"
        # We just use this here as a convenient way to group the column data
        # in arrays (`self._sources` is in a list of dicts format)
        t = Table(self._sources)

        # Fix up column dtype, missing values and unit one by one
        # (alphabetical order).
        table['canonical_name'] = _fix_data(t['canonical_name'])

        table['catalog_id'] = _fix_data(t['catalog_id'], int)

        catalog_id_name = [self._catalogs[str(int(_))]['name']
                           for _ in table['catalog_id']]
        table['catalog_id_name'] = Column(catalog_id_name,
                                          description='Name of sub-catalog containing this source')

        table['catalog_name'] = _fix_data(t['catalog_name'])

        with catch_warnings(IllegalSecondWarning):
            coord_dec = Angle(t['coord_dec'], 'degree').degree
            table['coord_dec'] = Column(coord_dec, unit='degree',
                                        description='Declination')

            coord_gal_lat = Angle(t['coord_gal_lat'], 'degree').degree
            table['coord_gal_lat'] = Column(coord_gal_lat, unit='degree',
                                            description='Galactic latitude')

            coord_gal_lon = Angle(t['coord_gal_lon'], 'degree').degree
            table['coord_gal_lon'] = Column(coord_gal_lon, unit='degree',
                                            description='Galactic longitude')

            coord_ra = Angle(t['coord_ra'], 'hour').degree
            table['coord_ra'] = Column(coord_ra, unit='degree',
                                       description='Right Ascension')

        # TODO: what does `coord_type` mean?
        coord_type = _fix_data(t['coord_type'], 'int')
        table['coord_type'] = Column(coord_type, description='Coordinate type')

        # TODO: translate integer code to string
        table['discoverer'] = _fix_data(t['discoverer'], 'int')

        # Store date in format that can be passed to astropy.time.Time as
        # Time(date, scale='utc', format='iso')
        date = _fix_date(t['discovery_date'])
        table['discovery_date'] = Column(date, description='Discovery date')

        distance = _fix_distance(t)
        table['distance'] = Column(distance, unit='kpc',
                                   description='Distance to source')

        eth = _fix_data(t['eth'], 'float')
        table['eth'] = Column(eth, unit='TeV', description='Energy threshold')

        # TODO: Which crab flux should be used as reference?
        flux = _fix_data(t['flux'], 'float')
        table['flux'] = Column(flux, description='Source flux (Crab nebula flux units)')

        greens_cat = _fix_data(t['greens_cat'])
        table['greens_cat'] = Column(greens_cat,
                                     description="URL to Green's catalog entry")

        table['id'] = _fix_data(t['id'], 'int')

        # Omitting `image` column ... not useful.
        # Omitting `marker_id` column ... not useful.

        if with_notes:
            table['notes'] = _fix_data(t['notes'])

        table['observatory_name'] = _fix_data(t['observatory_name'])

        table['other_names'] = _fix_data(t['other_names'])

        table['owner'] = _fix_data(t['owner'], 'int')

        if with_notes:
            table['private_notes'] = _fix_data(t['private_notes'])

        # Omitting `public` column ... not useful.

        size_x = _fix_data(t['size_x'], 'float')
        table['size_x'] = Column(size_x, unit='deg',
                                 description='Size (major axis)')

        size_y = _fix_data(t['size_y'], 'float')
        table['size_y'] = Column(size_y, unit='deg',
                                 description='Size (minor axis)')

        table['source_type'] = _fix_data(t['source_type'], 'int')

        table['source_type_name'] = _fix_data(t['source_type_name'])

        spec_idx = _fix_data(t['spec_idx'], 'float')
        table['spec_idx'] = Column(spec_idx, description='Spectral index')

        table['src_rank'] = _fix_data(t['src_rank'], 'int')

        table['variability'] = _fix_data(t['variability'], 'int')

        # This doesn't seem to have any effect ... column dtype is still unicode!?
        # 
        #table.convert_unicode_to_bytestring(python3_only=True)
        #table._convert_string_dtype('U', 'S', python3_only=True)

        # Store tables (the `sources_table` is mainly useful for debugging)
        self._sources_table = t
        self.table = table


def _fix_data(in_data, dtype='str', fill_value=None):

    # Use float for int columns to make `NaN` available for missing values
    #if dtype == 'int':
    #    dtype = 'float'

    if fill_value == None:
        if dtype == 'str':
            fill_value = ''
        elif dtype == 'float':
            fill_value = np.NAN
        elif dtype == 'int':
            fill_value = -99

    out_data = []
    for element in in_data:
        if element == None:
            out_data.append(fill_value)
        else:
            if dtype == 'str':
                if six.PY2:
                    element = element.encode('utf8')
                else:
                    try:
                        element = element.encode('ascii')
                    except Exception as e:
                        log.info('PROBLEMATIC STRING: {0}'.format(element))
                        log.info(e)
                        element = element.encode('ascii', errors='replace')
            elif dtype == 'float':
                element = float(element)
            elif dtype == 'int':
                element = int(element)
            out_data.append(element)

    return out_data
    #return np.array(out_data, dtype=dtype)
    # mask = [_ == None for _ in column]
    # return MaskedColumn(data=data, name=column.name, mask)


def _fix_date(in_data):
    out_data = []
    for element in in_data:
        out_data.append(element[0:4] + '-' + element[4:6] + '-01')

    return out_data


def _fix_distance(t):
    distance = _fix_data(t['distance'], 'float')
    distance_mod = _fix_data(t['distance_mod'], 'str')
    #mask = (distance_mod == 'z')

    try:
        cosmo = cosmology.default_cosmology.get()
    except:
        # compatibility with pre Astropy 0.4
        cosmo = cosmology.get_current()

    out_data = copy(distance)
    for ii in range(len(t)):
        if distance_mod[ii] == 'z':
            dist = cosmo.luminosity_distance(distance[ii]).to('kpc').value
            out_data[ii] = dist

    return distance
