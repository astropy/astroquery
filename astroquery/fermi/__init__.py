# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Access to Fermi Gamma-ray Space Telescope data.

https://fermi.gsfc.nasa.gov
https://fermi.gsfc.nasa.gov/ssc/data/

As of 2026, the Fermi LAT Data Server exposes a JSON REST API.  This module
targets that API; the legacy ``LATDataQuery.cgi`` HTML-scraping path has been
removed.
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.fermi`.
    """

    url = _config.ConfigItem(
        'https://fermi.gsfc.nasa.gov/ssc/data/access/lat/query/api/v1',
        'Base URL of the Fermi LAT Data Query REST API. Endpoints '
        '(/query, /query/{id}/status, /query/{id}/results) are appended to it.')
    file_base_url = _config.ConfigItem(
        # NOTE: the results endpoint returns bare filenames; download URLs are
        # reconstructed against this staging area. Currently a /test/ path -
        # revisit if the staging location changes at production cutover.
        'https://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/test/queries/',
        'Base URL under which query result files are staged.')
    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to the Fermi server.')
    retrieval_timeout = _config.ConfigItem(
        120,
        'Time limit for retrieving a data file once it has been located.')


conf = Conf()

from .core import FermiLAT, FermiLATClass, GetFermilatDatafile, get_fermilat_datafile  # noqa: E402

__all__ = ['FermiLAT', 'FermiLATClass',
           'GetFermilatDatafile', 'get_fermilat_datafile',
           'Conf', 'conf',
           ]
