import astropy
from astropy import units
from astropy.table import Table, MaskedColumn

import numpy as np

import json

from ..query import BaseQuery
from ..utils.class_or_instance import class_or_instance
from ..utils import async_to_sync
from . import conf

__all__ = ['Observations', 'ObservationsClass']  # specifies what to import

@async_to_sync
class ObservationsClass(BaseQuery):

    server = conf.server

    def __init__(self, *args):
        """ set some parameters """
        # do login here
        super().__init__()

    @class_or_instance
    def query_region(self, coordinates, radius=0.3*units.deg):
        response = self.query_region_async(coordinates=coordinates, radius=radius)
        js = json.loads(response.text)
        return _gemini_json_to_table(js)

    @class_or_instance
    def query_region_async(self, coordinates, radius=0.3*units.deg):

        # request_payload = self._args_to_payload(*args)
        if isinstance(radius, (int, float)):
            radius = radius * units.deg
        radius = astropy.coordinates.Angle(radius)

        url = "%s/jsonsummary/notengineering/NotFail" % self.server
        if coordinates is not None:
            url = "%s/ra=%f/dec=%f" % (url, coordinates.ra.deg, coordinates.dec.deg)
        if radius is not None:
            url = "%s/sr=%fd" % (url, radius.deg)
        response = self._request(method="GET", url=url, data={}, timeout=180, cache=False)

        return response

    # @class_or_instance
    # def get_images_async(self, *args):
    #     image_urls = self.get_image_list(*args)
    #     return [get_readable_fileobj(U) for U in image_urls]
    #     # get_readable_fileobj returns need a "get_data()" method?
    #
    # @class_or_instance
    # def get_image_list(self, *args):
    #
    #     request_payload = self._args_to_payload(*args)
    #
    #     response = self._request(method="POST", url=self.server,
    #                              data=request_payload, timeout=TIMEOUT)
    #
    #     return self.extract_image_urls(response.text)
    #
    # def _parse_result(self, result):
    #     # do something, probably with regexp's
    #     return astropy.table.Table(tabular_data)
    #
    # def _args_to_payload(self, *args):
    #     # convert arguments to a valid requests payload
    #
    #     return dict


def _gemini_json_to_table(json):
    """
    Takes a JSON object as returned from a Mashup request and turns it into an `~astropy.table.Table`.

    Parameters
    ----------
    json_obj : dict
        A Mashup response JSON object (python dictionary)
    col_config : dict, optional
        Dictionary that defines column properties, e.g. default value.

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

