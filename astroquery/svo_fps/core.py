import numpy as np
import requests
import io

from astropy import units as u
from astropy.io.votable import parse_single_table
# The VOTables fetched from SVO contain only single table element, thus parse_single_table

from . import conf

from ..query import BaseQuery

__all__ = ['SvoFpsClass', 'SvoFps']

FLOAT_MAX = np.finfo(np.float64).max


class SvoFpsClass(BaseQuery):
    """
    Class for querying the Spanish Virtual Observatory filter profile service
    """
    SVO_MAIN_URL = conf.base_url
    TIMEOUT = conf.timeout

    def data_from_svo(self, query, cache=True, timeout=None,
                      error_msg='No data found for requested query'):
        """Get data in response to the query send to SVO FPS.
        This method is not generally intended for users, but it can be helpful
        if you want something very specific from the SVO FPS service.
        If you don't know what you're doing, try `get_filter_index`,
        `get_filter_list`, and `get_transmission_data` instead.

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
        cache : bool
            Cache the results?  Defaults to True

        Returns
        -------
        astropy.table.table.Table object
            Table containing data fetched from SVO (in response to query)
        """
        response = self._request("GET", self.SVO_MAIN_URL, params=query,
                                 timeout=timeout or self.TIMEOUT,
                                 cache=cache)
        response.raise_for_status()
        votable = io.BytesIO(response.content)
        try:
            return parse_single_table(votable).to_table()
        except IndexError:
            # If no table element found in VOTable
            raise IndexError(error_msg)

    def get_filter_index(self, wavelength_eff_min=0*u.angstrom,
                         wavelength_eff_max=FLOAT_MAX*u.angstrom, **kwargs):
        """Get master list (index) of all filters at SVO
        Optional parameters can be given to get filters data for specified
        Wavelength Effective range from SVO

        Parameters
        ----------
        wavelength_eff_min : `~astropy.units.Quantity` having units of angstrom, optional
            Minimum value of Wavelength Effective (default is 0 angstrom)
        wavelength_eff_max : `~astropy.units.Quantity` having units of angstrom, optional
            Maximum value of Wavelength Effective (default is a very large
            quantity FLOAT_MAX angstroms i.e. maximum value of np.float64)
        kwargs : dict
            Passed to `data_from_svo`.  Relevant arguments include ``cache``

        Returns
        -------
        astropy.table.table.Table object
            Table containing data fetched from SVO (in response to query)
        """
        query = {'WavelengthEff_min': wavelength_eff_min.value,
                 'WavelengthEff_max': wavelength_eff_max.value}
        error_msg = 'No filter found for requested Wavelength Effective range'
        return self.data_from_svo(query=query, error_msg=error_msg, **kwargs)

    def get_transmission_data(self, filter_id, **kwargs):
        """Get transmission data for the requested Filter ID from SVO

        Parameters
        ----------
        filter_id : str
            Filter ID in the format SVO specifies it: 'facilty/instrument.filter'.
            This is returned by `get_filter_list` and `get_filter_index` as the
            ``filterID`` column.
        kwargs : dict
            Passed to `data_from_svo`.  Relevant arguments include ``cache``

        Returns
        -------
        astropy.table.table.Table object
            Table containing data fetched from SVO (in response to query)
        """
        query = {'ID': filter_id}
        error_msg = 'No filter found for requested Filter ID'
        return self.data_from_svo(query=query, error_msg=error_msg, **kwargs)

    def get_filter_list(self, facility, instrument=None, **kwargs):
        """Get filters data for requested facilty and instrument from SVO

        Parameters
        ----------
        facility : str
            Facilty for filters
        instrument : str, optional
            Instrument for filters (default is None).
            Leave empty if there are no instruments for specified facilty
        kwargs : dict
            Passed to `data_from_svo`.  Relevant arguments include ``cache``

        Returns
        -------
        astropy.table.table.Table object
            Table containing data fetched from SVO (in response to query)
        """
        query = {'Facility': facility,
                 'Instrument': instrument}
        error_msg = 'No filter found for requested Facilty (and Instrument)'
        return self.data_from_svo(query=query, error_msg=error_msg, **kwargs)


SvoFps = SvoFpsClass()
