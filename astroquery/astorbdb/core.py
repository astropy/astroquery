# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json
from collections import OrderedDict

from astropy.time import Time
import astropy.units as u

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

    def albedos_async(self, object_name, *,
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
        >>> albedos = AstInfo.albedos('Beagle')  # doctest: +SKIP
        >>> print(albedos)  # doctest: +SKIP
        [{'albedo': 0.065, 'albedo_error_lower': -0.002, ..., 'survey_name': 'Usui et al. (2011)'},
         {'albedo': 0.0625, 'albedo_error_lower': -0.015, ..., 'survey_name': 'Infrared Astronomical Satellite (IRAS)'},
         ...]
        """

        self.query_type = 'albedos'

        response = self._request('GET',
                                 url=self.URL + object_name + '/data/albedos',
                                 timeout=self.TIMEOUT, cache=cache)

        if get_uri:
            self._uri = response.url

        return response

    def colors_async(self, object_name, *,
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
        >>> colors = AstInfo.colors('Beagle')  # doctest: +SKIP
        >>> print(colors)  # doctest: +SKIP
        [{..., 'color': 0.431, 'color_error': 0.035, ..., 'sys_color': 'J-H'},
         {..., 'color': 0.076, 'color_error': 0.041, ..., 'sys_color': 'H-K'},
         ...]
        """

        self.query_type = 'colors'

        response = self._request('GET',
                                 url=self.URL + object_name + '/data/colors',
                                 timeout=self.TIMEOUT, cache=cache)

        if get_uri:
            self._uri = response.url

        return response

    def designations_async(self, object_name, *,
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
        >>> designations = AstInfo.designations('Beagle')  # doctest: +SKIP
        >>> print(designations)  # doctest: +SKIP
        {'alternate_designations': ['1954 HJ', ...], 'name': 'Beagle', 'number': 656, ...}
        """

        self.query_type = 'designations'

        response = self._request('GET',
                                 url=self.URL + object_name + '/designations',
                                 timeout=self.TIMEOUT, cache=cache)

        if get_uri:
            self._uri = response.url

        return response

    def dynamical_family_async(self, object_name, *,
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
        >>> dynamical_family = AstInfo.dynamical_family('Beagle')  # doctest: +SKIP
        >>> print(dynamical_family)  # doctest: +SKIP
        [{'citation_bibcode': '2015PDSS..234.....N', ..., 'family': 'Themis', ...},
         {'citation_bibcode': '2015PDSS..234.....N', ..., 'family': 'Beagle', ...}]
        """

        self.query_type = 'dynamical_family'

        response = self._request('GET',
                                 url=self.URL + object_name + '/data/dynamical-family',
                                 timeout=self.TIMEOUT, cache=cache)

        if get_uri:
            self._uri = response.url

        return response

    def elements_async(self, object_name, *,
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
        >>> elements = AstInfo.elements('Beagle')  # doctest: +SKIP
        >>> print(elements)  # doctest: +SKIP
        {'a': <Quantity 3.15597543 AU>, 'aphelion_dist': <Quantity 3.57009832 AU>, ...}
        """

        self.query_type = 'elements'

        response = self._request('GET',
                                 url=self.URL + object_name + '/elements',
                                 timeout=self.TIMEOUT, cache=cache)

        if get_uri:
            self._uri = response.url

        return response

    def escape_routes_async(self, object_name, *,
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
        >>> escape_routes = AstInfo.escape_routes('3552')  # doctest: +SKIP
        >>> print(escape_routes)  # doctest: +SKIP
        [{'citation_bibcode': '2018Icar..312..181G', ..., 'dp21_complex': 0.03695, 'dp31_complex': 0.00105, ...}]
        """

        self.query_type = 'escape_routes'

        response = self._request('GET',
                                 url=self.URL + object_name + '/data/escape-routes',
                                 timeout=self.TIMEOUT, cache=cache)

        if get_uri:
            self._uri = response.url

        return response

    def lightcurves_async(self, object_name, *,
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
        >>> lightcurves = AstInfo.lightcurves('Beagle')  # doctest: +SKIP
        >>> print(lightcurves)  # doctest: +SKIP
        [{..., 'amp_max': <Quantity 1.2 mag>, 'amp_min': <Quantity 0.57 mag>, ..., 'period': <Quantity 7.035 h>, ...}]
        """

        self.query_type = 'lightcurves'

        response = self._request('GET',
                                 url=self.URL + object_name + '/data/lightcurves',
                                 timeout=self.TIMEOUT, cache=cache)

        if get_uri:
            self._uri = response.url

        return response

    def orbit_async(self, object_name, *,
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
        res : A dictionary holding available orbit fitting data

        Examples
        --------
        >>> from astroquery.astorbdb import AstInfo
        >>> orbit = AstInfo.orbit('Beagle')  # doctest: +SKIP
        >>> print(orbit)  # doctest: +SKIP
        {'a1con': <Quantity 0. AU / d2>, 'a2con': <Quantity 0. AU / d2>, ...}
        """

        self.query_type = 'orbit'

        response = self._request('GET',
                                 url=self.URL + object_name + '/orbit',
                                 timeout=self.TIMEOUT, cache=cache)

        if get_uri:
            self._uri = response.url

        return response

    def taxonomies_async(self, object_name, *,
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
        >>> taxonomies = AstInfo.taxonomies('Beagle')  # doctest: +SKIP
        >>> print(taxonomies)  # doctest: +SKIP
        [{'citation_bibcode': '2011PDSS..145.....H', ..., 'survey_name': 'Carvano et al. (2010)', 'taxonomy': 'C', ...},
         {'citation_bibcode': '2013Icar..226..723D', ..., 'survey_name': 'DeMeo et al. (2013)', 'taxonomy': 'C', ...}]
        """

        self.query_type = 'taxonomies'

        response = self._request('GET',
                                 url=self.URL + object_name + '/data/taxonomies',
                                 timeout=self.TIMEOUT, cache=cache)

        if get_uri:
            self._uri = response.url

        return response

    def lightcurves_async(self, object_name, *,
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
        >>> lightcurves = AstInfo.lightcurves('Beagle')  # doctest: +SKIP
        >>> print(lightcurves)  # doctest: +SKIP
        [{..., 'amp_max': <Quantity 1.2 mag>, 'amp_min': <Quantity 0.57 mag>, ..., 'period': <Quantity 7.035 h>, ...}]
        """

        self.query_type = 'lightcurves'

        response = self._request('GET',
                                 url=self.URL + object_name + '/data/lightcurves',
                                 timeout=self.TIMEOUT, cache=cache)

        if get_uri:
            self._uri = response.url

        return response

    def orbit_async(self, object_name, *,
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
        res : A dictionary holding available orbit fitting data

        Examples
        --------
        >>> from astroquery.astorbdb import AstInfo
        >>> orbit = AstInfo.orbit('Beagle')  # doctest: +SKIP
        >>> print(orbit)  # doctest: +SKIP
        {'a1con': <Quantity 0. AU / d2>, 'a2con': <Quantity 0. AU / d2>, ...}
        """

        self.query_type = 'orbit'

        response = self._request('GET',
                                 url=self.URL + object_name + '/orbit',
                                 timeout=self.TIMEOUT, cache=cache)

        if get_uri:
            self._uri = response.url

        return response

    def taxonomies_async(self, object_name, *,
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
        >>> taxonomies = AstInfo.taxonomies('Beagle')  # doctest: +SKIP
        >>> print(taxonomies)  # doctest: +SKIP
        [{'citation_bibcode': '2011PDSS..145.....H', ..., 'survey_name': 'Carvano et al. (2010)', 'taxonomy': 'C', ...},
         {'citation_bibcode': '2013Icar..226..723D', ..., 'survey_name': 'DeMeo et al. (2013)', 'taxonomy': 'C', ...}]
        """

        self.query_type = 'taxonomies'

        response = self._request('GET',
                                 url=self.URL + object_name + '/data/taxonomies',
                                 timeout=self.TIMEOUT, cache=cache)

        if get_uri:
            self._uri = response.url

        return response

    def all_astinfo_async(self, object_name, *,
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
        >>> all_astinfo = AstInfo.all_astinfo('Beagle')  # doctest: +SKIP
        >>> print(all_astinfo)  # doctest: +SKIP
        OrderedDict({
        'albedos': [{'albedo': 0.065, ..., 'survey_name': 'Usui et al. (2011)'},
                    {'albedo': 0.0625, ..., 'survey_name': 'Infrared Astronomical Satellite (IRAS)'},
                    ...],
        'colors': [{..., 'color': 0.431, 'color_error': 0.035, ..., 'sys_color': 'J-H'},
                   {..., 'color': 0.076, 'color_error': 0.041, ..., 'sys_color': 'H-K'},
                   ...],
        'designations': {'alternate_designations': ['1954 HJ', ...], 'name': 'Beagle', ...},
        'dynamical_family': [{'citation_bibcode': '2015PDSS..234.....N', ..., 'family': 'Themis', ...},
                             {'citation_bibcode': '2015PDSS..234.....N', ..., 'family': 'Beagle', ...}],
        'elements': {'a': <Quantity 3.15597543 AU>, 'aphelion_dist': <Quantity 3.57009832 AU>, ...},
        'escape_routes': [],
        'lightcurves': [{..., 'amp_max': <Quantity 1.2 mag>, ..., 'period': <Quantity 7.035 h>, ...}],
        'orbit': {'a1con': <Quantity 0. AU / d2>, 'a2con': <Quantity 0. AU / d2>, ...},
        'taxonomies': [{..., 'survey_name': 'Carvano et al. (2010)', 'taxonomy': 'C', ...},
                       {..., 'survey_name': 'DeMeo et al. (2013)', 'taxonomy': 'C', ...}]
        })
        """

        self.query_type = 'all_astinfo'

        response = {}

        response['albedos'] = self._request('GET',
                                            url=self.URL + object_name + '/data/albedos',
                                            timeout=self.TIMEOUT, cache=cache)

        response['colors'] = self._request('GET',
                                           url=self.URL + object_name + '/data/colors',
                                           timeout=self.TIMEOUT, cache=cache)

        response['designations'] = self._request('GET',
                                                 url=self.URL + object_name + '/designations',
                                                 timeout=self.TIMEOUT, cache=cache)

        response['dynamical_family'] = self._request('GET',
                                                    url=self.URL + object_name + '/data/dynamical-family',
                                                    timeout=self.TIMEOUT, cache=cache)

        response['elements'] = self._request('GET',
                                             url=self.URL + object_name + '/elements',
                                             timeout=self.TIMEOUT, cache=cache)

        response['escape_routes'] = self._request('GET',
                                                 url=self.URL + object_name + '/data/escape-routes',
                                                 timeout=self.TIMEOUT, cache=cache)

        response['lightcurves'] = self._request('GET',
                                                url=self.URL + object_name + '/data/lightcurves',
                                                timeout=self.TIMEOUT, cache=cache)

        response['orbit'] = self._request('GET',
                                          url=self.URL + object_name + '/orbit',
                                          timeout=self.TIMEOUT, cache=cache)

        response['taxonomies'] = self._request('GET',
                                               url=self.URL + object_name + '/data/taxonomies',
                                               timeout=self.TIMEOUT, cache=cache)

        if get_uri:
            self._uri = {'albedos': response['albedos'].url,
                         'colors': response['colors'].url,
                         'designations': response['designations'].url,
                         'dynamical_family': response['dynamical_family'].url,
                         'elements': response['elements'].url,
                         'escape_routes': response['escape_routes'].url,
                         'lightcurves': response['lightcurves'].url,
                         'orbit': response['orbit'].url,
                         'taxonomies': response['taxonomies'].url
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
            if isinstance(response,dict):
                src = OrderedDict()
                for key in response:
                    src[key] = OrderedDict(json.loads(response[key].text))
            else:
                src = OrderedDict(json.loads(response.text))
        except ValueError:
            raise ValueError('Server response not readable.')

        if self.query_type == 'albedos':
            src = self._process_data_albedos(src)

        elif self.query_type == 'colors':
            src = self._process_data_colors(src)

        elif self.query_type == 'designations':
            src = self._process_data_designations(src)

        elif self.query_type == 'dynamical_family':
            src = self._process_data_dynamical_family(src)

        elif self.query_type == 'elements':
            src = self._process_data_elements(src)

        elif self.query_type == 'escape_routes':
            src = self._process_data_escape_routes(src)

        elif self.query_type == 'lightcurves':
            src = self._process_data_lightcurves(src)

        elif self.query_type == 'orbit':
            src = self._process_data_orbit(src)

        elif self.query_type == 'taxonomies':
            src = self._process_data_taxonomies(src)

        elif self.query_type == 'all_astinfo':
            src['albedos'] = self._process_data_albedos(src['albedos'])
            src['colors'] = self._process_data_colors(src['colors'])
            src['designations'] = self._process_data_designations(src['designations'])
            src['dynamical_family'] = self._process_data_dynamical_family(src['dynamical_family'])
            src['elements'] = self._process_data_elements(src['elements'])
            src['escape_routes'] = self._process_data_escape_routes(src['escape_routes'])
            src['lightcurves'] = self._process_data_lightcurves(src['lightcurves'])
            src['orbit'] = self._process_data_orbit(src['orbit'])
            src['taxonomies'] = self._process_data_taxonomies(src['taxonomies'])

        else:
            raise ValueError('Query type not recognized.')

        # add query uri, if desired
        if self._uri is not None:
            src['query_uri'] = self._uri

        return src

    def _process_data_albedos(self, src):
        """
        internal routine to process raw data in Dict format

        """

        if 'albedos' in src:
            src = src['albedos']
            for i in range(len(src)):
                if src[i]['diameter'] is not None:
                    src[i]['diameter'] = u.Quantity(src[i]['diameter'], u.km)
                if src[i]['diameter_error_lower'] is not None:
                    src[i]['diameter_error_lower'] = u.Quantity(src[i]['diameter_error_lower'], u.km)
                if src[i]['diameter_error_upper'] is not None:
                    src[i]['diameter_error_upper'] = u.Quantity(src[i]['diameter_error_upper'], u.km)

        return src

    def _process_data_colors(self, src):
        """
        internal routine to process raw data in Dict format

        """

        if 'colors' in src:
            src = src['colors']
            for i in range(len(src)):
                if src[i]['jd'] is not None:
                    src[i]['jd'] = Time(src[i]['jd'], format='jd', scale='utc')

        return src

    def _process_data_designations(self, src):
        """
        internal routine to process raw data in Dict format

        """

        if 'designations' in src:
            src = src['designations']

        return src

    def _process_data_dynamical_family(self, src):
        """
        internal routine to process raw data in Dict format, must
        be able to work recursively

        """

        if 'dynamical-family' in src:
            src = src['dynamical-family']

        return src

    def _process_data_elements(self, src):
        """
        internal routine to process raw data in Dict format, must
        be able to work recursively

        """

        if 'elements' in src:
            src = src['elements']
            if src['a'] is not None:
                src['a'] = u.Quantity(src['a'], u.au)
            if src['aphelion_dist'] is not None:
                src['aphelion_dist'] = u.Quantity(src['aphelion_dist'], u.au)
            if src['delta_v'] is not None:
                src['delta_v'] = u.Quantity(src['delta_v'], u.km/u.s)
            if src['ecc_anomaly'] is not None:
                src['ecc_anomaly'] = u.Quantity(src['ecc_anomaly'], u.deg)
            if src['epoch'] is not None:
                src['epoch'] = Time(src['epoch'], format='isot', scale='utc')
            if src['h'] is not None:
                src['h'] = u.Quantity(src['h'], u.mag)
            if src['i'] is not None:
                src['i'] = u.Quantity(src['m'], u.deg)
            if src['long_of_perihelion'] is not None:
                src['long_of_perihelion'] = u.Quantity(src['long_of_perihelion'], u.deg)
            if src['m'] is not None:
                src['m'] = u.Quantity(src['m'], u.deg)
            if src['moid_earth'] is not None:
                src['moid_earth'] = u.Quantity(src['moid_earth'], u.au)
            if src['moid_jupiter'] is not None:
                src['moid_jupiter'] = u.Quantity(src['moid_jupiter'], u.au)
            if src['moid_mars'] is not None:
                src['moid_mars'] = u.Quantity(src['moid_mars'], u.au)
            if src['moid_mercury'] is not None:
                src['moid_mercury'] = u.Quantity(src['moid_mercury'], u.au)
            if src['moid_neptune'] is not None:
                src['moid_neptune'] = u.Quantity(src['moid_neptune'], u.au)
            if src['moid_saturn'] is not None:
                src['moid_saturn'] = u.Quantity(src['moid_saturn'], u.au)
            if src['moid_uranus'] is not None:
                src['moid_uranus'] = u.Quantity(src['moid_uranus'], u.au)
            if src['moid_venus'] is not None:
                src['moid_venus'] = u.Quantity(src['moid_venus'], u.au)
            if src['node'] is not None:
                src['node'] = u.Quantity(src['node'], u.deg)
            if src['peri'] is not None:
                src['peri'] = u.Quantity(src['peri'], u.deg)
            if src['q'] is not None:
                src['q'] = u.Quantity(src['q'], u.au)
            if src['r'] is not None:
                src['r'] = u.Quantity(src['r'], u.au)
            if src['true_anomaly'] is not None:
                src['true_anomaly'] = u.Quantity(src['true_anomaly'], u.deg)
            if src['x'] is not None:
                src['x'] = u.Quantity(src['x'], u.au)
            if src['y'] is not None:
                src['y'] = u.Quantity(src['y'], u.au)
            if src['z'] is not None:
                src['z'] = u.Quantity(src['z'], u.au)

        return src

    def _process_data_escape_routes(self, src):
        """
        internal routine to process raw data in Dict format, must
        be able to work recursively

        """

        if 'escape-routes' in src:
            src = src['escape-routes']
            if src is not None:
                for i in range(len(src)):
                    if src[i]['epoch'] is not None:
                        src[i]['epoch'] = Time(src[i]['epoch'], format='isot', scale='utc')

        return src

    def _process_data_lightcurves(self, src):
        """
        internal routine to process raw data in Dict format, must
        be able to work recursively

        """

        if 'lightcurves' in src:
            src = src['lightcurves']
            for i in range(len(src)):
                if src[i]['amp_max'] is not None:
                    src[i]['amp_max'] = u.Quantity(src[i]['amp_max'], u.mag)
                if src[i]['amp_min'] is not None:
                    src[i]['amp_min'] = u.Quantity(src[i]['amp_min'], u.mag)
                if src[i]['period'] is not None:
                    src[i]['period'] = u.Quantity(src[i]['period'], u.h)

        return src

    def _process_data_orbit(self, src):
        """
        internal routine to process raw data in Dict format, must
        be able to work recursively

        """

        if 'orbit' in src:
            src = src['orbit']
            if src['a1con'] is not None:
                src['a1con'] = u.Quantity(src['a1con'], u.au/(u.d ** 2))
            if src['a2con'] is not None:
                src['a2con'] = u.Quantity(src['a2con'], u.au/(u.d ** 2))
            if src['a3con'] is not None:
                src['a3con'] = u.Quantity(src['a3con'], u.au/(u.d ** 2))
            if src['arc'] is not None:
                src['arc'] = u.Quantity(src['arc'], u.yr)

        return src

    def _process_data_taxonomies(self, src):
        """
        internal routine to process raw data in Dict format, must
        be able to work recursively

        """

        if 'taxonomies' in src:
            src = src['taxonomies']

        return src


AstInfo = AstInfoClass()

# once your class is done, tests should be written
# See ./tests for examples on this

# Next you should write the docs in astroquery/docs/module_name
# using Sphinx.
