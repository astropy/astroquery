# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
MAST Tesscut
============

Cutout queries on TESS FFIs.

"""


import warnings
import time
import json
import zipfile
import os

from io import BytesIO

import numpy as np

import astropy.units as u
from astropy.coordinates import Angle

from astropy.table import Table
from astropy.io import fits

from ..exceptions import InputWarning, NoResultsWarning, InvalidQueryError

from .utils import parse_input_location
from .core import MastQueryWithLogin


__all__ = ["TesscutClass", "Tesscut", "ZcutClass", "Zcut"]


def _parse_cutout_size(size):
    """
    Take a user input cutout size and parse it into the regular format
    [ny,nx] where nx/ny are quantities with units either pixels or degrees.

    Parameters
    ----------
    size : int, array-like, `~astropy.units.Quantity`
        The size of the cutout array. If ``size`` is a scalar number or
        a scalar `~astropy.units.Quantity`, then a square cutout of ``size``
        will be created.  If ``size`` has two elements, they should be in
        ``(ny, nx)`` order.  Scalar numbers in ``size`` are assumed to be in
        units of pixels. `~astropy.units.Quantity` objects must be in pixel or
        angular units.

    Returns
    -------
    response : array
        Size array in the form [ny, nx] where nx/ny are quantities with units
        either pixels or degrees.
    """

    # Making size into an array [ny, nx]
    if np.isscalar(size):
        size = np.repeat(size, 2)

    if isinstance(size, u.Quantity):
        size = np.atleast_1d(size)
        if len(size) == 1:
            size = np.repeat(size, 2)

    if len(size) > 2:
        warnings.warn("Too many dimensions in cutout size, only the first two will be used.",
                      InputWarning)

    # Getting x and y out of the size
    if np.isscalar(size[0]):
        x = size[1]
        y = size[0]
        units = "px"
    elif size[0].unit == u.pixel:
        x = size[1].value
        y = size[0].value
        units = "px"
    elif size[0].unit.physical_type == 'angle':
        x = size[1].to(u.deg).value
        y = size[0].to(u.deg).value
        units = "d"
    else:
        raise InvalidQueryError("Cutout size must be in pixels or angular quantity.")

    return {"x": x, "y": y, "units": units}


class TesscutClass(MastQueryWithLogin):
    """
    MAST TESS FFI cutout query class.

    Class for accessing TESS full-frame image cutouts.
    """

    def __init__(self):

        super().__init__()

        services = {"sector": {"path": "sector"},
                    "astrocut": {"path": "astrocut"},
                    "mt_sector": {"path": "moving_target/sector"},
                    "mt_astrocut": {"path": "moving_target/astrocut"}
                    }
        self._service_api_connection.set_service_params(services, "tesscut")

    def get_sectors(self, *, coordinates=None, radius=0*u.deg, product='SPOC', objectname=None,
                    moving_target=False, mt_type=None):
        """
        Get a list of the TESS data sectors whose footprints intersect
        with the given search area.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object, optional
            The target around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object.

            NOTE: If moving_target or objectname is supplied, this argument cannot be used.
        radius : str, float, or `~astropy.units.Quantity` object, optional
            Default 0 degrees.
            If supplied as a float degrees is the assumed unit.
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used.

            NOTE: If moving_target is supplied, this argument is ignored.
        product : str
            Default is 'SPOC'.
            The product whose sectors will be returned. Options are: 'SPOC' or 'TICA', for the Science Processing
            Operations Center (SPOC) products, and the TESS Image CAlibration (TICA) high-level science products,
            respectively. TICA products will usually be available for the latest sectors sooner than their SPOC
            counterparts, but are not available for sectors 1-26.

            NOTE: TICA is currently not available for moving targets.
        objectname : str, optional
            The target around which to search, by name (objectname="M104")
            or TIC ID (objectname="TIC 141914082"). If moving_target is True, input must be the name or ID
            (as understood by the `JPL ephemerides service <https://ssd.jpl.nasa.gov/horizons.cgi>`__)
            of a moving target such as an asteroid or comet.

            NOTE: If coordinates is supplied, this argument cannot be used.
        moving_target : bool, optional
            Indicate whether the object is a moving target or not. Default is set to False, in other words,
            not a moving target.

            NOTE: If coordinates is supplied, this argument cannot be used.
        mt_type : str, optional
            The moving target type, valid inputs are majorbody and smallbody. If not supplied
            first majorbody is tried and then smallbody if a matching majorbody is not found.

            NOTE: If moving_target is supplied, this argument is ignored.

        Returns
        -------
        response : `~astropy.table.Table`
            Sector/camera/chip information for given coordinates/objectname/moving_target.
        """

        if moving_target:

            # The Moving Targets service is currently only available for SPOC
            if product.upper() != "SPOC":
                raise InvalidQueryError("Only SPOC is available for moving targets queries.")

            # Check that objectname has been passed in and coordinates
            # is not
            if coordinates:
                raise InvalidQueryError("Only one of moving_target and coordinates may be specified. "
                                        "Please remove coordinates if using moving_target and objectname.")

            if not objectname:
                raise InvalidQueryError("Please specify the object name or ID (as understood by the "
                                        "`JPL ephemerides service <https://ssd.jpl.nasa.gov/horizons.cgi>`__) "
                                        "of a moving target such as an asteroid or comet.")

            params = {"product": product.upper(), "obj_id": objectname}

            # Add optional parameter is present
            if mt_type:
                params["obj_type"] = mt_type

            response = self._service_api_connection.service_request_async("mt_sector", params)

        else:

            # Get Skycoord object for coordinates/object
            coordinates = parse_input_location(coordinates, objectname)

            # If radius is just a number we assume degrees
            radius = Angle(radius, u.deg)

            # Making sure input product is either SPOC or TICA
            if product.upper() not in ['TICA', 'SPOC']:
                raise InvalidQueryError("Input product must either be SPOC or TICA.")

            params = {"ra": coordinates.ra.deg,
                      "dec": coordinates.dec.deg,
                      "radius": radius.deg,
                      "product": product.upper()}

            response = self._service_api_connection.service_request_async("sector", params)

        # Raise any errors
        response.raise_for_status()

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
            warnings.warn("Coordinates are not in any TESS sector.", NoResultsWarning)
        return Table(sector_dict)

    def download_cutouts(self, *, coordinates=None, size=5, sector=None, product='SPOC', path=".",
                         inflate=True, objectname=None, moving_target=False, mt_type=None, verbose=False):
        """
        Download cutout target pixel file(s) around the given coordinates with indicated size.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object, optional
            The target around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object.

            NOTE: If moving_target or objectname is supplied, this argument cannot be used.
        size : int, array-like, `~astropy.units.Quantity`
            Optional, default 5 pixels.
            The size of the cutout array. If ``size`` is a scalar number or
            a scalar `~astropy.units.Quantity`, then a square cutout of ``size``
            will be created.  If ``size`` has two elements, they should be in
            ``(ny, nx)`` order.  Scalar numbers in ``size`` are assumed to be in
            units of pixels. `~astropy.units.Quantity` objects must be in pixel or
            angular units.
        sector : int
            Optional.
            The TESS sector to return the cutout from.  If not supplied, cutouts
            from all available sectors on which the coordinate appears will be returned.
        product : str
            Default is 'SPOC'.
            The product that the cutouts will be made out of. Options are: 'SPOC' or 'TICA', for the Science Processing
            Operations Center (SPOC) products, and the TESS Image CAlibration (TICA) high-level science products,
            respectively. TICA products will usually be available for the latest sectors sooner than their SPOC
            counterparts, but are not available for sectors 1-26.

            NOTE: TICA is currently not available for moving targets.
        path : str
            Optional.
            The directory in which the cutouts will be saved.
            Defaults to current directory.
        inflate : bool
            Optional, default True.
            Cutout target pixel files are returned from the server in a zip file,
            by default they will be inflated and the zip will be removed.
            Set inflate to false to stop before the inflate step.
        objectname : str, optional
            The target around which to search, by name (objectname="M104")
            or TIC ID (objectname="TIC 141914082"). If moving_target is True, input must be the name or ID
            (as understood by the `JPL ephemerides service <https://ssd.jpl.nasa.gov/horizons.cgi>`__)
            of a moving target such as an asteroid or comet.

            NOTE: If coordinates is supplied, this argument cannot be used.
        moving_target : str, optional
            Indicate whether the object is a moving target or not. Default is set to False, in other words,
            not a moving target.

            NOTE: If coordinates is supplied, this argument cannot be used.
        mt_type : str, optional
            The moving target type, valid inputs are majorbody and smallbody. If not supplied
            first majorbody is tried and then smallbody if a matching majorbody is not found.

            NOTE: If moving_target is supplied, this argument is ignored.

        Returns
        -------
        response : `~astropy.table.Table`
        """

        if moving_target:

            # The Moving Targets service is currently only available for SPOC
            if product.upper() != "SPOC":
                raise InvalidQueryError("Only SPOC is available for moving targets queries.")

            # Check that objectname has been passed in and coordinates
            # is not
            if coordinates:
                raise InvalidQueryError("Only one of moving_target and coordinates may be specified. "
                                        "Please remove coordinates if using moving_target and objectname.")

            if not objectname:
                raise InvalidQueryError("Please specify the object name or ID (as understood by the "
                                        "`JPL ephemerides service <https://ssd.jpl.nasa.gov/horizons.cgi>`__) "
                                        "of a moving target such as an asteroid or comet.")

            astrocut_request = f"moving_target/astrocut?obj_id={objectname}&product={product.upper()}"
            if mt_type:
                astrocut_request += f"&obj_type={mt_type}"

        else:

            # Get Skycoord object for coordinates/object
            coordinates = parse_input_location(coordinates, objectname)

            astrocut_request = f"astrocut?ra={coordinates.ra.deg}&dec={coordinates.dec.deg}"

        # Adding the arguments that are common between moving/still astrocut requests
        size_dict = _parse_cutout_size(size)
        astrocut_request += f"&y={size_dict['y']}&x={size_dict['x']}&units={size_dict['units']}"

        # Making sure input product is either SPOC or TICA,
        # and adding the argument to the request URL
        if product.upper() not in ['TICA', 'SPOC']:
            raise InvalidQueryError("Input product must either be SPOC or TICA.")
        astrocut_request += f"&product={product.upper()}"

        if sector:
            astrocut_request += "&sector={}".format(sector)

        astrocut_url = self._service_api_connection.REQUEST_URL + astrocut_request
        path = os.path.join(path, '')
        zipfile_path = "{}tesscut_{}.zip".format(path, time.strftime("%Y%m%d%H%M%S"))
        self._download_file(astrocut_url, zipfile_path)

        localpath_table = Table(names=["Local Path"], dtype=[str])

        # Checking if we got a zip file or a json no results message
        if not zipfile.is_zipfile(zipfile_path):
            with open(zipfile_path, 'r') as FLE:
                response = json.load(FLE)
            warnings.warn(response['msg'], NoResultsWarning)
            return localpath_table

        if not inflate:  # not unzipping
            localpath_table['Local Path'] = [zipfile_path]
            return localpath_table

        if verbose:
            print("Inflating...")

        # unzipping the zipfile
        zip_ref = zipfile.ZipFile(zipfile_path, 'r')
        cutout_files = zip_ref.namelist()
        zip_ref.extractall(path, members=cutout_files)
        zip_ref.close()
        os.remove(zipfile_path)

        localpath_table['Local Path'] = [path+x for x in cutout_files]
        return localpath_table

    def get_cutouts(self, *, coordinates=None, size=5, product='SPOC', sector=None,
                    objectname=None, moving_target=False, mt_type=None):
        """
        Get cutout target pixel file(s) around the given coordinates with indicated size,
        and return them as a list of  `~astropy.io.fits.HDUList` objects.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object, optional
            The target around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object.

            NOTE: If moving_target or objectname is supplied, this argument cannot be used.
        size : int, array-like, `~astropy.units.Quantity`
            Optional, default 5 pixels.
            The size of the cutout array. If ``size`` is a scalar number or
            a scalar `~astropy.units.Quantity`, then a square cutout of ``size``
            will be created.  If ``size`` has two elements, they should be in
            ``(ny, nx)`` order.  Scalar numbers in ``size`` are assumed to be in
            units of pixels. `~astropy.units.Quantity` objects must be in pixel or
            angular units.
        product : str
            Default is 'SPOC'.
            The product that the cutouts will be made out of. Options are: 'SPOC' or 'TICA', for the Science Processing
            Operations Center (SPOC) products, and the TESS Image CAlibration (TICA) high-level science products,
            respectively. TICA products will usually be available for the latest sectors sooner than their SPOC
            counterparts, but are not available for sectors 1-26.

            NOTE: TICA is currently not available for moving targets.
        sector : int
            Optional.
            The TESS sector to return the cutout from.  If not supplied, cutouts
            from all available sectors on which the coordinate appears will be returned.
        objectname : str, optional
            The target around which to search, by name (objectname="M104")
            or TIC ID (objectname="TIC 141914082"). If moving_target is True, input must be the name or ID
            (as understood by the `JPL ephemerides service <https://ssd.jpl.nasa.gov/horizons.cgi>`__)
            of a moving target such as an asteroid or comet.

            NOTE: If coordinates is supplied, this argument cannot be used.
        moving_target : str, optional
            Indicate whether the object is a moving target or not. Default is set to False, in other words,
            not a moving target.

            NOTE: If coordinates is supplied, this argument cannot be used.
        mt_type : str, optional
            The moving target type, valid inputs are majorbody and smallbody. If not supplied
            first majorbody is tried and then smallbody if a matching majorbody is not found.

            NOTE: If moving_target is supplied, this argument is ignored.

        Returns
        -------
        response : A list of `~astropy.io.fits.HDUList` objects.
        """

        # Setting up the cutout size
        param_dict = _parse_cutout_size(size)

        # Add sector if present
        if sector:
            param_dict["sector"] = sector

        if moving_target:

            # The Moving Targets service is currently only available for SPOC
            if product.upper() != "SPOC":
                raise InvalidQueryError("Only SPOC is available for moving targets queries.")

            param_dict['product'] = product.upper()

            # Check that objectname has been passed in and coordinates
            # is not
            if coordinates:
                raise InvalidQueryError("Only one of moving_target and coordinates may be specified. "
                                        "Please remove coordinates if using moving_target and objectname.")

            if not objectname:
                raise InvalidQueryError("Please specify the object name or ID (as understood by the "
                                        "`JPL ephemerides service <https://ssd.jpl.nasa.gov/horizons.cgi>`__) "
                                        "of a moving target such as an asteroid or comet.")

            param_dict["obj_id"] = objectname

            # Add optional parameter if present
            if mt_type:
                param_dict["obj_type"] = mt_type

            response = self._service_api_connection.service_request_async("mt_astrocut", param_dict)

        else:

            # Making sure input product is either SPOC or TICA, then add the `product` param
            if product.upper() not in ['TICA', 'SPOC']:
                raise InvalidQueryError("Input product must either be SPOC or TICA.")

            param_dict['product'] = product.upper()

            # Get Skycoord object for coordinates/object
            coordinates = parse_input_location(coordinates, objectname)

            param_dict["ra"] = coordinates.ra.deg
            param_dict["dec"] = coordinates.dec.deg

            response = self._service_api_connection.service_request_async("astrocut", param_dict)

        response.raise_for_status()  # Raise any errors

        try:
            ZIPFILE = zipfile.ZipFile(BytesIO(response.content), 'r')
        except zipfile.BadZipFile:
            message = response.json()
            warnings.warn(message['msg'], NoResultsWarning)
            return []

        # Open all the contained fits files:
        # Since we cannot seek on a compressed zip file,
        # we have to read the data, wrap it in another BytesIO object,
        # and then open that using fits.open
        cutout_hdus_list = []
        for name in ZIPFILE.namelist():
            CUTOUT = BytesIO(ZIPFILE.open(name).read())
            cutout_hdus_list.append(fits.open(CUTOUT))

            # preserve the original filename in the fits object
            cutout_hdus_list[-1].filename = name

        return cutout_hdus_list


Tesscut = TesscutClass()


class ZcutClass(MastQueryWithLogin):
    """
    MAST ZCUT cutout query class.

    Class for accessing deep field full-frame image cutouts.
    """

    def __init__(self):

        super().__init__()

        self.accepted_img_params = ['stretch', 'minmax_percent', 'minmax_value', 'invert']

        services = {"survey": {"path": "survey"},
                    "astrocut": {"path": "astrocut"}}
        self._service_api_connection.set_service_params(services, "zcut")

    def get_surveys(self, coordinates, *, radius="0d"):
        """
        Gives a list of deep field surveys available for a position in the sky

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object.
        radius : str, float, or `~astropy.units.Quantity` object, optional
            Default 0 degrees.
            If supplied as a float, degrees is the assumed unit.
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used.

        Returns
        -------
        response : list
            List of available deep field surveys at the given coordinates.
        """

        # Get Skycoord object for coordinates/object
        coordinates = parse_input_location(coordinates)
        radius = Angle(radius, u.deg)

        params = {"ra": coordinates.ra.deg,
                  "dec": coordinates.dec.deg,
                  "radius": radius.deg}

        response = self._service_api_connection.service_request_async("survey", params)
        response.raise_for_status()  # Raise any errors

        survey_json = response.json()['surveys']

        if not len(survey_json):
            warnings.warn("Coordinates are not in an available deep field survey.", NoResultsWarning)
        return survey_json

    def download_cutouts(self, coordinates, *, size=5, survey=None, cutout_format="fits", path=".", inflate=True,
                         verbose=False, **img_params):
        """
        Download cutout FITS/image file(s) around the given coordinates with indicated size.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object.
        size : int, array-like, `~astropy.units.Quantity`
            Optional, default 5 pixels.
            The size of the cutout array. If ``size`` is a scalar number or
            a scalar `~astropy.units.Quantity`, then a square cutout of ``size``
            will be created.  If ``size`` has two elements, they should be in
            ``(ny, nx)`` order.  Scalar numbers in ``size`` are assumed to be in
            units of pixels. `~astropy.units.Quantity` objects must be in pixel or
            angular units.
        survey : str
            Optional
            The survey to restrict the cutout. The survey parameter will restrict to
            only the matching survey. Default behavior is to return all matched surveys.
        cutout_format : str
            Optional
            The cutout file format. Default is fits, valid options are fits, jpg, png.
        path : str
            Optional.
            The directory in which the cutouts will be saved.
            Defaults to current directory.
        inflate : bool
            Optional, default True.
            Cutout target pixel files are returned from the server in a zip file,
            by default they will be inflated and the zip will be removed.
            Set inflate to false to stop before the inflate step.
        **img_params : dict
            Optional, only used if format is jpg or png
            Valid parameters are stretch, minmax_percent, minmax_value, and invert.
            These arguments are documented here:
            https://astrocut.readthedocs.io/en/latest/api/astrocut.img_cut.html
            The Column Name is the keyword, with the argument being one or more acceptable
            values for that parameter, except for fields with a float datatype where the
            argument should be in the form [minVal, maxVal].

        Returns
        -------
        response : `~astropy.table.Table`
            Cutout file(s) for given coordinates
        """
        # Get Skycoord object for coordinates/object
        coordinates = parse_input_location(coordinates)
        size_dict = _parse_cutout_size(size)

        path = os.path.join(path, '')
        astrocut_request = "ra={}&dec={}&y={}&x={}&units={}".format(coordinates.ra.deg,
                                                                    coordinates.dec.deg,
                                                                    size_dict["y"],
                                                                    size_dict["x"],
                                                                    size_dict["units"])

        if survey:
            astrocut_request += "&survey={}".format(survey)

        astrocut_request += "&format={}".format(cutout_format)

        for key in img_params:
            if key in self.accepted_img_params:
                astrocut_request += "&{}={}".format(key, img_params[key])

        astrocut_url = self._service_api_connection.REQUEST_URL + "astrocut?" + astrocut_request
        zipfile_path = "{}zcut_{}.zip".format(path, time.strftime("%Y%m%d%H%M%S"))
        self._download_file(astrocut_url, zipfile_path)

        localpath_table = Table(names=["Local Path"], dtype=[str])

        if not zipfile.is_zipfile(zipfile_path):
            with open(zipfile_path, 'r') as FLE:
                response = json.load(FLE)
            warnings.warn(response['msg'], NoResultsWarning)
            return localpath_table

        if not inflate:  # not unzipping
            localpath_table['Local Path'] = [zipfile_path]
            return localpath_table

        if verbose:
            print("Inflating...")

        # unzipping the zipfile
        zip_ref = zipfile.ZipFile(zipfile_path, 'r')
        cutout_files = zip_ref.namelist()
        zip_ref.extractall(path, members=cutout_files)
        zip_ref.close()
        os.remove(zipfile_path)

        localpath_table['Local Path'] = [path+x for x in cutout_files]
        return localpath_table

    def get_cutouts(self, coordinates, *, size=5, survey=None):
        """
        Get cutout  FITS file(s) around the given coordinates with indicated size,
        and return them as a list of  `~astropy.io.fits.HDUList` objects.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object.
            One and only one of coordinates and objectname must be supplied.
        size : int, array-like, `~astropy.units.Quantity`
            Optional, default 5 pixels.
            The size of the cutout array. If ``size`` is a scalar number or
            a scalar `~astropy.units.Quantity`, then a square cutout of ``size``
            will be created.  If ``size`` has two elements, they should be in
            ``(ny, nx)`` order.  Scalar numbers in ``size`` are assumed to be in
            units of pixels. `~astropy.units.Quantity` objects must be in pixel or
            angular units.
        survey : str
            Optional
            The survey to restrict the cutout. The survey parameter will restrict to
            only the matching survey. Default behavior is to return all matched surveys.

        Returns
        -------
        response : A list of `~astropy.io.fits.HDUList` objects.
            Cutoutfiles for given coordinates
        """

        # Get Skycoord object for coordinates/object
        coordinates = parse_input_location(coordinates)

        param_dict = _parse_cutout_size(size)
        param_dict["ra"] = coordinates.ra.deg
        param_dict["dec"] = coordinates.dec.deg

        if survey:
            param_dict["survey"] = survey

        response = self._service_api_connection.service_request_async("astrocut", param_dict)
        response.raise_for_status()  # Raise any errors

        try:
            ZIPFILE = zipfile.ZipFile(BytesIO(response.content), 'r')
        except zipfile.BadZipFile:
            message = response.json()
            warnings.warn(message['msg'], NoResultsWarning)
            return []

        # Open all the contained fits files:
        # Since we cannot seek on a compressed zip file,
        # we have to read the data, wrap it in another BytesIO object,
        # and then open that using fits.open
        cutout_list = []
        for name in ZIPFILE.namelist():
            CUTOUT = BytesIO(ZIPFILE.open(name).read())
            cutout_list.append(fits.open(CUTOUT))

            # preserve the original filename in the fits object
            cutout_list[-1].filename = name

        return cutout_list


Zcut = ZcutClass()


class HapcutClass(MastQueryWithLogin):
    """
    MAST Hubble Advanced Product (HAP) cutout query class.

    Class for accessing HAP image cutouts.
    """

    def __init__(self):

        super().__init__()

        services = {"astrocut": {"path": "astrocut"}}

        self._service_api_connection.set_service_params(services, "hapcut")

    def download_cutouts(self, coordinates, *, size=5, path=".", inflate=True, verbose=False):
        """
        Download cutout images around the given coordinates with indicated size.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object.
        size : int, array-like, `~astropy.units.Quantity`
            Optional, default 5 pixels.
            The size of the cutout array. If ``size`` is a scalar number or
            a scalar `~astropy.units.Quantity`, then a square cutout of ``size``
            will be created.  If ``size`` has two elements, they should be in
            ``(ny, nx)`` order.  Scalar numbers in ``size`` are assumed to be in
            units of pixels. `~astropy.units.Quantity` objects must be in pixel or
            angular units.
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

        # Get Skycoord object for coordinates/object
        coordinates = parse_input_location(coordinates)

        # Build initial astrocut request
        astrocut_request = f"astrocut?ra={coordinates.ra.deg}&dec={coordinates.dec.deg}"

        # Add size parameters to request
        size_dict = _parse_cutout_size(size)
        astrocut_request += f"&x={size_dict['x']}&y={size_dict['y']}&units={size_dict['units']}"

        # Build the URL
        astrocut_url = self._service_api_connection.REQUEST_URL + astrocut_request

        # Set up the download path
        path = os.path.join(path, '')
        zipfile_path = "{}hapcut_{}.zip".format(path, time.strftime("%Y%m%d%H%M%S"))

        # Download
        self._download_file(astrocut_url, zipfile_path)
        localpath_table = Table(names=["Local Path"], dtype=[str])

        # Checking if we got a zip file or a json no results message
        if not zipfile.is_zipfile(zipfile_path):
            with open(zipfile_path, 'r') as FLE:
                response = json.load(FLE)
            warnings.warn(response['msg'], NoResultsWarning)
            return localpath_table

        if not inflate:  # not unzipping
            localpath_table['Local Path'] = [zipfile_path]
            return localpath_table

        if verbose:
            print("Inflating...")

        # unzipping the zipfile
        zip_ref = zipfile.ZipFile(zipfile_path, 'r')
        cutout_files = zip_ref.namelist()
        zip_ref.extractall(path, members=cutout_files)
        zip_ref.close()
        os.remove(zipfile_path)

        localpath_table['Local Path'] = [path+x for x in cutout_files]
        return localpath_table

    def get_cutouts(self, coordinates, *, size=5):
        """
        Get cutout image(s) around the given coordinates with indicated size,
        and return them as a list of  `~astropy.io.fits.HDUList` objects.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object.
        size : int, array-like, `~astropy.units.Quantity`
            Optional, default 5 pixels.
            The size of the cutout array. If ``size`` is a scalar number or
            a scalar `~astropy.units.Quantity`, then a square cutout of ``size``
            will be created.  If ``size`` has two elements, they should be in
            ``(ny, nx)`` order.  Scalar numbers in ``size`` are assumed to be in
            units of pixels. `~astropy.units.Quantity` objects must be in pixel or
            angular units.

        Returns
        -------
        response : A list of `~astropy.io.fits.HDUList` objects.
        """

        # Get Skycoord object for coordinates/object
        coordinates = parse_input_location(coordinates)

        param_dict = _parse_cutout_size(size)

        # Need to convert integers from numpy dtypes
        # so we can convert the dictionary into a JSON object
        # in service_request_async(...)
        param_dict["x"] = float(param_dict["x"])
        param_dict["y"] = float(param_dict["y"])

        # Adding RA and DEC to parameters dictionary
        param_dict["ra"] = coordinates.ra.deg
        param_dict["dec"] = coordinates.dec.deg

        response = self._service_api_connection.service_request_async("astrocut", param_dict, use_json=True)
        response.raise_for_status()  # Raise any errors

        try:
            ZIPFILE = zipfile.ZipFile(BytesIO(response.content), 'r')
        except zipfile.BadZipFile:
            message = response.json()
            if len(message['results']) == 0:
                warnings.warn(message['msg'], NoResultsWarning)
                return []
            else:
                raise

        # Open all the contained fits files:
        # Since we cannot seek on a compressed zip file,
        # we have to read the data, wrap it in another BytesIO object,
        # and then open that using fits.open
        cutout_hdus_list = []
        for name in ZIPFILE.namelist():
            CUTOUT = BytesIO(ZIPFILE.open(name).read())
            cutout_hdus_list.append(fits.open(CUTOUT))

            # preserve the original filename in the fits object
            cutout_hdus_list[-1].filename = name

        return cutout_hdus_list


Hapcut = HapcutClass()
