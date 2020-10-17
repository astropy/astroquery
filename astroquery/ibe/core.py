# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
IBE
===

API from

 http://irsa.ipac.caltech.edu/ibe/
"""


import os
import webbrowser
from bs4 import BeautifulSoup

import astropy.coordinates as coord
from astropy.table import Table
import six

from ..exceptions import InvalidQueryError
from ..query import BaseQuery
from ..utils import commons
from . import conf

__all__ = ['Ibe', 'IbeClass']


class IbeClass(BaseQuery):
    URL = conf.server
    MISSION = conf.mission
    DATASET = conf.dataset
    TABLE = conf.table
    TIMEOUT = conf.timeout

    def query_region(
            self, coordinate=None, where=None, mission=None, dataset=None,
            table=None, columns=None, width=None, height=None,
            intersect='OVERLAPS', most_centered=False):
        """
        For certain missions, this function can be used to search for image and
        catalog files based on a point, a box (bounded by great circles) and/or
        an SQL-like ``where`` clause.

        If ``coordinates`` is specified, then the optional ``width`` and
        ``height`` arguments control the width and height of the search
        box. If neither ``width`` nor ``height`` are provided, then the
        search area is a point. If only one of ``width`` or ``height`` are
        specified, then the search area is a square with that side length
        centered at the coordinate.

        Parameters
        ----------
        coordinate : str, `astropy.coordinates` object
            Gives the position of the center of the box if performing a box
            search. If it is a string, then it must be a valid argument to
            `~astropy.coordinates.SkyCoord`. Required if ``where`` is absent.
        where : str
            SQL-like query string. Required if ``coordinates`` is absent.
        mission : str
            The mission to be used (if not the default mission).
        dataset : str
            The dataset to be used (if not the default dataset).
        table : str
            The table to be queried (if not the default table).
        columns : str, list
            A space-separated string or a list of strings of the names of the
            columns to return.
        width : str or `~astropy.units.Quantity` object
            Width of the search box if ``coordinates`` is present.

            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `astropy.units`
            may also be used.
        height : str, `~astropy.units.Quantity` object
            Height of the search box if ``coordinates`` is present.

            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `astropy.units`
            may also be used.
        intersect : ``'COVERS'``, ``'ENCLOSED'``, ``'CENTER'``, ``'OVERLAPS'``
            Spatial relationship between search box and image footprint.

            ``'COVERS'``: X must completely contain S. Equivalent to
            ``'CENTER'`` and ``'OVERLAPS'`` if S is a point.

            ``'ENCLOSED'``: S must completely contain X. If S is a point, the
            query will always return an empty image table.

            ``'CENTER'``: X must contain the center of S. If S is a point, this
            is equivalent to ``'COVERS'`` and ``'OVERLAPS'``.

            ``'OVERLAPS'``: The intersection of S and X is non-empty. If S is a
            point, this is equivalent to ``'CENTER'`` and ``'COVERS'``.
        most_centered : bool
            If True, then only the most centered image is returned.

        Returns
        -------
        table : `~astropy.table.Table`
            A table containing the results of the query
        """
        response = self.query_region_async(
            coordinate=coordinate, where=where, mission=mission,
            dataset=dataset, table=table, columns=columns, width=width,
            height=height, intersect=intersect, most_centered=most_centered)

        # Raise exception, if request failed
        response.raise_for_status()

        return Table.read(response.text, format='ipac', guess=False)

    def query_region_sia(self, coordinate=None, mission=None,
                         dataset=None, table=None, width=None,
                         height=None, intersect='OVERLAPS',
                         most_centered=False):
        """
        Query using simple image access protocol.  See ``query_region`` for
        details.  The returned table will include a list of URLs.
        """
        response = self.query_region_async(
            coordinate=coordinate, mission=mission,
            dataset=dataset, table=table, width=width,
            height=height, intersect=intersect, most_centered=most_centered,
            action='sia')

        # Raise exception, if request failed
        response.raise_for_status()

        return commons.parse_votable(
            response.text).get_first_table().to_table()

    def query_region_async(
            self, coordinate=None, where=None, mission=None, dataset=None,
            table=None, columns=None, width=None, height=None,
            action='search',
            intersect='OVERLAPS', most_centered=False):
        """
        For certain missions, this function can be used to search for image and
        catalog files based on a point, a box (bounded by great circles) and/or
        an SQL-like ``where`` clause.

        If ``coordinates`` is specified, then the optional ``width`` and
        ``height`` arguments control the width and height of the search
        box. If neither ``width`` nor ``height`` are provided, then the
        search area is a point. If only one of ``width`` or ``height`` are
        specified, then the search area is a square with that side length
        centered at the coordinate.

        Parameters
        ----------
        coordinate : str, `astropy.coordinates` object
            Gives the position of the center of the box if performing a box
            search. If it is a string, then it must be a valid argument to
            `~astropy.coordinates.SkyCoord`. Required if ``where`` is absent.
        where : str
            SQL-like query string. Required if ``coordinates`` is absent.
        mission : str
            The mission to be used (if not the default mission).
        dataset : str
            The dataset to be used (if not the default dataset).
        table : str
            The table to be queried (if not the default table).
        columns : str, list
            A space-separated string or a list of strings of the names of the
            columns to return.
        width : str or `~astropy.units.Quantity` object
            Width of the search box if ``coordinates`` is present.

            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `astropy.units`
            may also be used.
        height : str, `~astropy.units.Quantity` object
            Height of the search box if ``coordinates`` is present.

            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `astropy.units`
            may also be used.
        intersect : ``'COVERS'``, ``'ENCLOSED'``, ``'CENTER'``, ``'OVERLAPS'``
            Spatial relationship between search box and image footprint.

            ``'COVERS'``: X must completely contain S. Equivalent to
            ``'CENTER'`` and ``'OVERLAPS'`` if S is a point.

            ``'ENCLOSED'``: S must completely contain X. If S is a point, the
            query will always return an empty image table.

            ``'CENTER'``: X must contain the center of S. If S is a point, this
            is equivalent to ``'COVERS'`` and ``'OVERLAPS'``.

            ``'OVERLAPS'``: The intersection of S and X is non-empty. If S is a
            point, this is equivalent to ``'CENTER'`` and ``'COVERS'``.
        most_centered : bool
            If True, then only the most centered image is returned.
        action : ``'search'``, ``'data'``, or ``'sia'``
            The action to perform at the server.  The default is ``'search'``,
            which returns a table of the available data.  ``'data'`` requires
            advanced path construction that is not yet supported. ``'sia'``
            provides access to the 'simple image access' IVOA protocol

        Returns
        -------
        response : `~requests.Response`
            The HTTP response returned from the service
        """

        if coordinate is None and where is None:
            raise InvalidQueryError(
                'At least one of `coordinate` or `where` is required')

        intersect = intersect.upper()
        if intersect not in ('COVERS', 'ENCLOSED', 'CENTER', 'OVERLAPS'):
            raise InvalidQueryError(
                "Invalid value for `intersects` " +
                "(must be 'COVERS', 'ENCLOSED', 'CENTER', or 'OVERLAPS')")

        if action not in ('sia', 'data', 'search'):
            raise InvalidQueryError("Valid actions are: sia, data, search.")
        if action == 'data':
            raise NotImplementedError(
                "The action='data' option is a placeholder for future " +
                "functionality.")

        args = {
            'INTERSECT': intersect
        }

        # Note: in IBE, if 'mcen' argument is present, it is true.
        # If absent, it is false.
        if most_centered:
            args['mcen'] = '1'

        if coordinate is not None:
            c = commons.parse_coordinates(coordinate).transform_to(coord.ICRS)
            args['POS'] = '{0},{1}'.format(c.ra.deg, c.dec.deg)
            if width and height:
                args['SIZE'] = '{0},{1}'.format(
                    coord.Angle(width).value,
                    coord.Angle(height).value)
            elif width or height:
                args['SIZE'] = str(coord.Angle(width or height).value)

        if where:
            args['where'] = where

        if columns:
            if isinstance(columns, six.string_types):
                columns = columns.split()
            args['columns'] = ','.join(columns)

        url = "{URL}{action}/{mission}/{dataset}/{table}".format(
                URL=self.URL,
                action=action,
                mission=mission or self.MISSION,
                dataset=dataset or self.DATASET,
                table=table or self.TABLE)

        return self._request('GET', url, args, timeout=self.TIMEOUT)

    def list_missions(self, cache=True):
        """
        Return a list of the available missions

        Parameters
        ----------
        cache : bool
            Cache the query result
        """
        if hasattr(self, '_missions') and cache:
            # extra level caching to avoid redoing the BeautifulSoup parsing
            # unnecessarily
            missions = self._missions
        else:
            url = self.URL + "search/"
            response = self._request('GET', url, timeout=self.TIMEOUT,
                                     cache=cache)

            root = BeautifulSoup(response.text)
            links = root.findAll('a')
            missions = [os.path.basename(a.attrs['href']) for a in links]
            self._missions = missions

        return missions

    def list_datasets(self, mission=None, cache=True):
        """
        For a given mission, list the available datasets

        Parameters
        ----------
        mission : str
            A mission name.  Must be one of the valid missions from
            `~astroquery.ibe.IbeClass.list_missions`.  Defaults to the
            configured Mission
        cache : bool
            Cache the query result

        Returns
        -------
        datasets : list
            A list of dataset names
        """
        if mission is None:
            mission = self.MISSION
        if mission not in self.list_missions():
            raise ValueError("Invalid mission specified: {0}."
                             "Must be one of: {1}"
                             .format(mission, self.list_missions()))

        url = "{URL}search/{mission}/".format(URL=self.URL, mission=mission)
        response = self._request('GET', url, timeout=self.TIMEOUT,
                                 cache=cache)

        root = BeautifulSoup(response.text)
        links = root.findAll('a')
        datasets = [a.text for a in links
                    if a.attrs['href'].count('/') >= 4  # shown as '..'; ignore
                    ]

        return datasets

    def list_tables(self, mission=None, dataset=None, cache=True):
        """
        For a given mission and dataset (see
        `~.astroquery.ibe.IbeClass.list_missions`,
        `~astroquery.ibe.IbeClass.list_datasets`), return the list of valid
        table names to query.

        Parameters
        ----------
        mission : str
            A mission name.  Must be one of the valid missions from
            `~.astroquery.ibe.IbeClass.list_missions`.  Defaults to the
            configured Mission
        dataset : str
            A dataset name.  Must be one of the valid dataset from
            ``list_datsets(mission)``.  Defaults to the configured Dataset
        cache : bool
            Cache the query result

        Returns
        -------
        tables : list
            A list of table names
        """
        if mission is None:
            mission = self.MISSION
        if dataset is None:
            dataset = self.DATASET

        if mission not in self.list_missions():
            raise ValueError("Invalid mission specified: {0}."
                             "Must be one of: {1}"
                             .format(mission, self.list_missions()))

        if dataset not in self.list_datasets(mission, cache=cache):
            raise ValueError("Invalid dataset {0} specified for mission {1}."
                             "Must be one of: {2}"
                             .format(dataset, mission,
                                     self.list_datasets(mission, cache=True)))

        url = "{URL}search/{mission}/{dataset}/".format(URL=self.URL,
                                                        mission=mission,
                                                        dataset=dataset)
        response = self._request('GET', url, timeout=self.TIMEOUT,
                                 cache=cache)

        root = BeautifulSoup(response.text)
        return [tr.find('td').string for tr in root.findAll('tr')[1:]]

    # Unfortunately, the URL construction for each data set is different, and
    # they're not obviously accessible via API
    # def get_data(self, **kwargs):
    #    return self.query_region_async(retrieve_data=True, **kwargs)

    def show_docs(self, mission=None, dataset=None, table=None):
        """
        Open the documentation for a given table in a web browser.

        Parameters
        ----------
        mission : str
            The mission to be used (if not the default mission).
        dataset : str
            The dataset to be used (if not the default dataset).
        table : str
            The table to be queried (if not the default table).
        """

        url = "{URL}docs/{mission}/{dataset}/{table}".format(
                URL=self.URL,
                mission=mission or self.MISSION,
                dataset=dataset or self.DATASET,
                table=table or self.TABLE)

        return webbrowser.open(url)

    def get_columns(self, mission=None, dataset=None, table=None):
        """
        Get the schema for a given table.

        Parameters
        ----------
        mission : str
            The mission to be used (if not the default mission).
        dataset : str
            The dataset to be used (if not the default dataset).
        table : str
            The table to be queried (if not the default table).

        Returns
        -------
        table : `~astropy.table.Table`
            A table containing a description of the columns
        """

        url = "{URL}search/{mission}/{dataset}/{table}".format(
                URL=self.URL,
                mission=mission or self.MISSION,
                dataset=dataset or self.DATASET,
                table=table or self.TABLE)

        response = self._request(
            'GET', url, {'FORMAT': 'METADATA'}, timeout=self.TIMEOUT)

        # Raise exception, if request failed
        response.raise_for_status()

        return Table.read(response.text, format='ipac', guess=False)


Ibe = IbeClass()
