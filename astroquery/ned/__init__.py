# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
NED Query Tool
==============

Module containing a series of functions that execute queries to the NASA Extragalactic Database (NED):

.. topic:: Revision History

    Refactored using common API as a part of Google Summer of Code 2013.

    :Originally contributed by:

     K. Willett, Jun 2011

    :Acknowledgements:

        Based off Adam Ginsburg's Splatalogue search routine:
            http://code.google.com/p/agpy/source/browse/trunk/agpy/query_splatalogue.py

        Service URLs to acquire the VO Tables are taken from Mazzarella et al. (2007)
        The National Virtual Observatory: Tools and Techniques for Astronomical Research,
        ASP Conference Series, Vol. 382., p.165

"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.ned`.
    """
    server = _config.ConfigItem(
        'http://ned.ipac.caltech.edu/cgi-bin/',
        'Name of the NED server to use.'
        )
    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to NED server.'
        )

    # Set input parameters of choice

    hubble_constant = _config.ConfigItem(
        [73, 70.5],
        'Value of the Hubble Constant for many NED queries.'
        )

    """
    The correct redshift for NED queries may be chosen by specifying numbers
    1, 2, 3 and 4, having the following meanings:
    (1) To the Reference Frame defined by the 3K CMB
    (2) To the Reference Frame defined by the Virgo Infall only
    (3) To the Reference Frame defined by the (Virgo + GA) only
    (4) To the Reference Frame defined by the (Virgo + GA + Shapley)
    """
    correct_redshift = _config.ConfigItem(
        defaultvalue=1,
        description='The correct redshift for NED queries, see comments above..',
        #cfgtype=[1, 2, 3, 4],
        )

    # Set output parameters of choice
    output_coordinate_frame = _config.ConfigItem(
        defaultvalue='Equatorial',
        description='Frame in which to display the coordinates in the output.',
        #cfgtype=['Equatorial', 'Ecliptic', 'Galactic', 'SuperGalactic']
        )
    output_equinox = _config.ConfigItem(
        defaultvalue='J2000.0',
        description='Equinox for the output coordinates.',
        #['J2000.0', 'B1950.0'],
        )
    sort_output_by = _config.ConfigItem(
        defaultvalue="RA or Longitude",
        description='Display output sorted by this criteria.',
        #["RA or Longitude",
        # "DEC or Latitude",
        # "GLON",
        # "GLAT",
        # "Redshift - ascending",
        # "Redshift - descending"],
        )

conf = Conf()

from .core import Ned, NedClass

__all__ = ['Ned', 'NedClass',
           'Conf', 'conf',
           ]
