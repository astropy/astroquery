import requests
import io

from astropy import units as u
from astropy.io.votable import parse_single_table
# The VOTables fetched from SVO contain only single table element, thus parse_single_table

from . import conf

from ..query import BaseQuery
from astroquery.exceptions import InvalidQueryError, TimeoutError


__all__ = ['SvoFpsClass', 'SvoFps']

# Valid query parameters taken from
# http://svo2.cab.inta-csic.es/theory/fps/index.php?mode=voservice
_params_with_range = {"WavelengthRef", "WavelengthMean", "WavelengthEff",
                      "WavelengthMin", "WavelengthMax", "WidthEff", "FWHM"}
QUERY_PARAMETERS = _params_with_range.copy()
for suffix in ("_min", "_max"):
    QUERY_PARAMETERS.update(param + suffix for param in _params_with_range)
QUERY_PARAMETERS.update(("Instrument", "Facility", "PhotSystem", "ID", "PhotCalID",
                         "FORMAT", "VERB"))


class SvoFpsClass(BaseQuery):
    """
    Class for querying the Spanish Virtual Observatory filter profile service
    """
    SVO_MAIN_URL = conf.base_url
    TIMEOUT = conf.timeout

    def data_from_svo(self, query, *, cache=True, timeout=None,
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
            values as required. Description of search parameters can be found at
            http://svo2.cab.inta-csic.es/theory/fps/index.php?mode=voservice
        error_msg : str, optional
            Error message to be shown in case no table element found in the
            responded VOTable. Use this to make error message verbose in context
            of the query made (default is 'No data found for requested query')
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        astropy.table.table.Table object
            Table containing data fetched from SVO (in response to query)
        """
        bad_params = [param for param in query if param not in QUERY_PARAMETERS]
        if bad_params:
            raise InvalidQueryError(
                f"parameter{'s' if len(bad_params) > 1 else ''} "
                f"{', '.join(bad_params)} {'are' if len(bad_params) > 1 else 'is'} "
                f"invalid. For a description of valid query parameters see "
                "http://svo2.cab.inta-csic.es/theory/fps/index.php?mode=voservice"
            )
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

    def get_filter_index(self, wavelength_eff_min, wavelength_eff_max, **kwargs):
        """Get master list (index) of all filters at SVO
        Optional parameters can be given to get filters data for specified
        Wavelength Effective range from SVO

        Parameters
        ----------
        wavelength_eff_min : `~astropy.units.Quantity` with units of length
            Minimum value of Wavelength Effective
        wavelength_eff_max : `~astropy.units.Quantity` with units of length
            Maximum value of Wavelength Effective
        kwargs : dict
            Passed to `data_from_svo`.  Relevant arguments include ``cache``

        Returns
        -------
        astropy.table.table.Table object
            Table containing data fetched from SVO (in response to query)
        """
        query = {'WavelengthEff_min': wavelength_eff_min.to_value(u.angstrom),
                 'WavelengthEff_max': wavelength_eff_max.to_value(u.angstrom)}
        error_msg = 'No filter found for requested Wavelength Effective range'
        try:
            return self.data_from_svo(query=query, error_msg=error_msg, **kwargs)
        except requests.ReadTimeout:
            raise TimeoutError(
                "Query did not finish fast enough. A smaller wavelength range might "
                "succeed. Try increasing the timeout limit if a large range is needed."
            )

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

    def get_filter_list(self, facility, *, instrument=None, **kwargs):
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
