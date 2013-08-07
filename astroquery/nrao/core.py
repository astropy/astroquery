# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import re
import tempfile
import warnings
import functools

import astropy.units as u
import astropy.io.votable as votable

from ..query import BaseQuery
from ..utils.class_or_instance import class_or_instance
from ..utils import commons, async_to_sync
from ..utils.docstr_chompers import prepend_docstr_noreturns

from . import  NRAO_SERVER, NRAO_TIMEOUT

__all__ = ["Nrao"]

def _validate_params(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        telescope = kwargs.get('telescope')
        telescope_config = kwargs.get('telescope_config')
        obs_band = kwargs.get('obs_band')
        sub_array = kwargs.get('sub_array')
        if telescope not in Nrao.telescope_code:
            raise ValueError("'telescope must be one of {!s}".format(Nrao.telescope_code.keys()))
        if telescope_config.upper() not in Nrao.telescope_config:
            raise ValueError("'telescope_config' must be one of {!s}".format(Nrao.telescope_config))
        if obs_band.upper() not in Nrao.obs_bands:
            raise ValueError("'obs_band' must be one of {!s}".format(Nrao.obs_bands))
        if sub_array.upper() not in Nrao.subarrays:
            raise ValueError("'sub_array' must be one of {!s}".format(Nrao.subarrays))
        return func(*args, **kwargs)
    return wrapper

@async_to_sync
class Nrao(BaseQuery):

    DATA_URL = NRAO_SERVER()
    TIMEOUT = NRAO_TIMEOUT()

    # dicts and lists for data archive queries
    telescope_code = {
        "all": "ALL",
        "jansky_vla": "EVLA",
        "historical_vla": "VLA",
        "vlba": "VLBA",
        "gbt": "GBT",
        }

    telescope_config = ['ALL', 'A', 'AB', 'BnA', 'B', 'BC', 'CnB', 'C',	'CD', 'DnC', 'D',  'DA']

    obs_bands = ['ALL', '4', 'P', 'L', 'S',  'C', 'X', 'U', 'K', 'Ka', 'Q', 'W']

    subarrays = ['ALL', 1, 2, 3, 4, 5]


    """
    @class_or_instance
    def query_region(self, coordinates, radius=1 * u.deg, equinox='J2000',
                     telescope='all', start_date="", end_date="",
                     freq_low=None, freq_up=None,
                     telescope_config='all', obs_band='all',
                     sub_array='all', verbose=False, get_query_payload=False):

        response = self.query_region_async(coordinates,
                                           radius=radius,
                                           telescope=telescope,
                                           start_date=start_date,
                                           end_date=end_date,
                                           freq_low=freq_low, freq_up=freq_up,
                                           telescope_config=telescope_config,
                                           obs_band=obs_band,
                                           sub_array=sub_array,
                                           get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result
    """


    @class_or_instance
    @_validate_params
    def _args_to_payload(self, *args, **kwargs):
        """
        Queries the NRAO data archive and fetches table of observation summaries.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the appropriate
            `astropy.coordinates` object. ICRS coordinates may also be entered
            as a string.
        radius : str or `astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The appropriate
            `Quantity` object from `astropy.units` may also be used. Defaults to 1 degree.
        equinox : str, optional
            One of 'J2000' or 'B1950'. Defaults to 'J2000'.
        telescope : str, optional
            The telescope that produced the data. Defaults to 'all'.
            Valid values are ['gbt', 'all', 'historical_vla', 'vlba', 'jansky_vla']
        start_date : str, optional
            The starting date and time of the observations , e.g. 2010-06-21 14:20:30
            Decimal seconds are not allowed. Defaults to `None` for no constraints.
        end_date :  str, optional
            The ending date and time of the observations , e.g. 2010-06-21 14:20:30
            Decimal seconds are not allowed. Defaults to `None` for no constraints.
        freq_low : `astropy.units.Quantity` object, optional
            The lower frequency of the observations in proper units of frequency
            via `astropy.units`. Defaults to `None` for no constraints.
        freq_up : `astropy.units.Quantity` object, optional
            The upper frequency of the observations in proper units of frequency
            via `astropy.units`. Defaults to `None` for no constraints.
        telescope_config : str, optional
            Select the telescope configuration (only valid for VLA array). Defaults
            to 'all'. Valid values are ['all', 'A', 'AB', 'BnA', 'B', 'BC', 'CnB', 'C',	'CD', 'DnC', 'D',  'DA']
        obs_band : str, optional
            The frequency bands for the observation. Defaults to 'all'. Valid values are
            ['all', '4', 'P', 'L', 'S',  'C', 'X', 'U', 'K', 'Ka', 'Q', 'W'].
        sub_array : str, number, optional
            VLA subarray designations, may be set to an integer from 1 to 5.
            Defaults to 'all'.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`

        Returns
        -------
        request_payload : dict
            The dictionary of parameters to send via HTTP GET request.
        """
        c = commons.parse_coordinates(args[0])
        lower_frequency = kwargs['freq_low']
        upper_frequency = kwargs['freq_up']
        if lower_frequency is not None and upper_frequency is not None:
            freq_str = str(lower_frequency.to(u.MHz).value)+'-'+str(upper_frequency.to(u.MHz).value)
        else:
            freq_str = ""
        request_payload = dict(QUERYTYPE="OBSSUMMARY",
                               PROTOCOL="VOTable-XML",
                               MAX_ROWS="NO LIMIT",
                               SORT_PARM="Starttime",
                               SORT_ORDER="Asc",
                               SORT_PARM2="Starttime",
                               SORT_ORDER2="Asc",
                               QUERY_ID=9999,
                               QUERY_MODE="AAT_TOOL",
                               LOCKMODE="PROJECT",
                               SITE_CODE="AOC",
                               DBHOST="CHEWBACCA",
                               WRITELOG=0,
                               TELESCOPE=Nrao.telescope_code[kwargs['telescope']],
                               PROJECT_CODE="",
                               SEGMENT="",
                               TIMERANGE1=kwargs['start_date'],
                               OBSERVER="",
                               ARCHIVE_VOLUME="",
                               TIMERANGE2=kwargs['end_date'],
                               CENTER_RA = str(c.icrs.ra.degree) + 'd',
                               CENTER_DEC = str(c.icrs.dec.degree) + 'd',
                               EQUINOX=kwargs['equinox'],
                               SRAD=str(commons.parse_radius(kwargs['radius']).degree) + 'd',
                               TELESCOPE_CONFIG='ALL' if kwargs['telescope_config'] == 'all' else  kwargs['telescope_config'],
                               OBS_BANDS=kwargs['obs_band'].upper(),
                               SUBARRAY='ALL' if kwargs['sub_array'] == 'all' else kwargs['sub_array'],
                               OBSFREQ1=freq_str,
                               OBS_POLAR="ALL",
                               RECEIVER_ID="ALL",
                               BACKEND_ID="ALL",
                               SUBMIT="Submit Query")
        return request_payload

    @class_or_instance
    @prepend_docstr_noreturns(_args_to_payload.__doc__)
    def query_region_async(self, coordinates, radius=1 * u.deg, equinox='J2000',
                           telescope='all', start_date="", end_date="",
                           freq_low=None, freq_up=None,
                           telescope_config='all', obs_band='all',
                           sub_array='all', get_query_payload=False):
        """
        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """

        request_payload = self._args_to_payload(coordinates,
                                               radius=radius,
                                               equinox=equinox,
                                               telescope=telescope,
                                               start_date=start_date,
                                               end_date=end_date,
                                               freq_low=freq_low, freq_up=freq_up,
                                               telescope_config=telescope_config,
                                               obs_band=obs_band,
                                               sub_array=sub_array)
        if get_query_payload:
            return request_payload
        response = commons.send_request(Nrao.DATA_URL, request_payload, Nrao.TIMEOUT, request_type='GET')
        return response


    @class_or_instance
    def _parse_result(self, response, verbose=False):
        if not verbose:
            commons.suppress_vo_warnings()
        # fix to replace non standard datatype 'integer' in returned VOTable
        # with 'int' to make it parsable by astropy.io.votable
        integer_re = re.compile(r'datatype="integer"')
        new_content = integer_re.sub(r'datatype="int"', response.content)
        try:
            tf = tempfile.NamedTemporaryFile()
            tf.write(new_content.encode('utf-8'))
            tf.flush()
            first_table = votable.parse(tf.name, pedantic=False).get_first_table()
            table = first_table.to_table(use_names_over_ids=True)
            return table
        except Exception as ex:
            print (str(ex))
            warnings.warn("Error in parsing Ned result. "
                 "Returning raw result instead.")
            return response.content
