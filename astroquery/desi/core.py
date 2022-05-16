# Licensed under a 3-clause BSD style license - see LICENSE.rst
import urllib.error
import requests
import warnings

import pyvo as vo
import numpy as np
import astropy.coordinates as coord

from astroquery.exceptions import NoResultsWarning
from astroquery.query import BaseQuery
from astroquery.utils import commons, async_to_sync
from astroquery.desi import conf

__all__ = ['DESILegacySurvey', 'DESILegacySurveyClass']


class DESILegacySurveyClass(BaseQuery):

    def query_region(self, coordinates, radius, *, data_release=9):
        """
        Queries a region around the specified coordinates.

        Parameters
        ----------
        coordinates : `astropy.coordinates`
            coordinates around which to query.
        radius : `astropy.units.Quantity`
            the radius of the cone search.
        data_release: int
            the data release of the LegacySurvey to use.

        Returns
        -------
        response : `astropy.table.Table`
        """

        tap_service = vo.dal.TAPService(conf.tap_service_url)
        coordinates_transformed = coordinates.transform_to(coord.ICRS)

        qstr = (f"SELECT all * FROM ls_dr{data_release}.tractor WHERE "
               f"dec>{coordinates_transformed.dec.deg - radius.deg} and "
               f"dec<{coordinates_transformed.dec.deg + radius.deg} and "
               f"ra>{coordinates_transformed.ra.deg - radius.deg / np.cos(coordinates_transformed.dec.deg * np.pi / 180.)} and "
               f"ra<{coordinates_transformed.ra.deg + radius.deg / np.cos(coordinates_transformed.dec.deg * np.pi / 180)}")

        tap_result = tap_service.run_sync(qstr)
        tap_result = tap_result.to_table()
        # filter out duplicated lines from the table
        mask = tap_result['type'] != 'D'
        filtered_table = tap_result[mask]

        return filtered_table

    def get_images(self, position, pixels, radius, *, data_release=9, show_progress=True, image_band='g'):
        """
        Downloads the images for a certain region of interest.

        Parameters
        -------
        position: `astropy.coordinates`.
            coordinates around which we define our region of interest.
        radius: `astropy.units.Quantity`.
            the radius of the cone search.
        data_release: int
            the data release of the LegacySurvey to use.

        Returns
        -------
        list: A list of `astropy.io.fits.HDUList` objects.
        """

        position_transformed = position.transform_to(coord.ICRS)

        image_size_arcsec = radius.arcsec
        pixsize = 2 * image_size_arcsec / pixels

        image_url = (f"{conf.legacysurvey_service_url}?"
                    f"ra={position_transformed.ra.deg}&"
                    f"dec={position_transformed.dec.deg}&"
                    f"size={pixels}&"
                    f"layer=ls-dr{data_release}&"
                    f"pixscale={pixsize}&"
                    f"bands={image_band}")

        file_container = commons.FileContainer(image_url, encoding='binary', show_progress=show_progress)

        try:
            fits_file = file_container.get_fits()
        except (requests.exceptions.HTTPError, urllib.error.HTTPError) as e:
            fits_file = None
            warnings.warn(f"{str(e)} - Problem retrieving the file at the url: {image_url}", NoResultsWarning)

        return [fits_file]


DESILegacySurvey = DESILegacySurveyClass()
