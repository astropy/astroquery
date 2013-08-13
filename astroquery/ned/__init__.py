# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
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

from astropy.config import ConfigurationItem
NED_SERVER = ConfigurationItem('ned_server', ['http://ned.ipac.caltech.edu/cgi-bin/'],
                               'Name of the NED mirror to use.')

NED_TIMEOUT = ConfigurationItem('timeout', 60, 'time limit for connecting to NED server')


# Set input parameters of choice
HUBBLE_CONSTANT = ConfigurationItem('hubble_constant', [73, 70.5], 'value of the Hubble Constant for many NED queries.')

"""
The correct redshift for NED queries may be chosen by specifying numbers 1, 2, 3 and 4, having the following meanings
(1) To the Reference Frame defined by the 3K CMB
(2) To the Reference Frame defined by the Virgo Infall only
(3) To the Reference Frame defined by the (Virgo + GA) only
(4) To the Reference Frame defined by the (Virgo + GA + Shapley)
"""
CORRECT_REDSHIFT = ConfigurationItem('correct_redshift', [1, 2, 3, 4], 'the correct redshift for NED queries, see comments above.')

# Set output parameters of choice
OUTPUT_COORDINATE_FRAME = ConfigurationItem('output_coordinate_frame',
                                            ['Equatorial',
                                             'Ecliptic',
                                             'Galactic',
                                             'SuperGalactic'], 'Frame in which to display the coordinates in the output.')

OUTPUT_EQUINOX = ConfigurationItem('output_equinox', ['J2000.0', 'B1950.0'], 'Equinox for the output coordinates.')
SORT_OUTPUT_BY = ConfigurationItem('sort_output_by',
                                   ["RA or Longitude",
                                    "DEC or Latitude",
                                    "GLON",
                                    "GLAT",
                                    "Redshift - ascending",
                                    "Redshift - descending"], 'display output sorted by this criteria.')

from .core import Ned

__all__ = ['Ned']
