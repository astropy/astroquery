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
        >>> planet.coord
        <SkyCoord (ICRS): (ra, dec) in deg
            (330.794891, 18.884319)>

or the exoplanets.org parameters like so

.. code-block:: python

        >>> from astroquery.exoplanets import PlanetParams
        >>> planet = PlanetParams.from_exoplanets_org('HD 209458 b')
        >>> planet.per
        <Quantity 3.52474859 d>
        >>> planet.tt
        <Time object: scale='utc' format='jd' value=2452826.628514>
        >>> planet.coord
        <SkyCoord (ICRS): (ra, dec) in deg
            (330.79479167, 18.88436389)>

The common attributes on the `~astroquery.exoplanets.PlanetParams` object from
either source include ``name`` and ``coord`` (which returns a
`~astropy.coordinates.SkyCoord` object).

Reference/API
=============

.. automodapi:: astroquery.exoplanets
    :no-inheritance-diagram:
