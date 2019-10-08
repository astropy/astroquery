import numpy as np
import pandas as pd
import requests
import io

from astropy import units as u
from astropy.io.votable import parse_single_table
# The VOTables fetched from SVO contain only single table element, thus parse_single_table

from ..query import BaseQuery

__all__ = ['SvoFpsClass', 'SvoFps']

FLOAT_MAX = np.finfo(np.float64).max


class SvoFpsClass(BaseQuery):
    SVO_MAIN_URL = 'http://svo2.cab.inta-csic.es/theory/fps/fps.php'

    def data_from_svo(self, query, error_msg='No data found for requested query'):
        """Get data in response to the query send to SVO FPS

        Parameters
        ----------
        query : dict
            Used to create a HTTP query string i.e. send to SVO FPS to get data.
            In dictionary, specify keys as search parameters (str) and
            values as required. List of search parameters can be found at
            http://svo2.cab.inta-csic.es/theory/fps/fps.php?FORMAT=metadata
        error_msg : str, optional
            Error message to be shown in case no table element found in the
            responded VOTable. Use this to make error message verbose in context
            of the query made (default is 'No data found for requested query')

        Returns
        -------
        astropy.io.votable.tree.Table object
            Table element of the VOTable fetched from SVO (in response to query)
        """
        response = self._request("GET", self.SVO_MAIN_URL, params=query)
        response.raise_for_status()
        votable = io.BytesIO(response.content)
        try:
            return parse_single_table(votable)
        except IndexError:
            # If no table element found in VOTable
            raise ValueError(error_msg)

    def get_filter_index(self, wavelength_eff_min=0, wavelength_eff_max=FLOAT_MAX):
        """Get master list (index) of all filters at SVO
        Optional parameters can be given to get filters data for specified
        Wavelength Eff. range from SVO

        Parameters
        ----------
        wavelength_eff_min : float, optional
            Minimum value of Wavelength Eff. (default is 0)
        wavelength_eff_max : float, optional
            Maximum value of Wavelength Eff. (default is a very large no.
            FLOAT_MAX - maximum value of np.float64)

        Returns
        -------
        astropy.io.votable.tree.Table object
            Table element of the VOTable fetched from SVO (in response to query)
        """
        wavelength_eff_min = u.Quantity(wavelength_eff_min, u.angstrom)
        wavelength_eff_max = u.Quantity(wavelength_eff_max, u.angstrom)
        query = {'WavelengthEff_min': wavelength_eff_min.value,
                 'WavelengthEff_max': wavelength_eff_max.value}
        error_msg = 'No filter found for requested Wavelength Eff. range'
        return self.data_from_svo(query, error_msg)

    def get_transmission_data(self, filter_id):
        """Get transmission data for the requested Filter ID from SVO

        Parameters
        ----------
        filter_id : str
            Filter ID in the format SVO specifies it: 'facilty/instrument.filter'

        Returns
        -------
        astropy.io.votable.tree.Table object
            Table element of the VOTable fetched from SVO (in response to query)
        """
        query = {'ID': filter_id}
        error_msg = 'No filter found for requested Filter ID'
        return self.data_from_svo(query, error_msg)

    def get_filter_list(self, facility, instrument=None):
        """Get filters data for requested facilty and instrument from SVO

        Parameters
        ----------
        facility : str
            Facilty for filters
        instrument : str, optional
            Instrument for filters (default is None).
            Leave empty if there are no instruments for specified facilty

        Returns
        -------
        astropy.io.votable.tree.Table object
            Table element of the VOTable fetched from SVO (in response to query)
        """
        query = {'Facility': facility,
                 'Instrument': instrument}
        error_msg = 'No filter found for requested Facilty (and Instrument)'
        return self.data_from_svo(query, error_msg)


SvoFps = SvoFpsClass()
