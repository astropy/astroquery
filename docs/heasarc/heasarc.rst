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

.. code-block:: python

    >>> from astroquery.heasarc import Heasarc
    >>> heasarc = Heasarc()
    >>> mission = 'rospublic'
    >>> object_name = '3c273'
    >>> table = heasarc.query_object(object_name, mission=mission)
    >>> table[:3].pprint()


Downloading identified datasets
-------------------------------

Not implemented yet.

Reference/API
=============

.. automodapi:: astroquery.heasarc
    :no-inheritance-diagram:
