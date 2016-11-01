.. doctest-skip-all

.. _astroquery.exoplanets:

*****************************************************
Exoplanet Parameter Queries (`astroquery.exoplanets`)
*****************************************************

Accessing the tables
====================

You can access the complete tables from each table source, with units assigned
to columns wherever possible.

.. code-block:: python

        >>> from astroquery.exoplanets import ExoplanetArchive
        >>> exoplanet_archive_table = ExoplanetArchive.get_table()

        >>> exoplanet_archive_table[:2]
        <Table masked=True length=2>
        pl_hostname pl_letter pl_discmethod ... pl_nnotes rowupdate  NAME_LOWERCASE
                                            ...
           str27       str1       str29     ...   int64     str10        str29
        ----------- --------- ------------- ... --------- ---------- --------------
         Kepler-151         b       Transit ...         1 2014-05-14   kepler-151 b
         Kepler-152         b       Transit ...         1 2014-05-14   kepler-152 b

        >>> from astroquery.exoplanets import ExoplanetsOrg
        >>> exoplanets_org_table = ExoplanetsOrg.get_table()

        >>> exoplanets_org_table[:2]
        <Table masked=True length=2>
            A        AUPPER      ALOWER        UA     ... KEPID  KDE  NAME_LOWERCASE
            AU         AU          AU          AU     ...
         float64    float64     float64     float64   ... int64 int64     str20
        --------- ----------- ----------- ----------- ... ----- ----- --------------
        0.0780099  0.00130017  0.00130017  0.00130017 ...    --     1   kepler-107 d
        0.0344721 0.000675924 0.000675924 0.000675924 ...    --     1  kepler-1049 b

You can query for the row from each table corresponding to one exoplanet:

.. code-block:: python

        >>> from astroquery.exoplanets import ExoplanetsOrg
        >>> hatp11b = ExoplanetsOrg.query_planet('HAT-P-11 b')


Access a single planet's parameters
===================================

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
