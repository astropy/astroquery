import requests
import io

from astropy import units as u
from astropy.io.votable import parse_single_table
# The VOTables fetched from SVO contain only single table element, thus parse_single_table

from . import conf

from ..query import BaseQuery
from astroquery.exceptions import InvalidQueryError, TimeoutError


__all__ = ['SvoFpsClass', 'SvoFps']


# Parameters the SVO service accepts as either ``Name`` (base) or as a
# range pair ``Name_min``/``Name_max``.
RANGE_BASES = {"wavelength_ref", "wavelength_mean", "wavelength_eff",
               "wavelength_min", "wavelength_max", "width_eff", "fwhm"}

# Base mapping from public (snake_case, lowercase) keyword names to the
# CamelCase parameter names the SVO FPS server actually accepts.  The SVO
# service is case-sensitive: lowercase parameters silently fall through
# (the server returns the full unfiltered response), so every value sent
# in a query must come from this mapping.  See
# https://svo2.cab.inta-csic.es/theory/fps/index.php?mode=voservice
BASE_PARAM_NAMES = {
    "wavelength_ref": "WavelengthRef",
    "wavelength_mean": "WavelengthMean",
    "wavelength_eff": "WavelengthEff",
    "wavelength_min": "WavelengthMin",
    "wavelength_max": "WavelengthMax",
    "width_eff": "WidthEff",
    "fwhm": "FWHM",
    "instrument": "Instrument",
    "facility": "Facility",
    "phot_system": "PhotSystem",
    "id": "ID",
    "phot_cal_id": "PhotCalID",
    "format": "FORMAT",
    "verb": "VERB",
}

# Full mapping including the range variants, so a single dict lookup
# resolves any user-facing kwarg.
SVO_PARAM_NAMES = {
    **BASE_PARAM_NAMES,
    **{f"{k}_min": f"{v}_min"
       for k, v in BASE_PARAM_NAMES.items() if k in RANGE_BASES},
    **{f"{k}_max": f"{v}_max"
       for k, v in BASE_PARAM_NAMES.items() if k in RANGE_BASES},
}

# Set of every valid public keyword name (used to validate **kwargs
# passed to ``get_filter_metadata``).
QUERY_PARAMETERS = set(SVO_PARAM_NAMES)

ALLOWED_QUERY_PARAMETERS = {
    "verb": {0, 1, 2},
    "format": {"metadata", None}
}


def to_svo_query(local_params):
    """Translate a dict of public (snake_case) kwargs to the SVO native
    parameter names the server expects.  ``None`` values are dropped so
    they aren't sent over the wire."""
    return {SVO_PARAM_NAMES[k]: v for k, v in local_params.items()
            if v is not None}


