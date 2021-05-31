# Licensed under a 3-clause BSD style license - see LICENSE.rst
import urllib.error
import requests

import pyvo as vo
import numpy as np

from astroquery.exceptions import NoResultsWarning
from astroquery.query import BaseQuery
from astroquery.utils import commons, async_to_sync

from . import conf


__all__ = ['DESILegacySurvey', 'DESILegacySurveyClass']


@async_to_sync
class DESILegacySurveyClass(BaseQuery):
    URL = conf.server
    TIMEOUT = conf.timeout

    def query_region(self, coordinates, radius, data_release=9):
        """
        Queries a region around the specified coordinates.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            coordinates around which to query
        radius : str or `astropy.units.Quantity`.
            the radius of the cone search

        Returns
        -------
        response : `astropy.table.Table`
        """

        url = 'https://datalab.noirlab.edu/tap'
        tap_service = vo.dal.TAPService(url)
        qstr = "SELECT all * FROM ls_dr" + str(data_release) + ".tractor WHERE dec>" + str(coordinates.dec.deg - radius.deg) + " and dec<" + str(
            coordinates.dec.deg + radius.deg) + " and ra>" + str(coordinates.ra.deg - radius.deg / np.cos(coordinates.dec.deg * np.pi / 180.)) + " and ra<" + str(
            coordinates.ra.deg + radius.deg / np.cos(coordinates.dec.deg * np.pi / 180))

        tap_result = tap_service.run_sync(qstr)
        tap_result = tap_result.to_table()
        # filter out duplicated lines from the table
        mask = tap_result['type'] != 'D'
        filtered_table = tap_result[mask]

        return filtered_table

    def get_images(self, position, data_release=9, pixels=None, radius=None, show_progress=True, image_band='g'):
        """
        Returns
        -------
        A list of `astropy.io.fits.HDUList` objects.
        """

        image_size_arcsec = radius.arcsec
        pixsize = 2 * image_size_arcsec / pixels

        image_url = 'https://www.legacysurvey.org/viewer/fits-cutout?ra=' + str(position.ra.deg) + '&dec=' + str(position.dec.deg) + '&size=' + str(
            pixels) + '&layer=ls-dr' + str(data_release) + '&pixscale=' + str(pixsize) + '&bands=' + image_band

        file_container = commons.FileContainer(image_url, encoding='binary', show_progress=show_progress)

        try:
            fits_file = file_container.get_fits()
        except (requests.exceptions.HTTPError, urllib.error.HTTPError) as e:
            # TODO not sure this is the most suitable exception
            raise NoResultsWarning(f"{str(e)} - Problem retrieving the file at the url: {str(image_url)}")

        return [fits_file]


DESILegacySurvey = DESILegacySurveyClass()
