# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
HSC-SSP Catalog Query Tool
-------------------------
Module for accessing the Hyper Suprime-Cam Subaru Strategic Program database.

:author: Angel Ruiz (angel.ruizca@gmail.com)
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.hsc`.
    """
    api_server = _config.ConfigItem(
        ['https://hsc-release.mtk.nao.ac.jp/datasearch/api/catalog_jobs/'],
        'Name of the HSC server to use (database API).')

    download_server = _config.ConfigItem(
        ['https://hsc-release.mtk.nao.ac.jp/datasearch/catalog_jobs/download/'],
        'Name of the HSC server to use (database downloads).')

    cutout_server = _config.ConfigItem(
        ['https://hsc-release.mtk.nao.ac.jp/das_quarry/cgi-bin/quarryImage'],
        'Name of the HSC server to use (cut-outs).')

    image_server = _config.ConfigItem(
        ['https://hsc-release.mtk.nao.ac.jp/das_search/'],
        'Name of the HSC server to use (image search).')

    archive_server = _config.ConfigItem(
        ['https://hsc-release.mtk.nao.ac.jp/archive/filetree/'],
        'Name of the HSC server to use (image archive).')

    timeout = _config.ConfigItem(
        300,
        'Time limit for connecting to HSC server.')


conf = Conf()

# Now import your public class
# Should probably have the same name as your module
from .core import Hsc, HscClass

__all__ = ['Hsc', 'HscClass',
           'Conf', 'conf',
           ]
