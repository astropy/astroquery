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
# https://svo2.cab.inta-csic.es/theory/fps/index.php?mode=voservice
_params_with_range = {"WavelengthRef", "WavelengthMean", "WavelengthEff",
                      "WavelengthMin", "WavelengthMax", "WidthEff", "FWHM"}
QUERY_PARAMETERS = _params_with_range.copy()
for suffix in ("_min", "_max"):
    QUERY_PARAMETERS.update(param + suffix for param in _params_with_range)
QUERY_PARAMETERS.update(("Instrument", "Facility", "PhotSystem", "ID", "PhotCalID",
                         "FORMAT", "VERB"))

ALLOWED_QUERY_PARAMETERS = {
    "VERB": {0, 1, 2},
    "FORMAT": {"metadata", None}
}


class SvoFpsClass(BaseQuery):
    """
    Class for querying the Spanish Virtual Observatory filter profile service
    """
    SVO_MAIN_URL = conf.base_url
    TIMEOUT = conf.timeout

    def data_from_svo(self,
                      *,
                      WavelengthRef_min=None,
                      WavelengthRef_max=None,
                      WavelengthMean_min=None,
                      WavelengthMean_max=None,
                      WavelengthEff_min=None,
                      WavelengthEff_max=None,
                      WavelengthMin_min=None,
                      WavelengthMin_max=None,
                      WavelengthMax_min=None,
                      WavelengthMax_max=None,
                      WidthEff_min=None,
                      WidthEff_max=None,
                      FWHM_min=None,
                      FWHM_max=None,
                      Instrument=None,
                      Facility=None,
                      PhotSystem=None,
                      ID=None,
                      PhotCalID=None,
                      FORMAT=None,
                      VERB=2,
                      cache=True, timeout=None,
                      error_msg='No data found for requested query',
                      ):
        """Get data in response to the query send to SVO FPS.
        This method is not generally intended for users, but it can be helpful
        if you want something very specific from the SVO FPS service.
        If you don't know what you're doing, try `get_filter_index`,
        `get_filter_list`, and `get_transmission_data` instead.

        Description of search parameters can be found at
        https://svo2.cab.inta-csic.es/theory/fps/index.php?mode=voservice


        Parameters
        ----------
        WavelengthRef_min : float, optional
            Min value for WavelengthRef parameter
        WavelengthRef_max : float, optional
            Max value for WavelengthRef parameter
        WavelengthMean_min : float, optional
            Min value for WavelengthMean parameter
        WavelengthMean_max : float, optional
            Max value for WavelengthMean parameter
        WavelengthEff_min : float, optional
            Min value for WavelengthEff parameter
        WavelengthEff_max : float, optional
            Max value for WavelengthEff parameter
        WavelengthMin_min : float, optional
            Min value for WavelengthMin parameter
        WavelengthMin_max : float, optional
            Max value for WavelengthMin parameter
        WavelengthMax_min : float, optional
            Min value for WavelengthMax parameter
        WavelengthMax_max : float, optional
            Max value for WavelengthMax parameter
        WidthEff_min : float, optional
            Min value for WidthEff parameter
        WidthEff_max : float, optional
            Max value for WidthEff parameter
        FWHM_min : float, optional
            Min value for FWHM parameter
        FWHM_max : float, optional
            Max value for FWHM parameter
        Instrument : str, optional
            Instrument for filters (default is None). Leave empty if there are no instruments for specified facility
        Facility : str, optional
            Facility for filters (default is None)
        PhotSystem : str, optional
            Photometric system for filters (default is None)
        ID : str, optional
            Filter ID (default is None)
        PhotCalID : str, optional
            Photometric calibration ID (default is None)
        FORMAT : str, optional
            Format of the output.  Default includes all data, ``metadata`` includes only metadata.
        VERB : 0, 1, or 2
            0: The resulting VOTable won't include the transmission curve or PARAM descriptions.
            1: The resulting VOTable won't include the transmission curve but it will include PARAM descriptions.
            2: The resulting VOTable will include the transmission curve and PARAM descriptions.
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

        query = {
            'WavelengthRef_min': WavelengthRef_min,
            'WavelengthRef_max': WavelengthRef_max,
            'WavelengthMean_min': WavelengthMean_min,
            'WavelengthMean_max': WavelengthMean_max,
            'WavelengthEff_min': WavelengthEff_min,
            'WavelengthEff_max': WavelengthEff_max,
            'WavelengthMin_min': WavelengthMin_min,
            'WavelengthMin_max': WavelengthMin_max,
            'WavelengthMax_min': WavelengthMax_min,
            'WavelengthMax_max': WavelengthMax_max,
            'WidthEff_min': WidthEff_min,
            'WidthEff_max': WidthEff_max,
            'FWHM_min': FWHM_min,
            'FWHM_max': FWHM_max,
            'Instrument': Instrument,
            'Facility': Facility,
            'PhotSystem': PhotSystem,
            'ID': ID,
            'PhotCalID': PhotCalID,
            'FORMAT': FORMAT,
            'VERB': VERB
        }

        # check validity of query parameters with limited allowed values
        for key in ALLOWED_QUERY_PARAMETERS:
            if key in query and query[key] not in ALLOWED_QUERY_PARAMETERS[key]:
                raise InvalidQueryError(
                    f"Invalid value for parameter {key}. Allowed values are "
                    f"{ALLOWED_QUERY_PARAMETERS[key]}"
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
        error_msg = 'No filter found for requested Wavelength Effective range'
        try:
            return self.data_from_svo(
                WavelengthEff_min=wavelength_eff_min.to_value(u.angstrom),
                WavelengthEff_max=wavelength_eff_max.to_value(u.angstrom),
                error_msg=error_msg,
                **kwargs
            )
        except requests.ReadTimeout:
            raise TimeoutError(
                "Query did not finish fast enough. A smaller wavelength range might "
                "succeed. Try increasing the timeout limit if a large range is needed."
            )

    def get_filter_metadata(self, filter_id, *, cache=True, timeout=None, **kwargs):
        """Get metadata/parameters for the requested Filter ID from SVO

        Parameters
        ----------
        filter_id : str
            Filter ID in the format SVO specifies it: 'facilty/instrument.filter'.
            This is returned by `get_filter_list` and `get_filter_index` as the
            ``filterID`` column.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.
        timeout : int
            Timeout in seconds. If not specified, defaults to ``conf.timeout``.
        kwargs : dict
            Appended to the ``query`` dictionary sent to SVO. See the API
            documentation of `data_from_svo` for the valid parameter names.

        Returns
        -------
        params : dict
            Dictionary of VOTable PARAM names and values.
        """
        query = {'ID': filter_id, 'VERB': 0}
        query.update(kwargs)

        bad_params = [param for param in query if param not in QUERY_PARAMETERS]
        if bad_params:
            raise InvalidQueryError(
                f"parameter{'s' if len(bad_params) > 1 else ''} "
                f"{', '.join(bad_params)} {'are' if len(bad_params) > 1 else 'is'} "
                f"invalid. For a description of valid query parameters see "
                "https://svo2.cab.inta-csic.es/theory/fps/index.php?mode=voservice"
            )

        query.update(kwargs)

        bad_params = [param for param in query if param not in QUERY_PARAMETERS]
        if bad_params:
            raise InvalidQueryError(
                f"parameter{'s' if len(bad_params) > 1 else ''} "
                f"{', '.join(bad_params)} {'are' if len(bad_params) > 1 else 'is'} "
                f"invalid. For a description of valid query parameters see "
                "https://svo2.cab.inta-csic.es/theory/fps/index.php?mode=voservice"
            )

        response = self._request("GET", self.SVO_MAIN_URL, params=query,
                                 timeout=timeout or self.TIMEOUT,
                                 cache=cache)
        response.raise_for_status()
        response_content = io.BytesIO(response.content)
        votable = parse_single_table(response_content)
        params = {}
        for param in votable.iter_fields_and_params():
            if param.unit is not None:
                params[param.name] = param.value*param.unit
            else:
                params[param.name] = param.value
        return params

    def get_zeropoint(self, filter_id, *, mag_system='Vega', **kwargs):
        """
        Get the zero point for a specififed filter in a specified system.

        This is a highly-specific downselection of the metadata returned by
        `get_filter_metadata`; the full metadata includes the zero point with
        ``Vega`` as the default system.

        Parameters
        ----------
        filter_id : str
            Filter ID in the format SVO specifies it: 'facilty/instrument.filter'.
            This is returned by `get_filter_list` and `get_filter_index` as the
            ``filterID`` column.
        mag_system : str
            The magnitude system for which to return the zero point.
        kwargs : dict
            Appended to the ``query`` dictionary sent to SVO. See the API
            documentation of `data_from_svo` for the valid parameter names.

        Examples
        --------
        >>> from astroquery.svo_fps import SvoFps  # doctest: +REMOTE_DATA
        >>> SvoFps.get_zeropoint(filter_id='2MASS/2MASS.J', mag_system='AB')  # doctest: +REMOTE_DATA
        {'MagSys': 'AB',
         'ZeroPoint': <Quantity 3631. Jy>,
         'ZeroPointUnit': 'Jy',
         'ZeroPointType': 'Pogson'}
        >>> SvoFps.get_filter_metadata(filter_id='2MASS/2MASS.J', PhotCalID='2MASS/2MASS.J/AB')  # doctest: +REMOTE_DATA
        {'FilterProfileService': 'ivo://svo/fps',
         'filterID': '2MASS/2MASS.J',
         ...
         'PhotCalID': '2MASS/2MASS.J/AB',
         'MagSys': 'AB',
         'ZeroPoint': <Quantity 3631. Jy>,
         'ZeroPointUnit': 'Jy',
         'ZeroPointType': 'Pogson'}

        """
        metadata = self.get_filter_metadata(filter_id=filter_id,
                                            PhotCalID=f'{filter_id}/{mag_system}', **kwargs)

        zeropoint_keys = ['MagSys', 'ZeroPoint', 'ZeroPointUnit', 'ZeroPointType']

        zp = {key: metadata[key] for key in zeropoint_keys if key in metadata}

        return zp

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
        error_msg = 'No filter found for requested Filter ID'
        return self.data_from_svo(ID=filter_id, error_msg=error_msg, **kwargs)

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
        error_msg = 'No filter found for requested Facilty (and Instrument)'
        return self.data_from_svo(
            Facility=facility,
            Instrument=instrument,
            error_msg=error_msg,
            **kwargs
        )


SvoFps = SvoFpsClass()
