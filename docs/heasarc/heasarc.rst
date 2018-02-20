.. doctest-skip-all

.. _astroquery.heasarc:

**************************************
HEASARC Queries (`astroquery.heasarc`)
**************************************

Getting started
===============

This is a python interface for querying the
`HEASARC <http://heasarc.gsfc.nasa.gov/>`__
archive web service.

The capabilities are currently very limited ... feature requests and contributions welcome!

Getting lists of available datasets
-----------------------------------

There are two ways to obtain a list of objects. The first is by querying around
an object by name:

.. code-block:: python

    >>> from astroquery.heasarc import Heasarc
    >>> heasarc = Heasarc()
    >>> mission = 'rospublic'
    >>> object_name = '3c273'
    >>> table = heasarc.query_object(object_name, mission=mission)
    >>> table[:3].pprint()

Alternatively, a query can also be conducted around a specific set of sky
coordinates:

.. code-block:: python

    >>> from astroquery.heasarc import Heasarc
    >>> from astropy.coordinates import SkyCoord
    >>> heasarc = Heasarc()
    >>> mission = 'rospublic'
    >>> coords = SkyCoord('12h29m06.70s +02d03m08.7s', frame='icrs')
    >>> table = heasarc.query_position(coords, mission=mission, radius='1 degree')
    >>> table[:3].pprint()

Note that the `query_position` converts the passed coordinates to the FK5
reference frame before submitting the query.

Modifying returned table columns
--------------------------------

Each table has a set of default columns that are returned when querying the
database. You can return all available columns for a given mission by specifying
the ``fields`` parameter in either of the above queries. For exampe:

.. code-block:: python

    >>> table = heasarc.query_object(object_name='3c273', mission='rospublic', fields='All')

will return all available columns from the ``rospublic`` mission table.
Alternatively, a comma-separated list of column names can also be provided to
specify which columns will be returned:

.. code-block:: python

    >>> table = heasarc.query_object(object_name='3c273', mission='rospublic', fields='EXPOSURE,RA,DEC')

Note that the ``SEARCH_OFFSET_`` column will always be included in the results.
If a column name is passed to the ``fields`` parameter which does not exist in
the requested mission table, the query will fail. To obtain a list of available 
columns for a given mission table, do the following:

.. code-block:: python

    >>> cols = heasarc.query_mission_cols(mission='rospublic')
    >>> print(cols)
    
Additional query parameters
---------------------------

By default, the ``query_object()`` method returns all entries within approximately 
one degree of the specified object. This can be modified by supplying the 
``radius`` parameter. This parameter takes a distance to look for objects. The 
following modifies the search radius to 120 arcmin:

.. code-block:: python

    >>> from astroquery.heasarc import Heasarc
    >>> heasarc = Heasarc()
    >>> table = heasarc.query_object(object_name, mission='rospublic', radius='120 arcmin')

``radius`` takes an angular distance specified as an astropy Quantity object, 
or a string that can be parsed into one (e.g., '1 degree' or 1*u.degree). The
following are equivalent:

.. code-block:: python

    >>> table = heasarc.query_object(object_name, mission='rospublic', radius='120 arcmin')
    >>> table = heasarc.query_object(object_name, mission='rospublic', radius='2 degree')
    >>> from astropy import units as u
    >>> table = heasarc.query_object(object_name, mission='rospublic', radius=120*u.arcmin)
    >>> table = heasarc.query_object(object_name, mission='rospublic', radius=2*u.degree)

As per the astroquery specifications, the ``query_region()`` method requires the 
user to supply the radius parameter.

The results can also be sorted by the value in a given column using the ``sortvar``
parameter. The following sorts the results by the value in the 'EXPOSURE' column.

.. code-block:: python

    >>> table = heasarc.query_object(object_name, mission='rospublic', sortvar='EXPOSURE')

Setting the ``resultmax`` parameter controls the maximum number of results to be
returned. The following will store only the first 10 results:

.. code-block:: python

    >>> table = heasarc.query_object(object_name, mission='rospublic', resultmax=10)

All of the above parameters can be mixed and matched to refine the query results.

Getting list of available missions
----------------------------------

The ``query_mission_list()`` method will return a list of available missions 
that can be queried.

.. code-block:: python
    
    >>> from astroquery.heasarc import Heasarc
    >>> heasarc = Heasarc()
    >>> table = heasarc.query_mission_list()
    >>> table.pprint()

The returned table includes both the names and a short description of each 
mission table.

Downloading identified datasets
-------------------------------

Not implemented yet.

Reference/API
=============

.. automodapi:: astroquery.heasarc
    :no-inheritance-diagram:
