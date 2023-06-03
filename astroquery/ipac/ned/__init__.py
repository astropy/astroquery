# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
NED Query Tool
==============

Module containing a series of functions that execute queries to the NASA
Extragalactic Database (NED):

.. topic:: Revision History

    Refactored using common API as a part of Google Summer of Code 2013.

    :Originally contributed by:

     K. Willett, Jun 2011

    :Acknowledgements:

        Based off Adam Ginsburg's Splatalogue search routine:
            https://github.com/keflavich/agpy/blob/master/agpy/query_splatalogue.py

        Service URLs to acquire the VO Tables are taken from Mazzarella et
        al. (2007) The National Virtual Observatory: Tools and Techniques
        for Astronomical Research, ASP Conference Series, Vol. 382., p.165

"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.ipac.ned`.
    """
    server = _config.ConfigItem(
        ['https://ned.ipac.caltech.edu/cgi-bin/'],
        'Name of the NED server to use.')

    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to NED server.')

    # Set input parameters of choice

    hubble_constant = _config.ConfigItem(
        [73, 70.5],
        'Value of the Hubble Constant for many NED queries.')

    """
    The correct redshift for NED queries may be chosen by specifying numbers
    1, 2, 3 and 4, having the following meanings:
    (1) To the Reference Frame defined by the 3K CMB
    (2) To the Reference Frame defined by the Virgo Infall only
    (3) To the Reference Frame defined by the (Virgo + GA) only
    (4) To the Reference Frame defined by the (Virgo + GA + Shapley)
    """
    correct_redshift = _config.ConfigItem(
        [1, 2, 3, 4],
        'The correct redshift for NED queries, see comments above.')

    # Set output parameters of choice
    output_coordinate_frame = _config.ConfigItem(
        ['Equatorial',
         'Ecliptic',
         'Galactic',
         'SuperGalactic'],
        'Frame in which to display the coordinates in the output.')

    output_equinox = _config.ConfigItem(
        ['J2000.0', 'B1950.0'],
        'Equinox for the output coordinates.')

    sort_output_by = _config.ConfigItem(
        ["RA or Longitude",
         "DEC or Latitude",
         "GLON",
         "GLAT",
         "Redshift - ascending",
         "Redshift - descending"],
        'Display output sorted by this criteria.')


conf = Conf()

from .core import Ned, NedClass

__all__ = ['Ned', 'NedClass', 'Conf', 'conf']
