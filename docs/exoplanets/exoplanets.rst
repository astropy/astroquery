.. doctest-skip-all

.. _astroquery.exoplanets:

*****************************************************
Exoplanet Parameter Queries (`astroquery.exoplanets`)
*****************************************************

Getting started
===============

The exoplanets module allows you to download (and optionally cache) the
exoplanet parameter tables from `exoplanets.org <http://www.exoplanets.org>`_ or
from NExScI's
`Exoplanet Archive <http://exoplanetarchive.ipac.caltech.edu/index.html>`_.

You can access the Exoplanet Archive parameters like so

.. code-block:: python

        >>> from astroquery.exoplanets import PlanetParams
        >>> planet = PlanetParams.from_exoplanet_archive('HD 209458 b')
        >>> planet.pl_orbper
        <Quantity 3.52474859 d>
        >>> planet.pl_orbincl
        <Quantity 86.929 deg>

or the exoplanets.org parameters like so

.. code-block:: python

        >>> from astroquery.exoplanets import PlanetParams
        >>> planet = PlanetParams.from_exoplanets_org('HD 209458 b')
        >>> planet.per
        <Quantity 3.52474859 d>
        >>> planet.tt
        <Time object: scale='utc' format='jd' value=2452826.628514>

Reference/API
=============

.. automodapi:: astroquery.exoplanets
    :no-inheritance-diagram:
