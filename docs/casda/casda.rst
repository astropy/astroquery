.. doctest-skip-all

.. _astroquery.casda:

**********************************
CASDA Queries (`astroquery.casda`)
**********************************

The CSIRO ASKAP Science Data Archive (CASDA) provides access to science-ready data products
from observations at the `Australian Square Kilometre Array Pathfinder (ASKAP) <https://www.atnf.csiro.au/projects/askap/index.html>`_ telescope.
These data products include source catalogues, images, spectral line and polarisation cubes, spectra and visbilities.
This package allows querying of the data products available in CASDA (`<https://casda.csiro.au/>`_).

Listing Data Products
=====================

The metadata for data products held in CASDA may be queried using the :meth:`~astroquery.casda.CasdaClass.query_region` method.
The results are returned in a `~astropy.table.Table`.
The method takes a location and either a radius or a height and width of the region to be queried.
The location should be specified in ICRS coordinates or an `astropy.coordinates.SkyCoord` object.
For example:

.. code-block:: python

    >>> from astroquery.casda import Casda
    >>> from astropy.coordinates import SkyCoord
    >>> from astropy import units as u
    >>> centre = SkyCoord.from_name('NGC 7232')
    >>> result_table = Casda.query_region(centre, radius=30*u.arcmin)
    >>> print(result_table['obs_publisher_did','s_ra', 's_dec', 'released_date'])
    obs_publisher_did       s_ra           s_dec            released_date
                            deg             deg
    ----------------- --------------- ---------------- ------------------------
             cube-502 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-503 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-504 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-505 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-506 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-507 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-508 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-453 332.53629746595 -44.850153699406 2017-07-10T05:18:13.482Z
             cube-454 332.53629746595 -44.850153699406 2017-07-10T05:18:13.482Z
             cube-455 332.53629746595 -44.850153699406 2017-07-10T05:18:13.482Z
                  ...             ...              ...                      ...
             cube-468 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
             cube-469 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
             cube-470 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
             cube-471 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
             cube-472 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
             cube-473 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
            cube-1170 333.70448386919 -45.966341151806 2019-01-30T13:00:00.000Z
             cube-612 333.30189344648 -50.033321773361 2018-05-25T08:22:51.025Z
             cube-650 326.04487794126 -42.033324601808 2018-05-25T08:22:51.025Z
             cube-651 335.54487794126 -42.033324601808 2018-05-25T08:22:51.025Z
    Length = 121 rows


Reference/API
=============

.. automodapi:: astroquery.casda
    :no-inheritance-diagram:

.. _IAU format: http://cdsweb.u-strasbg.fr/Dic/iau-spec.html.
