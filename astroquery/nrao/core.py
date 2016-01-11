# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import re
import warnings
import functools

import astropy.units as u
import astropy.io.votable as votable
from astropy import coordinates
from astropy.extern import six

from ..query import BaseQuery
from ..utils import commons, async_to_sync
from ..utils.docstr_chompers import prepend_docstr_noreturns
from ..exceptions import TableParseError

from . import conf

__all__ = ["Nrao", "NraoClass"]


def _validate_params(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        telescope = kwargs.get('telescope', 'all')
        telescope_config = kwargs.get('telescope_config', 'all')
        obs_band = kwargs.get('obs_band', 'all')
        sub_array = kwargs.get('sub_array', 'all')
        if telescope not in Nrao.telescope_code:
            raise ValueError("'telescope must be one of {!s}"
                             .format(Nrao.telescope_code.keys()))
        if telescope_config.upper() not in Nrao.telescope_config:
            raise ValueError("'telescope_config' must be one of {!s}"
                             .format(Nrao.telescope_config))
        if obs_band.upper() not in Nrao.obs_bands:
            raise ValueError("'obs_band' must be one of {!s}"
                             .format(Nrao.obs_bands))
        if sub_array not in Nrao.subarrays and sub_array != 'all':
            raise ValueError("'sub_array' must be one of {!s}"
                             .format(Nrao.subarrays))
        return func(*args, **kwargs)
    return wrapper


@async_to_sync
class NraoClass(BaseQuery):

    DATA_URL = conf.server
    TIMEOUT = conf.timeout

    # dicts and lists for data archive queries
    telescope_code = {
        "all": "ALL",
        "jansky_vla": "EVLA",
        "historical_vla": "VLA",
        "vlba": "VLBA",
        "gbt": "GBT",
    }

    telescope_config = ['ALL', 'A', 'AB', 'BnA', 'B', 'BC', 'CnB', 'C',
                        'CD', 'DnC', 'D', 'DA']

    obs_bands = ['ALL', '4', 'P', 'L', 'S', 'C', 'X', 'U', 'K', 'Ka', 'Q', 'W']

    subarrays = ['ALL', 1, 2, 3, 4, 5]

    @_validate_params
    def _args_to_payload(self, **kwargs):
        """
        Queries the NRAO data archive and fetches table of observation
        summaries.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as a string.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `Quantity` object from `astropy.units` may also be
            used. Defaults to 1 arcminute.
        equinox : str, optional
            One of 'J2000' or 'B1950'. Defaults to 'J2000'.
        telescope : str, optional
            The telescope that produced the data. Defaults to 'all'. Valid
            values are:
            ['gbt', 'all', 'historical_vla', 'vlba', 'jansky_vla']

        start_date : str, optional
            The starting date and time of the observations , e.g. 2010-06-21
            14:20:30 Decimal seconds are not allowed. Defaults to `None` for
            no constraints.
        end_date :  str, optional
            The ending date and time of the observations , e.g. 2010-06-21
            14:20:30 Decimal seconds are not allowed. Defaults to `None` for
            no constraints.
        freq_low : `~astropy.units.Quantity` object, optional
            The lower frequency of the observations in proper units of
            frequency via `astropy.units`. Defaults to `None` for no
            constraints.
        freq_up : `~astropy.units.Quantity` object, optional
            The upper frequency of the observations in proper units of
            frequency via `astropy.units`. Defaults to `None` for no
            constraints.
        telescope_config : str, optional
            Select the telescope configuration (only valid for VLA
            array). Defaults to 'all'. Valid values are ['all', 'A', 'AB',
            'BnA', 'B', 'BC', 'CnB', 'C', 'CD', 'DnC', 'D', 'DA']
        obs_band : str, optional
            The frequency bands for the observation. Defaults to
            'all'. Valid values are ['all', '4', 'P', 'L', 'S', 'C', 'X',
            'U', 'K', 'Ka', 'Q', 'W'].
        sub_array : str, number, optional
            VLA subarray designations, may be set to an integer from 1 to 5.
            Defaults to 'all'.
        project_code : str, optional
            A string indicating the project code.  Examples::

                * GBT: AGBT12A_055
                * JVLA: 12A-256

        querytype : str
            The type of query to perform.  "OBSSUMMARY" is the default, but
            it is only valid for VLA/VLBA observations.  ARCHIVE will not
            work at all because it relies on XML data.  OBSERVATION will
            provide full details of the sources observed and under what
            configurations.
        source_id : str, optional
            A source name (to be parsed by SIMBAD or NED)
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`

        Returns
        -------
        request_payload : dict
            The dictionary of parameters to send via HTTP GET request.
        """
        lower_frequency = kwargs.get('freq_low', None)
        upper_frequency = kwargs.get('freq_up', None)
        if lower_frequency is not None and upper_frequency is not None:
            freq_str = (str(lower_frequency.to(u.MHz).value) + '-' +
                        str(upper_frequency.to(u.MHz).value))
        else:
            freq_str = ""

        request_payload = dict(
            QUERYTYPE=kwargs.get('querytype', "OBSSUMMARY"),
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
            TELESCOPE=Nrao.telescope_code[kwargs.get('telescope', 'all')],
            PROJECT_CODE=kwargs.get('project_code', ''),
            SEGMENT="",
            MIN_EXPOSURE='',
            TIMERANGE1=kwargs.get('start_date', ''),
            OBSERVER="",
            ARCHIVE_VOLUME="",
            TIMERANGE2=kwargs.get('end_date', ''),
            EQUINOX=kwargs.get('equinox', 'J2000'),
            CENTER_RA='',
            CENTER_DEC='',
            SRAD=str(
                commons.parse_radius(kwargs.get('radius', "1.0m")).deg) + 'd',
            TELESCOPE_CONFIG=kwargs.get('telescope_config', 'all').upper(),
            OBS_BANDS=kwargs.get('obs_band', 'all').upper(),
            SUBARRAY=kwargs.get('subarray', 'all').upper(),
            SOURCE_ID=kwargs.get('source_id', ''),
            SRC_SEARCH_TYPE='SIMBAD or NED',
            OBSFREQ1=freq_str,
            OBS_POLAR="ALL",
            RECEIVER_ID="ALL",
            BACKEND_ID="ALL",
            DATATYPE="ALL",
            PASSWD="",  # TODO: implement login...
            SUBMIT="Submit Query")

        if 'coordinates' in kwargs:
            c = commons.parse_coordinates(
                kwargs['coordinates']).transform_to(coordinates.ICRS)
            request_payload['CENTER_RA'] = str(c.ra.degree) + 'd'
            request_payload['CENTER_DEC'] = str(c.dec.degree) + 'd'

        return request_payload

    @prepend_docstr_noreturns(_args_to_payload.__doc__)
    def query_async(self,
                    get_query_payload=False,
                    cache=True,
                    **kwargs):
        """
        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """

        request_payload = self._args_to_payload(**kwargs)

        if get_query_payload:
            return request_payload
        response = self._request('POST', self.DATA_URL, params=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        return response

    @prepend_docstr_noreturns(_args_to_payload.__doc__)
    def query_region_async(self, coordinates, radius=1 * u.deg,
                           equinox='J2000', telescope='all', start_date="",
                           end_date="", freq_low=None, freq_up=None,
                           telescope_config='all', obs_band='all',
                           sub_array='all', get_query_payload=False):
        """
        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """

        return self.query_async(coordinates=coordinates,
                                radius=radius,
                                equinox=equinox,
                                telescope=telescope,
                                start_date=start_date,
                                end_date=end_date,
                                freq_low=freq_low,
                                freq_up=freq_up,
                                telescope_config=telescope_config,
                                obs_band=obs_band,
                                sub_array=sub_array,
                                get_query_payload=get_query_payload)

    def _parse_result(self, response, verbose=False):
        if not verbose:
            commons.suppress_vo_warnings()

        new_content = response.text

        # these are pretty bad hacks, but also needed...
        days_re = re.compile(r'unit="days"  datatype="double"')
        new_content = days_re.sub(r'unit="days"  datatype="char" '
                                  'arraysize="*"', new_content)
        degrees_re = re.compile(r'unit="degrees"  datatype="double"')
        new_content = degrees_re.sub(r'unit="degrees"  datatype="char" '
                                     'arraysize="*"', new_content)
        telconfig_re = re.compile(r'datatype="char"  name="Telescope:config"')
        new_content = telconfig_re.sub(r'datatype="unicodeChar" '
                                       'name="Telescope:config" '
                                       ' arraysize="*" ', new_content)

        datatype_mapping = {'integer': 'long'}

        try:
            tf = six.BytesIO(new_content.encode())
            first_table = votable.parse(
                tf, pedantic=False,
                datatype_mapping=datatype_mapping).get_first_table()
            try:
                table = first_table.to_table(use_names_over_ids=True)
            except TypeError:
                warnings.warn("NRAO table parsing: astropy versions prior "
                              "to 6558975c use the table column IDs instead "
                              "of names.")
                table = first_table.to_table()
            return table
        except Exception as ex:
            self.response = response
            self.table_parse_error = ex
            raise TableParseError("Failed to parse NRAO votable result! The "
                                  "raw response can be found in self.response,"
                                  " and the error in self.table_parse_error.")

Nrao = NraoClass()
