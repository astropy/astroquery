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
    >>> table = heasarc.query_position(coords, mission=mission)
    >>> table[:3].pprint()

Note that the `query_position` converts the passed coordinates to FK5 internally
before making submitting the query.

Modifying returned table columns
--------------------------------

Each table has a set of default columns that are returned when submitting to the
database. You can return all available columns for a given query by specifying
the `fields` parameter in either of the above queries. For exampe:

.. code-block:: python

    >>> table = heasarc.query_object(object_name='3c273', mission='rospublic', fields='All')

will return all available columns from the 'rospublic' mission table.
Alternatively, a comma-separated list of column names can also be provided to
specify which columns will be returned:

.. code-block:: python

    >>> table = heasarc.query_object(object_name='3c273', mission='rospublic', fields='SEQ_ID,RA,BII')

To obtain a list of all available columns for a given mission table, do the 
following:

.. code-block:: python

    >>> cols = heasarc.query_mission_cols(mission='rospublic')
    >>> print(cols)

Getting list of available missions
----------------------------------

.. code-block:: python
    
    >>> from astroquery.heasarc import Heasarc
    >>> heasarc = Heasarc()
    >>> missions = heasarc.query_mission_list()
    >>> missions.pprint()

This will store a list of available missions that can be queried in the
`missions` object. This includes a list of both the names and descriptions of
each mission.

Downloading identified datasets
-------------------------------

Not implemented yet.

Reference/API
=============

.. automodapi:: astroquery.heasarc
    :no-inheritance-diagram:
