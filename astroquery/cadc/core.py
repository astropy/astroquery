# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

# put all imports organized as shown below
# 1. standard library imports

# 2. third party imports
from astropy.coordinates import SkyCoord

# 3. local imports - use relative imports
# commonly required local imports shown below as example
# all Query classes should inherit from BaseQuery.
from ..query import BaseQuery
# has common functions required by most modules
from ..utils import commons
# prepend_docstr is a way to copy docstrings between methods
from ..utils import prepend_docstr_noreturns
# async_to_sync generates the relevant query tools from _async methods
from ..utils import async_to_sync
# import configurable items declared in __init__.py
from . import conf
from ..utils.tap import Tap



# export all the public classes and methods
__all__ = ['Cadc', 'CadcClass']

# declare global variables and constants if any
# default fields by the query methods
DEFAULT_FIELDS = ['Observation.collection AS "Collection"',
                 'Observation.observationID AS "Obs. ID"',
                 'COORD1(CENTROID(Plane.position_bounds)) AS "RA (J2000.0)"',
                 'COORD2(CENTROID(Plane.position_bounds)) AS "Dec. (J2000.0)"',
                 'Plane.time_bounds_lower AS "Start Date"',
                 'Observation.instrument_name AS "Instrument"',
                 'Plane.time_exposure AS "Int. Time"',
                 'Observation.target_name AS "Target Name"',
                 'Plane.energy_bandpassName AS "Filter"',
                 'Plane.calibrationLevel AS "Cal. Lev."',
                 'Observation.type AS "Obs. Type"']

CADC_TABLES = 'caom2.Plane AS Plane JOIN caom2.Observation AS Observation ON Plane.obsID = Observation.obsID'

QUALITY_CONSTRAINT = '( Plane.quality_flag IS NULL OR Plane.quality_flag != \'junk\' )'


# Now begin your main class
# should be decorated with the async_to_sync imported previously
@async_to_sync
class CadcClass(BaseQuery):

    SERVER = conf.server
    TIMEOUT = conf.timeout

    def __init__(self):
        self.__cadctap = Tap(url='{}/tap'.format(CadcClass.SERVER))
        self.fields = DEFAULT_FIELDS

    def query_region(self, coordinates, radius):
        """
        Perform a query based on a region

        :returns results of the query in astropy table format
        """
        coordinates = self.__getCoordInput(coordinates, 'Region coordinates')
        query = ('SELECT {} FROM {} WHERE {} AND '
                 '( INTERSECTS( CIRCLE(\'ICRS\', {}, {}, {}), '
                 'Plane.position_bounds ) = 1 )'.format(', '.join(self.fields),
                                                       CADC_TABLES, QUALITY_CONSTRAINT,
                                                       coordinates.ra.value, coordinates.dec.value, radius))
        job = self.__cadctap.launch_job(query, verbose=True )
        return job.get_results()


    def query_target(self, target_name):
        """
        Perform a query based on name of the target

        :returns results of the query in astropy table format
        """
        query = ('SELECT {} FROM {} WHERE {} AND '
                 '( lower(Observation.target_name) = \'{}\' )'.format(', '.join(self.fields),
                                                       CADC_TABLES, QUALITY_CONSTRAINT, target_name.lower()))
        job = self.__cadctap.launch_job(query, verbose=True)
        return job.get_results()


    def __checkCoordInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value, SkyCoord)):
            raise ValueError(
                str(msg) + " must be either a string or astropy.coordinates")


    def __getCoordInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value, SkyCoord)):
            raise ValueError(
                str(msg) + " must be either a string or astropy.coordinates")
        if isinstance(value, str):
            c = commons.parse_coordinates(value)
            return c
        else:
            return value

    def load_tables(self, verbose=False):
        """Loads all public tables from the CADC TAP Web service
        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        Returns
        -------
        A list of table objects
        """
        return self.__cadctap.load_tables()

# the default tool for users to interact with is an instance of the Class
Cadc = CadcClass()

# once your class is done, tests should be written
# See ./tests for examples on this

# Next you should write the docs in astroquery/docs/module_name
# using Sphinx.
