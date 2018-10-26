# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
MAST Tesscut
============

Cutout queries on TESS FFIs.

"""

from __future__ import print_function, division

import warnings
import time
import json
import zipfile
import os

import numpy as np

import astropy.units as u
import astropy.coordinates as coord

from astropy.table import Table

from ..query import BaseQuery
from ..utils import commons
from ..exceptions import NoResultsWarning, InvalidQueryError

from . import conf

__all__ = ["TesscutClass", "Tesscut"]


class TesscutClass(BaseQuery):
    """
    MAST TESS FFI cutout query class.

    Class for accessing TESS full-frame image cutouts.
    """

    def __init__(self):

        super(TesscutClass, self).__init__()

        self._TESSCUT_URL = conf.server + "/tesscut/api/v0.1/"

    def _tesscut_livecheck(self):
        """
        Temporary function to check if the tesscut service is live. 
        We'll remove this function once tesscut is released.
        """

        response = self._request("GET", conf.server + "/tesscut/")
        if not response.status_code == 200:
            raise Exception("The TESSCut service hasn't been released yet.\n" +
                            "Try again Soon!\n( More info at https://archive.stsci.edu/tess/ )")

    def get_sectors(self, coordinates, radius=0.2*u.deg):
        """
        Get a list of the TESS data sectors whose footprints intersect 
        with the given search area.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object.
        radius : str, float, or `~astropy.units.Quantity` object, optional
            Default 0.2 degrees.
            If supplied as a float degrees is the assumed unit.
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used.

        Returns
        -------
        response : `~astropy.table.Table`
            Sector/camera/chip information for given coordinates/raduis.
        """

        # Check if tesscut is live before proceeding.
        self._tesscut_livecheck()

        # Put coordinates and radius into consistant format
        coordinates = commons.parse_coordinates(coordinates)

        # if radius is just a number we assume degrees
        if isinstance(radius, (int, float)):
            radius = radius * u.deg
        radius = coord.Angle(radius)

        sector_request = "ra={}&dec={}&radius={}d".format(coordinates.ra.deg,
                                                          coordinates.dec.deg,
                                                          radius.deg)
        response = self._request("GET", self._TESSCUT_URL+"sector",
                                 params=sector_request)

        response.raise_for_status()  # Raise any errors

        sector_json = response.json()['results']
        sector_dict = {'sectorName': [],
                       'sector': [],
                       'camera': [],
                       'ccd': []}

        for entry in sector_json:
            sector_dict['sectorName'].append(entry['sectorName'])
            sector_dict['sector'].append(int(entry['sector']))
            sector_dict['camera'].append(int(entry['camera']))
            sector_dict['ccd'].append(int(entry['ccd']))

        if not len(sector_json):
            warning.warn("Coordinates are not in any TESS sector.", NoResultsWarning)
        return Table(sector_dict)

    def get_cutouts(self, coordinates, size=5, path=".", inflate=True):
        """
        Get cutout target pixel file(s) around the coordinae of the given size.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object.
        size : str, int, or `~astropy.units.Quantity` object, optional
            Default 5 pixels.
            The size of the cutout (cutout will be a ``size x size`` square).
            If supplied as an int pixels is the assumed unit.
            The string must be parsable by `astropy.coordinates.Angle`.
            `~astropy.units.Quantity` objects must be in pixel or angular units.
        path : str
            Optional.
            The directory in which the cutouts will be saved.
            Defaults to current directory.
        inflate : bool
            Optional, default True.
            Cutout target pixel files are returned from the server in a zip file,
            by default they will be inflated and the zip will be removed.
            Set inflate to false to stop before the inflate step.


        Returns
        -------
        response : `~astropy.table.Table`
        """

        # Check if tesscut is live before proceeding.
        self._tesscut_livecheck()

        # Put coordinates and radius into consistant format
        coordinates = commons.parse_coordinates(coordinates)

        # if radius is just a number we assume degrees
        unit = 'px'
        if isinstance(size, str):
            size = coord.Angle(size).deg
            unit = 'deg'
        elif isinstance(size, u.Quantity):
            if size.unit.physical_type == 'angle':
                size = size.deg
                unit = 'deg'
            elif size.unit == "pix":
                size = int(size.value)
            else:
                raise InvalidQueryError("Size must be an agular quantity or pixels.")

        path = os.path.join(path, '')
        astrocut_request = "ra={}&dec={}&size={}{}".format(coordinates.ra.deg,
                                                           coordinates.dec.deg,
                                                           size, unit)
        astrocut_url = self._TESSCUT_URL + "astrocut?" + astrocut_request
        zipfile_path = "{}tesscut_{}.zip".format(path, time.strftime("%Y%m%d%H%M%S"))

        self._download_file(astrocut_url, zipfile_path)

        localpath_table = Table(names=["local_file"], dtype=[str])

        # Checking if we got a zip file or a json no results message
        if not zipfile.is_zipfile(zipfile_path):
            with open(zipfile_path, 'r') as FLE:
                response = json.load(FLE)
            warnings.warn(response['msg'], NoResultsWarning)
            return localpath_table

        if not inflate:  # not unzipping
            localpath_table['local_file'] = [zipfile_path]
            return localpath_table

        print("Inflating...")
        # unzipping the zipfile
        zip_ref = zipfile.ZipFile(zipfile_path, 'r')
        cutout_files = zip_ref.namelist()
        zip_ref.extractall(path, members=cutout_files)
        zip_ref.close()
        os.remove(zipfile_path)

        localpath_table['local_file'] = [path+x for x in cutout_files]
        return localpath_table


Tesscut = TesscutClass()
