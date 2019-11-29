"""
Search functionality for the Gemini archive of observations.

For questions, contact ooberdorf@gemini.edu
"""

from datetime import date

import warnings

import astropy
from astropy import units
from astropy.table import Table, MaskedColumn
from astropy.utils.exceptions import AstropyUserWarning
from ..utils import commons
import numpy as np

import json

from ..query import BaseQuery
from ..utils.class_or_instance import class_or_instance
from ..utils import async_to_sync
from . import conf

__all__ = ['Observations', 'ObservationsClass']  # specifies what to import


__valid_instruments__ = [
    'GMOS',
    'GMOS-N',
    'GMOS-S',
    'GNIRS',
    'GRACES',
    'NIRI',
    'NIFS',
    'GSAOI',
    'F2',
    'GPI',
    'NICI',
    'MICHELLE',
    'TRECS',
    'BHROS',
    'HRWFS',
    'OSCIR',
    'FLAMINGOS',
    'HOKUPAA+QUIRC',
    'PHOENIX',
    'TEXES',
    'ABU',
    'CIRPASS'
]


__valid_observation_class__ = [
    'science',
    'acq',
    'progCal',
    'dayCal',
    'partnerCal',
    'acqCal',
]

__valid_observation_types__ = [
    'OBJECT',
    'BIAS',
    'DARK',
    'FLAT',
    'ARC',
    'PINHOLE',
    'RONCHI',
    'CAL',
    'FRINGE',
    'MASK'
]

__valid_modes__ = [
    'imaging',
    'spectroscopy',
    'LS',
    'MOS',
    'IFS'
]

__valid_adaptive_optics__ = [
    'NOTAO',
    'AO',
    'NGS',
    'LGS'
]

__valid_raw_reduced__ = [
    'RAW',
    'PREPARED',
    'PROCESSED_BIAS',
    'PROCESSED_FLAT',
    'PROCESSED_FRINGE',
    'PROCESSED_ARC'
]


class ObservationsClass(BaseQuery):

    server = conf.server

    def __init__(self, *args):
        """ set some parameters """
        # do login here
        super().__init__()

    @class_or_instance
    def query_region(self, coordinates, radius):
        """
        search for Gemini observations by target on the sky.

        Given a sky position and radius, returns a list of Gemini observations.

        Parameters
        ----------
        coordinates : str or `~astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `~astropy.coordinates` object.
        radius : str or `~astropy.units.Quantity` object, optional
            Default 0.3 degrees.
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used. Defaults to 0.3 deg.

        Returns
        -------
        response : `~astropy.table.Table`
        """
        return self.query_criteria(coordinates=coordinates, radius=radius)


    @class_or_instance
    def query_object(self, objectname):
        """
        search for Gemini observations by target on the sky.

        Given a sky position and radius, returns a list of Gemini observations.

        Parameters
        ----------
        coordinates : str or `~astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `~astropy.coordinates` object.
        radius : str or `~astropy.units.Quantity` object, optional
            Default 0.3 degrees.
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used. Defaults to 0.3 deg.

        Returns
        -------
        response : `~astropy.table.Table`
        """
        return self.query_criteria(objectname=objectname)


    @class_or_instance
    def query_criteria(self, coordinates=None, radius=None, pi_name=None, program_id=None, utc_date=None,
                       instrument=None, observation_class=None, observation_type=None, mode=None,
                       adaptive_optics=None, program_text=None, objectname=None, raw_reduced=None):
        """
        search a variety of known parameters against the Gemini observations.

        Given various criteria, search the Gemini archive for matching observations.

        Parameters
        ----------
        coordinates : str or `~astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `~astropy.coordinates` object.
        radius : str or `~astropy.units.Quantity` object, optional
            Default 0.3 degrees.
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used. Defaults to 0.3 deg.
        pi_name : str, optional
            Default None.
            Can be used to search for data by the PI's name.
        program_id : str, optional
            Default None.
            Can be used to match on program ID
        utc_date : date or (date,date) tuple, optional
            Default None.
            Can be used to search for observations on a particular day or range of days (inclusive).
        instrument : str, optional
            Can be used to search for a particular instrument.  Valid values are:
                'GMOS',
                'GMOS-N',
                'GMOS-S',
                'GNIRS',
                'GRACES',
                'NIRI',
                'NIFS',
                'GSAOI',
                'F2',
                'GPI',
                'NICI',
                'MICHELLE',
                'TRECS',
                'BHROS',
                'HRWFS',
                'OSCIR',
                'FLAMINGOS',
                'HOKUPAA+QUIRC',
                'PHOENIX',
                'TEXES',
                'ABU',
                'CIRPASS'
        observation_class : str, optional
            Specifies the class of observations to search for.  Valid values are:
                'science',
                'acq',
                'progCal',
                'dayCal',
                'partnerCal',
                'acqCal'
        observation_type : str, optional
            Search for a particular type of observation.  Valid values are:
                'OBJECT',
                'BIAS',
                'DARK',
                'FLAT',
                'ARC',
                'PINHOLE',
                'RONCHI',
                'CAL',
                'FRINGE',
                'MASK'
        mode : str, optional
            The mode of the observation.  Valid values are:
                'imaging',
                'spectroscopy',
                'LS',
                'MOS',
                'IFS'
        adaptive_optics : str, optional
            Specify the presence of adaptive optics.  Valid values are:
                'NOTAO',
                'AO',
                'NGS',
                'LGS'
        program_text : str, optional
            Specify text in the information about the program.  This is free form text.
        objectname : str, optional
            Give the name of the target.
        raw_reduced : str, optional
            Indicate the raw or reduced status of the observations to search for.  Valid values are:
                'RAW',
                'PREPARED',
                'PROCESSED_BIAS',
                'PROCESSED_FLAT',
                'PROCESSED_FRINGE',
                'PROCESSED_ARC'

        Returns
        -------
        response : `~astropy.table.Table`
        """

        # This could be refactored to rely on query_raw, but I am not convinced
        # that is a good long-term approach.  I prefer the clarity of keeping
        # this as an independent implementation.
        if radius is not None:
            if isinstance(radius, (int, float)):
                radius = radius * units.deg
            radius = astropy.coordinates.Angle(radius)

        url = "%s/jsonsummary/notengineering/NotFail" % self.server
        if coordinates is not None:
            coordinates = commons.parse_coordinates(coordinates)
            url = "%s/ra=%f/dec=%f" % (url, coordinates.ra.deg, coordinates.dec.deg)
        if radius is not None:
            url = "%s/sr=%fd" % (url, radius.deg)
        if pi_name is not None:
            url = "%s/PIname=%s" % (url, pi_name)
        if program_id is not None:
            url = "%s/progid=%s" % (url, program_id.upper())
        if utc_date is not None:
            if isinstance(utc_date, date):
                url = "%s/%s" % (url, utc_date.strftime("YYYYMMdd"))
            elif isinstance(utc_date, tuple):
                if len(utc_date) != 2:
                    raise ValueError("utc_date tuple should have two values")
                if not isinstance(utc_date[0], date) or not isinstance(utc_date[1], date):
                    raise ValueError("utc_date tuple should have date values in it")
                url = "%s/%s-%s" % (url, utc_date[0].strftime("YYYYMMdd"), utc_date[1].strftime("YYYYMMdd"))
        if instrument is not None:
            if instrument.upper() not in __valid_instruments__:
                raise ValueError("Unrecognized instrument: %s" % instrument)
            url = "%s/%s" % (url, instrument)
        if observation_class is not None:
            if observation_class not in __valid_observation_class__:
                raise ValueError("Unrecognized observation class: %s" % observation_class)
            url = "%s/%s" % (url, observation_class)
        if observation_type is not None:
            if observation_type not in __valid_observation_types__:
                raise ValueError("Unrecognized observation type: %s" % observation_type)
            url = "%s/%s" % (url, observation_type)
        if mode is not None:
            if mode not in __valid_modes__:
                raise ValueError("Unrecognized mode: %s" % mode)
            url = "%s/%s" % mode
        if adaptive_optics is not None:
            if adaptive_optics not in __valid_adaptive_optics__:
                raise ValueError("Unrecognized adaptive optics: %s" % adaptive_optics)
            url = "%s/%s" % (url, adaptive_optics)
        if program_text is not None:
            url = "%s/ProgramText=%s" % (url, program_text)
        if objectname is not None:
            url = "%s/object=%s" % (url, objectname)
        if raw_reduced is not None:
            if raw_reduced not in __valid_raw_reduced__:
                raise ValueError("Unrecognized raw/reduced setting: %s" % raw_reduced)
            url = "%s/%s" % (url, raw_reduced)
        response = self._request(method="GET", url=url, data={}, timeout=180, cache=False)

        js = json.loads(response.text)
        return _gemini_json_to_table(js)


    @class_or_instance
    def query_raw(self, *args, **kwargs):
        """
        perform flexible query against Gemini observations

        This is a more flexible query method.  This method will do special handling for
        coordinates and radius if present in kwargs.  However, for the remaining arguments
        it assumes all of args are useable as query path elements.  For kwargs, it assumes
        all of the elements can be passed as name=value within the query path to Gemini.

        This method does not do any validation checking or attempt to interperet the
        values being passed, aside from coordinates and radius.

        This method is most useful when the query_criteria and query_region do not
        meet your needs and you can build the appropriate search in the website.  When
        you see the URL that is generated by the archive, you can translate that into
        an equivalent python call with this method.  For example, if the URL in the
        website is:

        https://archive.gemini.edu/searchform/RAW/cols=CTOWEQ/notengineering/GMOS-N/PIname=Hirst/NotFail
        
        You can disregard NotFail, cols=x and notengineering.  You would run this query as

        query_raw('GMOS-N', PIname='Hirst')

        Parameters
        ----------
        args : 
            The list of parameters to be passed via the query path to the webserver
        kwargs :
            The dictionary of parameters to be passed by name=value within the query 
            path to the webserver

        Returns
        -------
        response : `~astropy.table.Table`
        """
        if 'radius' in kwargs:
            radius = kwargs['radius']
        else:
            radius = None
        if radius is not None:
            if isinstance(radius, (int, float)):
                radius = radius * units.deg
            radius = astropy.coordinates.Angle(radius)
        if 'coordinates' in kwargs:
            coordinates = kwargs['coordinates']
            coordinates = commons.parse_coordinates(coordinates)
        else:
            coordinates = None
        
        if coordinates is not None:
            url = "%s/ra=%f/dec=%f" % (url, coordinates.ra.deg, coordinates.dec.deg)
        if radius is not None:
            url = "%s/sr=%fd" % (url, radius.deg)

        url = "%s/jsonsummary/notengineering/NotFail" % self.server
        for arg in args:
            url = "%s/%s" % (url, arg)
        for key in filter(lambda key: key not in ["coordinates", "radius"], kwargs):
            url = "%s/%s=%s" % (url, key, kwargs[key])

        response = self._request(method="GET", url=url, data={}, timeout=180, cache=False)

        js = json.loads(response.text)
        return _gemini_json_to_table(js)


