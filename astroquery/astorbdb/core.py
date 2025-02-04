# Licensed under a 3-clause BSD style license - see LICENSE.rst

import astropy.units as u
from astropy.time import Time
import json
from collections import OrderedDict

from ..query import BaseQuery
from ..utils import async_to_sync
from . import conf

__all__ = ['AstInfo', 'AstInfoClass']


@async_to_sync
class AstInfoClass(BaseQuery):

    """
    A class for querying Lowell Observatory's `astorbDB
    <https://asteroid.lowell.edu/>`_ service.
    """
    # Not all the methods below are necessary but these cover most of the common
    # cases, new methods may be added if necessary, follow the guidelines at
    # <http://astroquery.readthedocs.io/en/latest/api.html>

    URL = conf.server
    TIMEOUT = conf.timeout

    # internal flag whether to return the raw reponse
    _return_raw = False

    # actual query uri
    _uri = None

    def designations_async(self, object_name, *,
                           get_raw_response=False,
                           get_uri=False,
                           cache=True):
        """
        This method uses a REST interface to query the `Lowell Observatory
        astorbDB database <https://asteroid.lowell.edu/>`_ for designation
        data for a single object and returns a dictionary from JSON results

        Parameters
        ----------
        object_name : str
            name of the identifier to query.

        Returns
        -------
        res : A dictionary holding available designation data

        Examples
        --------
        >>> from astroquery.astorbdb import AstInfo
        >>> designations = AstInfo.designations('Beagle')
        >>> print(designations)
        OrderedDict({'alternate_designations': ['1954 HJ', 'A908 BJ', 'A917 ST'], 'name': 'Beagle', 'number': 656, 'primary_designation': 'Beagle'})
        """

        self.query_type = 'designations'

        response = self._request('GET',
            url=self.URL + object_name + '/designations',
            timeout=self.TIMEOUT, cache=cache)

        if get_raw_response:
            self._return_raw = True

        if get_uri:
            self._uri = response.url

        return response

    def elements_async(self, object_name, *,
                           get_raw_response=False,
                           get_uri=False,
                           cache=True):
        """
        This method uses a REST interface to query the `Lowell Observatory
        astorbDB database <https://asteroid.lowell.edu/>`_ for orbital element
        data for a single object and returns a dictionary from JSON results

        Parameters
        ----------
        object_name : str
            name of the identifier to query.

        Returns
        -------
        res : A dictionary holding available orbital element data

        Examples
        --------
        >>> from astroquery.astorbdb import AstInfo
        >>> elements = AstInfo.elements('Beagle')
        >>> print(elements)
        OrderedDict({'a': <Quantity 3.15597543 AU>, 'aphelion_dist': <Quantity 3.57009832 AU>, ...})
        """

        self.query_type = 'elements'

        response = self._request('GET',
            url=self.URL + object_name + '/elements',
            timeout=self.TIMEOUT, cache=cache)

        if get_raw_response:
            self._return_raw = True

        if get_uri:
            self._uri = response.url

        return response

    def orbit_async(self, object_name, *,
                    get_raw_response=False,
                    get_uri=False,
                    cache=True):
        """
        This method uses a REST interface to query the `Lowell Observatory
        astorbDB database <https://asteroid.lowell.edu/>`_ for orbit
        data for a single object and returns a dictionary from JSON results

        Parameters
        ----------
        object_name : str
            name of the identifier to query.

        Returns
        -------
        res : A dictionary holding available orbit data

        Examples
        --------
        >>> from astroquery.astorbdb import AstInfo
        >>> orbit = AstInfo.orbit('Beagle')
        >>> print(orbit)
        OrderedDict({'a1con': <Quantity 0. AU / d2>, 'a2con': <Quantity 0. AU / d2>, 'a3con': <Quantity 0. AU / d2>, ...})
        """

        self.query_type = 'orbit'

        response = self._request('GET',
            url=self.URL + object_name + '/orbit',
            timeout=self.TIMEOUT, cache=cache)

        if get_raw_response:
            self._return_raw = True

        if get_uri:
            self._uri = response.url

        return response

    def albedos_async(self, object_name, *,
                    get_raw_response=False,
                    get_uri=False,
                    cache=True):
        """
        This method uses a REST interface to query the `Lowell Observatory
        astorbDB database <https://asteroid.lowell.edu/>`_ for albedo
        data for a single object and returns a dictionary from JSON results

        Parameters
        ----------
        object_name : str
            name of the identifier to query.

        Returns
        -------
        res : A dictionary holding available albedo data

        Examples
        --------
        >>> from astroquery.astorbdb import AstInfo
        >>> albedos = AstInfo.albedos('Beagle')
        >>> print(albedos)
        [{'albedo': 0.065, 'albedo_error_lower': -0.002, ..., 'survey_name': 'Usui et al. (2011)'},
         {'albedo': 0.0625, 'albedo_error_lower': -0.015, ..., 'survey_name': 'Infrared Astronomical Satellite (IRAS)'},
         ...]
        """

        self.query_type = 'albedos'

        response = self._request('GET',
            url=self.URL + object_name + '/data/albedos',
            timeout=self.TIMEOUT, cache=cache)

        if get_raw_response:
            self._return_raw = True

        if get_uri:
            self._uri = response.url

        return response

    def colors_async(self, object_name, *,
                    get_raw_response=False,
                    get_uri=False,
                    cache=True):
        """
        This method uses a REST interface to query the `Lowell Observatory
        astorbDB database <https://asteroid.lowell.edu/>`_ for color
        data for a single object and returns a dictionary from JSON results

        Parameters
        ----------
        object_name : str
            name of the identifier to query.

        Returns
        -------
        res : A dictionary holding available color data

        Examples
        --------
        >>> from astroquery.astorbdb import AstInfo
        >>> colors = AstInfo.colors('Beagle')
        >>> print(colors)
        [{'citation_bibcode': '2010PDSS..125.....S', ..., 'color': 0.431, 'color_error': 0.035, ..., 'sys_color': 'J-H'},
         {'citation_bibcode': '2010PDSS..125.....S', ..., 'color': 0.076, 'color_error': 0.041, ..., 'sys_color': 'H-K'},
         ...]
        """

        self.query_type = 'colors'

        response = self._request('GET',
            url=self.URL + object_name + '/data/colors',
            timeout=self.TIMEOUT, cache=cache)

        if get_raw_response:
            self._return_raw = True

        if get_uri:
            self._uri = response.url

        return response

    def taxonomies_async(self, object_name, *,
                         get_raw_response=False,
                         get_uri=False,
                         cache=True):
        """
        This method uses a REST interface to query the `Lowell Observatory
        astorbDB database <https://asteroid.lowell.edu/>`_ for taxonomy
        data for a single object and returns a dictionary from JSON results

        Parameters
        ----------
        object_name : str
            name of the identifier to query.

        Returns
        -------
        res : A dictionary holding available taxonomy data

        Examples
        --------
        >>> from astroquery.astorbdb import AstInfo
        >>> taxonomies = AstInfo.taxonomies('Beagle')
        >>> print(taxonomies)
        [{'citation_bibcode': '2011PDSS..145.....H', ..., 'survey_name': 'Carvano et al. (2010)', 'taxonomy': 'C', ...},
         {'citation_bibcode': '2013Icar..226..723D', ..., 'survey_name': 'DeMeo et al. (2013)', 'taxonomy': 'C', ...}]
        """

        self.query_type = 'taxonomies'

        response = self._request('GET',
            url=self.URL + object_name + '/data/taxonomies',
            timeout=self.TIMEOUT, cache=cache)

        if get_raw_response:
            self._return_raw = True

        if get_uri:
            self._uri = response.url

        return response

    def lightcurves_async(self, object_name, *, 
                          get_raw_response=False,
                          get_uri=False,
                          cache=True):
        """
        This method uses a REST interface to query the `Lowell Observatory
        astorbDB database <https://asteroid.lowell.edu/>`_ for lightcurve
        data for a single object and returns a dictionary from JSON results

        Parameters
        ----------
        object_name : str
            name of the identifier to query.

        Returns
        -------
        res : A dictionary holding available lightcurve data

        Examples
        --------
        >>> from astroquery.astorbdb import AstInfo
        >>> lightcurves = AstInfo.lightcurves('Beagle')
        >>> print(lightcurves)
        [{'ambiguous_period': False, ..., 'amp_max': <Quantity 1.2 mag>, 'amp_min': <Quantity 0.57 mag>, ..., 'period': <Quantity 7.035 h>, ...}]
        """

        self.query_type = 'lightcurves'

        response = self._request('GET',
            url=self.URL + object_name + '/data/lightcurves',
            timeout=self.TIMEOUT, cache=cache)

        if get_raw_response:
            self._return_raw = True

        if get_uri:
            self._uri = response.url

        return response

    def dynamicalfamily_async(self, object_name, *,
                              get_raw_response=False,
                              get_uri=False,
                              cache=True):
        """
        This method uses a REST interface to query the `Lowell Observatory
        astorbDB database <https://asteroid.lowell.edu/>`_ for dynamical family
        data for a single object and returns a dictionary from JSON results

        Parameters
        ----------
        object_name : str
            name of the identifier to query.

        Returns
        -------
        res : A dictionary holding available dynamical family data

        Examples
        --------
        >>> from astroquery.astorbdb import AstInfo
        >>> dynamicalfamily = AstInfo.dynamicalfamily('Beagle')
        >>> print(dynamicalfamily)
        [{'citation_bibcode': '2015PDSS..234.....N', ..., 'family': 'Themis', ...},
         {'citation_bibcode': '2015PDSS..234.....N', ..., 'family': 'Beagle', ...}]
        """

        self.query_type = 'dynamicalfamily'

        response = self._request('GET',
            url=self.URL + object_name + '/data/dynamical-family',
            timeout=self.TIMEOUT, cache=cache)

        if get_raw_response:
            self._return_raw = True

        if get_uri:
            self._uri = response.url

        return response

    def escaperoutes_async(self, object_name, *,
                           get_raw_response=False,
                           get_uri=False,
                           cache=True):
        """
        This method uses a REST interface to query the `Lowell Observatory
        astorbDB database <https://asteroid.lowell.edu/>`_ for NEO escape route
        data for a single object and returns a dictionary from JSON results

        Parameters
        ----------
        object_name : str
            name of the identifier to query.

        Returns
        -------
        res : A dictionary holding available NEO escape route data

        Examples
        --------
        >>> from astroquery.astorbdb import AstInfo
        >>> escaperoutes = AstInfo.escaperoutes('3552')
        >>> print(escaperoutes)
        [{'citation_bibcode': '2018Icar..312..181G', ..., 'dp21_complex': 0.03695, 'dp31_complex': 0.00105, ...}]
        """

        self.query_type = 'escaperoutes'

        response = self._request('GET',
            url=self.URL + object_name + '/data/escape-routes',
            timeout=self.TIMEOUT, cache=cache)

        if get_raw_response:
            self._return_raw = True

        if get_uri:
            self._uri = response.url

        return response

    def all_astinfo_async(self, object_name, *,
                           get_raw_response=False,
                           get_uri=False,
                           cache=True):
        """
        This method uses REST interfaces to query the `Lowell Observatory
        astorbDB database <https://asteroid.lowell.edu/>`_ for all AstInfo
        data for a single object and returns a dictionary from JSON results

        Parameters
        ----------
        object_name : str
            name of the identifier to query.

        Returns
        -------
        res : A dictionary holding available AstInfo data

        Examples
        --------
        >>> from astroquery.astorbdb import AstInfo
        >>> all_astinfo = AstInfo.all_astinfo('Beagle')
        >>> print(all_astinfo)
        OrderedDict({
        'designations': OrderedDict({'alternate_designations': ['1954 HJ', 'A908 BJ', 'A917 ST'], 'name': 'Beagle', ...}),
        'elements': OrderedDict({'a': <Quantity 3.15597543 AU>, 'aphelion_dist': <Quantity 3.57009832 AU>, ...}),
        'orbit': OrderedDict({'a1con': <Quantity 0. AU / d2>, 'a2con': <Quantity 0. AU / d2>, 'a3con': <Quantity 0. AU / d2>, ...}),
        'albedos': [{'albedo': 0.065, 'albedo_error_lower': -0.002, 'albedo_error_upper': 0.002, ..., 'survey_name': 'Usui et al. (2011)'},
                    {'albedo': 0.0625, 'albedo_error_lower': -0.015, 'albedo_error_upper': 0.015, ..., 'survey_name': 'Infrared Astronomical Satellite (IRAS)'},
                    ...],
        'colors': [{'citation_bibcode': '2010PDSS..125.....S', ..., 'color': 0.431, 'color_error': 0.035, ..., 'sys_color': 'J-H'},
                   {'citation_bibcode': '2010PDSS..125.....S', ..., 'color': 0.076, 'color_error': 0.041, ..., 'sys_color': 'H-K'},
                   ...],
        'taxonomies': [{'citation_bibcode': '2011PDSS..145.....H', ..., 'survey_name': 'Carvano et al. (2010)', 'taxonomy': 'C', ...},
                       {'citation_bibcode': '2013Icar..226..723D', ..., 'survey_name': 'DeMeo et al. (2013)', 'taxonomy': 'C', ...}],
        'lightcurves': [{'ambiguous_period': False, ..., 'amp_max': <Quantity 1.2 mag>, 'amp_min': <Quantity 0.57 mag>, ..., 'period': <Quantity 7.035 h>, ...}],
        'dynamicalfamily': [{'citation_bibcode': '2015PDSS..234.....N', ..., 'family': 'Themis', ...},
                            {'citation_bibcode': '2015PDSS..234.....N', ..., 'family': 'Beagle', ...}],
        'escaperoutes': []
        })
        """

        self.query_type = 'all_astinfo'

        response = {}

        response['designations'] = self._request('GET',
            url=self.URL + object_name + '/designations',
            timeout=self.TIMEOUT, cache=cache)

        response['elements'] = self._request('GET',
            url=self.URL + object_name + '/elements',
            timeout=self.TIMEOUT, cache=cache)

        response['orbit'] = self._request('GET',
            url=self.URL + object_name + '/orbit',
            timeout=self.TIMEOUT, cache=cache)

        response['albedos'] = self._request('GET',
            url=self.URL + object_name + '/data/albedos',
            timeout=self.TIMEOUT, cache=cache)

        response['colors'] = self._request('GET',
            url=self.URL + object_name + '/data/colors',
            timeout=self.TIMEOUT, cache=cache)

        response['taxonomies'] = self._request('GET',
            url=self.URL + object_name + '/data/taxonomies',
            timeout=self.TIMEOUT, cache=cache)

        response['lightcurves'] = self._request('GET',
            url=self.URL + object_name + '/data/lightcurves',
            timeout=self.TIMEOUT, cache=cache)

        response['dynamicalfamily'] = self._request('GET',
            url=self.URL + object_name + '/data/dynamical-family',
            timeout=self.TIMEOUT, cache=cache)

        response['escaperoutes'] = self._request('GET',
            url=self.URL + object_name + '/data/escape-routes',
            timeout=self.TIMEOUT, cache=cache)

        if get_raw_response:
            self._return_raw = True

        if get_uri:
            self._uri = {'designations':response['designations'].url,
                         'elements':response['elements'].url,
                         'orbit':response['orbit'].url,
                         'albedos':response['albedos'].url,
                         'colors':response['colors'].url,
                         'taxonomies':response['taxonomies'].url,
                         'lightcurves':response['lightcurves'].url,
                         'dynamicalfamily':response['dynamicalfamily'].url,
                         'escaperoutes':response['escaperoutes'].url
                        }

        return response

    def _parse_result(self, response, *, verbose=None):
        """
        Parser for astorbDB AstInfo request results
        """

        if self._return_raw:
            return response.text

        # decode json response from Lowell astorbDB into ascii
        try:
            if self.query_type == 'all_astinfo':
                src = OrderedDict()
                for key in response:
                    src[key] = OrderedDict(json.loads(response[key].text))
            else:
                src = OrderedDict(json.loads(response.text))
        except ValueError:
            raise ValueError('Server response not readable.')

        if self.query_type == 'designations':
            src = self._process_data_designations(src)

        if self.query_type == 'elements':
            src = self._process_data_elements(src)

        if self.query_type == 'orbit':
            src = self._process_data_orbit(src)

        if self.query_type == 'albedos':
            src = self._process_data_albedos(src)

        if self.query_type == 'colors':
            src = self._process_data_colors(src)

        if self.query_type == 'taxonomies':
            src = self._process_data_taxonomies(src)

        if self.query_type == 'lightcurves':
            src = self._process_data_lightcurves(src)

        if self.query_type == 'dynamicalfamily':
            src = self._process_data_dynamicalfamily(src)

        if self.query_type == 'escaperoutes':
            src = self._process_data_escaperoutes(src)

        if self.query_type == 'all_astinfo':
            src['designations']    = self._process_data_designations(src['designations'])
            src['elements']        = self._process_data_elements(src['elements'])
            src['orbit']           = self._process_data_orbit(src['orbit'])
            src['albedos']         = self._process_data_albedos(src['albedos'])
            src['colors']          = self._process_data_colors(src['colors'])
            src['taxonomies']      = self._process_data_taxonomies(src['taxonomies'])
            src['lightcurves']     = self._process_data_lightcurves(src['lightcurves'])
            src['dynamicalfamily'] = self._process_data_dynamicalfamily(src['dynamicalfamily'])
            src['escaperoutes']    = self._process_data_escaperoutes(src['escaperoutes'])

        # add query uri, if desired
        if self._uri is not None:
            src['query_uri'] = self._uri

        return src

    def _process_data_designations(self, src):
        """
        internal routine to process raw data in OrderedDict format

        """

        if 'designations' in src:
            src = OrderedDict(src['designations'])

        return src

    def _process_data_elements(self, src):
        """
        internal routine to process raw data in OrderedDict format, must
        be able to work recursively

        """

        if 'elements' in src:
            src = OrderedDict(src['elements'])
            src['a']                  = u.Quantity(src['a'], u.au)
            src['aphelion_dist']      = u.Quantity(src['aphelion_dist'], u.au)
            if src['delta_v'] is not None:
                src['delta_v']        = u.Quantity(src['delta_v'], u.km/u.s)
            src['ecc_anomaly']        = u.Quantity(src['ecc_anomaly'], u.deg)
            src['epoch']              = Time(src['epoch'], format='isot', scale='utc')
            src['h']                  = u.Quantity(src['h'], u.mag)
            src['i']                  = u.Quantity(src['m'], u.deg)
            src['long_of_perihelion'] = u.Quantity(src['long_of_perihelion'], u.deg)
            src['m']                  = u.Quantity(src['m'], u.deg)            
            src['moid_earth']         = u.Quantity(src['moid_earth'], u.au)
            src['moid_jupiter']       = u.Quantity(src['moid_jupiter'], u.au)
            src['moid_mars']          = u.Quantity(src['moid_mars'], u.au)
            src['moid_mercury']       = u.Quantity(src['moid_mercury'], u.au)
            src['moid_neptune']       = u.Quantity(src['moid_neptune'], u.au)
            src['moid_saturn']        = u.Quantity(src['moid_saturn'], u.au)
            src['moid_uranus']        = u.Quantity(src['moid_uranus'], u.au)
            src['moid_venus']         = u.Quantity(src['moid_venus'], u.au)
            src['node']               = u.Quantity(src['node'], u.deg)
            src['peri']               = u.Quantity(src['peri'], u.deg)
            src['q']                  = u.Quantity(src['q'], u.au)
            src['r']                  = u.Quantity(src['r'], u.au)
            src['true_anomaly']       = u.Quantity(src['true_anomaly'], u.deg)
            src['x']                  = u.Quantity(src['x'], u.au)
            src['y']                  = u.Quantity(src['y'], u.au)
            src['z']                  = u.Quantity(src['z'], u.au)

        return src

    def _process_data_orbit(self, src):
        """
        internal routine to process raw data in OrderedDict format, must
        be able to work recursively

        """

        if 'orbit' in src:
            src = OrderedDict(src['orbit'])
            src['a1con']            = u.Quantity(src['a1con'], u.au/(u.d ** 2))
            src['a2con']            = u.Quantity(src['a2con'], u.au/(u.d ** 2))
            src['a3con']            = u.Quantity(src['a3con'], u.au/(u.d ** 2))
            src['arc']              = u.Quantity(src['arc'], u.yr)

        return src

    def _process_data_albedos(self, src):
        """
        internal routine to process raw data in Dict format

        """

        if 'albedos' in src:
            src = src['albedos']
            for i in range(len(src)):
                src[i]['diameter'] = u.Quantity(src[i]['diameter'], u.km)
                src[i]['diameter_error_lower'] = u.Quantity(src[i]['diameter_error_lower'], u.km)
                src[i]['diameter_error_upper'] = u.Quantity(src[i]['diameter_error_upper'], u.km)

        return src

    def _process_data_colors(self, src):
        """
        internal routine to process raw data in Dict format

        """

        if 'colors' in src:
            src = src['colors']
            for i in range(len(src)):
                src[i]['jd'] = Time(src[i]['jd'], format='jd', scale='utc')

        return src

    def _process_data_taxonomies(self, src):
        """
        internal routine to process raw data in OrderedDict format, must
        be able to work recursively

        """

        if 'taxonomies' in src:
            src = src['taxonomies']

        return src

    def _process_data_lightcurves(self, src):
        """
        internal routine to process raw data in OrderedDict format, must
        be able to work recursively

        """

        if 'lightcurves' in src:
            src = src['lightcurves']
            for i in range(len(src)):
                if src[i]['amp_max'] is not None:
                    src[i]['amp_max'] = u.Quantity(src[i]['amp_max'], u.mag)
                    if src[i]['amp_min'] is not None:
                        src[i]['amp_min'] = u.Quantity(src[i]['amp_min'], u.mag)
                    src[i]['period']  = u.Quantity(src[i]['period'], u.h)

        return src

    def _process_data_dynamicalfamily(self, src):
        """
        internal routine to process raw data in OrderedDict format, must
        be able to work recursively

        """

        if 'dynamical-family' in src:
            src = src['dynamical-family']

        return src

    def _process_data_escaperoutes(self, src):
        """
        internal routine to process raw data in OrderedDict format, must
        be able to work recursively

        """

        if 'escape-routes' in src:
            src = src['escape-routes']
            for i in range(len(src)):
                src[i]['epoch'] = Time(src[i]['epoch'], format='isot', scale='utc')

        return src

AstInfo = AstInfoClass()

# once your class is done, tests should be written
# See ./tests for examples on this

# Next you should write the docs in astroquery/docs/module_name
# using Sphinx.
