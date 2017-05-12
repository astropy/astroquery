# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Las Cumbres Observatory public archive Query Tool
=================================================

This module contains various methods for querying
Las Cumbres Observatory data archive.
"""
from astropy import config as _config

class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.lco`.
    """

    _base_path = 'https://archive-api.lco.global'

    server = _config.ConfigItem(
        _base_path,
        'Las Cumbres Observatory archive API base URL')

    aggregate = _config.ConfigItem(
        _base_path + '/aggregate/',
        'Returns the unique values shared across all fits files for site, telescope, instrument, filter and obstype.')

    get_token = _config.ConfigItem(
        _base_path + '/api-token-auth/',
        'Obtain an api token for use with authenticated requests.')

    frames = _config.ConfigItem(
        _base_path + '/frames/',
        'Return a list of frames.')

    frame = _config.ConfigItem(
        _base_path + '/frames/{id}/',
        'Return a single frame.')

    frames_related = _config.ConfigItem(
        _base_path + '/frames/{id}/related/',
        'Return a list of frames related to this frame (calibration frames, catalogs, etc).')

    frames_headers = _config.ConfigItem(
        _base_path + '/frames/{id}/headers/',
        'Return the headers for a single frame.')

    frames_zip = _config.ConfigItem(
        _base_path + '/frames/zip/',
        "Returns a zip file containing all of the requested frames. Note this is not the preferred method for downloading files. Use the frame's url property instead.")

    profile = _config.ConfigItem(
        _base_path + '/profile/',
        'Returns information about the currently authenticated user.')

    row_limit = _config.ConfigItem(
        10,
        'Maximum number of rows to retrieve in result')

    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to the Las Cumbres Observatory archive')

    username = _config.ConfigItem(
        "",
        'Optional default username for Las Cumbres Observatory archive.')

    dtypes = _config.ConfigItem(
            ['i','str','str','str','str','str','str','str','str','f','str','str'],
            "NumPy data types for archive response")

    names  = _config.ConfigItem(
            ['id','filename','url','RLEVEL','DATE_OBS','PROPID','OBJECT','SITEID','TELID','EXPTIME','FILTER','REQNUM'],
            "Archive response items")


conf = Conf()


from .core import Lco, LcoClass

__all__ = ['Lco', 'LcoClass',
           'Conf', 'conf',
           ]