def _gemini_json_to_table(json):
    """
    takes a JSON object as returned from the Gemini archive webserver and turns it into an `~astropy.table.Table`

    Parameters
    ----------
    json : dict
        A JSON object from the Gemini archive webserver

    Returns
    -------
    response : `~astropy.table.Table`
    """

    data_table = Table(masked=True)

    for key in __keys__:
        col_data = np.array([obj.get(key) for obj in json])

        atype = str

        col_mask = np.equal(col_data, None)
        data_table.add_column(MaskedColumn(col_data.astype(atype), name=key, mask=col_mask))

    return data_table


__keys__ = ["exposure_time",
        "detector_roi_setting",
        "detector_welldepth_setting",
        "telescope",
        "mdready",
        "requested_bg",
        "engineering",
        "cass_rotator_pa",
        "ut_datetime",
        "file_size",
        "types",
        "requested_wv",
        "detector_readspeed_setting",
        "size",
        "laser_guide_star",
        "observation_id",
        "science_verification",
        "raw_cc",
        "filename",
        "instrument",
        "reduction",
        "camera",
        "ra",
        "detector_binning",
        "lastmod",
        "wavelength_band",
        "data_size",
        "mode",
        "raw_iq",
        "airmass",
        "elevation",
        "data_label",
        "requested_iq",
        "object",
        "requested_cc",
        "program_id",
        "file_md5",
        "central_wavelength",
        "raw_wv",
        "compressed",
        "filter_name",
        "detector_gain_setting",
        "path",
        "observation_class",
        "qa_state",
        "observation_type",
        "calibration_program",
        "md5",
        "adaptive_optics",
        "name",
        "focal_plane_mask",
        "data_md5",
        "raw_bg",
        "disperser",
        "wavefront_sensor",
        "gcal_lamp",
        "detector_readmode_setting",
        "phot_standard",
        "local_time",
        "spectroscopy",
        "azimuth",
        "release",
        "dec"]

Observations = ObservationsClass()