class SvoFpsClass(BaseQuery):
    """
    Class for querying the Spanish Virtual Observatory filter profile service
    """
    SVO_MAIN_URL = conf.base_url
    TIMEOUT = conf.timeout

    def data_from_svo(self,
                      *,
                      wavelength_ref_min=None,
                      wavelength_ref_max=None,
                      wavelength_mean_min=None,
                      wavelength_mean_max=None,
                      wavelength_eff_min=None,
                      wavelength_eff_max=None,
                      wavelength_min_min=None,
                      wavelength_min_max=None,
                      wavelength_max_min=None,
                      wavelength_max_max=None,
                      width_eff_min=None,
                      width_eff_max=None,
                      fwhm_min=None,
                      fwhm_max=None,
                      instrument=None,
                      facility=None,
                      phot_system=None,
                      id=None,
                      phot_cal_id=None,
                      format=None,
                      verb=2,
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
        wavelength_ref_min : float, optional
            Min value for WavelengthRef parameter
        wavelength_ref_max : float, optional
            Max value for WavelengthRef parameter
        wavelength_mean_min : float, optional
            Min value for WavelengthMean parameter
        wavelength_mean_max : float, optional
            Max value for WavelengthMean parameter
        wavelength_eff_min : float, optional
            Min value for WavelengthEff parameter
        wavelength_eff_max : float, optional
            Max value for WavelengthEff parameter
        wavelength_min_min : float, optional
            Min value for WavelengthMin parameter
        wavelength_min_max : float, optional
            Max value for WavelengthMin parameter
        wavelength_max_min : float, optional
            Min value for WavelengthMax parameter
        wavelength_max_max : float, optional
            Max value for WavelengthMax parameter
        width_eff_min : float, optional
            Min value for WidthEff parameter
        width_eff_max : float, optional
            Max value for WidthEff parameter
        fwhm_min : float, optional
            Min value for FWHM parameter
        fwhm_max : float, optional
            Max value for FWHM parameter
        instrument : str, optional
            Instrument for filters (default is None). Leave empty if there are no instruments for specified facility
        facility : str, optional
            Facility for filters (default is None)
        phot_system : str, optional
            Photometric system for filters (default is None)
        id : str, optional
            Filter ID (default is None)
        phot_cal_id : str, optional
            Photometric calibration ID (default is None)
        format : str, optional
            Format of the output.  Default includes all data, ``metadata`` includes only metadata.
        verb : 0, 1, or 2
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

        local_params = {
            'wavelength_ref_min': wavelength_ref_min,
            'wavelength_ref_max': wavelength_ref_max,
            'wavelength_mean_min': wavelength_mean_min,
            'wavelength_mean_max': wavelength_mean_max,
            'wavelength_eff_min': wavelength_eff_min,
            'wavelength_eff_max': wavelength_eff_max,
            'wavelength_min_min': wavelength_min_min,
            'wavelength_min_max': wavelength_min_max,
            'wavelength_max_min': wavelength_max_min,
            'wavelength_max_max': wavelength_max_max,
            'width_eff_min': width_eff_min,
            'width_eff_max': width_eff_max,
            'fwhm_min': fwhm_min,
            'fwhm_max': fwhm_max,
            'instrument': instrument,
            'facility': facility,
            'phot_system': phot_system,
            'id': id,
            'phot_cal_id': phot_cal_id,
            'format': format,
            'verb': verb,
        }

        # check validity of query parameters with limited allowed values
        for key in ALLOWED_QUERY_PARAMETERS:
            if key in local_params and local_params[key] not in ALLOWED_QUERY_PARAMETERS[key]:
                raise InvalidQueryError(
                    f"Invalid value for parameter {key}. Allowed values are "
                    f"{ALLOWED_QUERY_PARAMETERS[key]}"
                )

        query = to_svo_query(local_params)
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
                wavelength_eff_min=wavelength_eff_min.to_value(u.angstrom),
                wavelength_eff_max=wavelength_eff_max.to_value(u.angstrom),
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
        local_params = {'id': filter_id, 'verb': 0}
        local_params.update(kwargs)

        bad_params = [param for param in local_params if param not in QUERY_PARAMETERS]
        if bad_params:
            raise InvalidQueryError(
                f"parameter{'s' if len(bad_params) > 1 else ''} "
                f"{', '.join(bad_params)} {'are' if len(bad_params) > 1 else 'is'} "
                f"invalid. For a description of valid query parameters see the docstring for SvoFps.data_from_svo"
            )

        query = to_svo_query(local_params)
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
        mag_system : 'Vega' (default), 'AB', or 'ST'
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
        """
        if mag_system not in ['Vega', 'AB', 'ST']:
            raise InvalidQueryError("Invalid magnitude system. Allowed values are 'Vega', 'AB', and 'ST'.")

        metadata = self.get_filter_metadata(filter_id=filter_id,
                                            phot_cal_id=f'{filter_id}/{mag_system}', **kwargs)

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
        return self.data_from_svo(id=filter_id, error_msg=error_msg, **kwargs)

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
            facility=facility,
            instrument=instrument,
            error_msg=error_msg,
            **kwargs
        )


SvoFps = SvoFpsClass()
