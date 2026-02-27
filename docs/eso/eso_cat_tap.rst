*****************************
Catalogues - Query with TAP
*****************************

The ESO TAP service can also be used to query catalogue tables directly with
free ADQL, using :meth:`~astroquery.eso.EsoClass.query_tap`. By default,
``query_tap(query)`` targets the observations TAP service (equivalent to
``which_tap="tap_obs"``). To query catalogue content, pass
``which_tap="tap_cat"`` -- i.e. ``eso.query_tap(query, which_tap="tap_cat")``.

Basic Usage
===========

.. doctest-skip::

    >>> from astroquery.eso import Eso
    >>> eso = Eso()
    >>> query = "SELECT table_name FROM TAP_SCHEMA.tables"
    >>> table = eso.query_tap(query, which_tap="tap_cat")

The examples below focus on common catalogue TAP workflows: schema discovery,
spatial filtering, metadata-driven joins, and light-curve retrieval.

Schema Discovery Examples
=========================

List Release Documentation URLs for Available Catalogues
--------------------------------------------------------

This example shows how to retrieve the release documentation URL for each
published catalogue directly from ``TAP_SCHEMA.tables``. For example, for the ``AMBRE_V1`` 
catalogue, the corresponding release documentation can be found at:
https://www.eso.org/rm/api/v1/public/releaseDescriptions/7

.. doctest-skip::

    >>> query = """
    ... SELECT table_name, cat_id, rel_descr_url
    ... FROM TAP_SCHEMA.tables
    ... WHERE schema_name = 'safcat' AND cat_id IS NOT NULL
    ... ORDER BY cat_id
    ... """
    >>> table = eso.query_tap(query, which_tap="tap_cat")
    >>> print(table[:2])
    table_name       cat_id                  release_documentation_url
    ---------------- ------ -----------------------------------------------------------
    AMBRE_V1             13 https://www.eso.org/rm/api/v1/public/releaseDescriptions/7
    GOODS_FORS2_V1       31 https://www.eso.org/rm/api/v1/public/releaseDescriptions/37

Inspect Columns in a Specific Catalogue Table
---------------------------------------------

Use this to list columns and data types for a specific catalogue table.
``TAP_SCHEMA.columns`` contains column names, units, UCDs, and additional
metadata for all published ESO tables.

.. doctest-skip::

    >>> query = """
    ... SELECT column_name, datatype, unit, ucd
    ... FROM TAP_SCHEMA.columns
    ... WHERE table_name='COSMOS2015_Laigle_v1_1b_latestV7_fits_V1'
    ... """
    >>> table = eso.query_tap(query, which_tap="tap_cat")

Find the Main RA/Dec Columns via UCD
------------------------------------

Use this to identify which columns carry the main sky coordinates in a table.
Here, the UCD values mark the primary ``RA`` and ``Dec`` fields -- in this case 
``TRANSIENT_RAJ2000`` and ``TRANSIENT_DECJ2000``.

.. doctest-skip::

    >>> query = """
    ... SELECT column_name
    ... FROM TAP_SCHEMA.columns
    ... WHERE table_name='PESSTO_TRAN_CAT_fits_V2'
    ...   AND (ucd = 'pos.eq.ra;meta.main' OR ucd = 'pos.eq.dec;meta.main')
    ... """
    >>> table = eso.query_tap(query, which_tap="tap_cat")

List VMC Tables with Coordinate and Source-ID Columns
-----------------------------------------------------

Use this to list coordinate and source-ID columns for all tables in the ``VMC``
collection, ordered by publication date.

.. doctest-skip::

    >>> query = """
    ... SELECT publication_date, T.table_name, column_name, ucd
    ... FROM TAP_SCHEMA.columns AS C, TAP_SCHEMA.tables AS T
    ... WHERE T.table_name = C.table_name
    ...   AND cat_id IN (
    ...       SELECT cat_id
    ...       FROM TAP_SCHEMA.tables
    ...       WHERE collection='VMC'
    ...   )
    ...   AND (
    ...       ucd = 'pos.eq.ra;meta.main'
    ...       OR ucd = 'pos.eq.dec;meta.main'
    ...       OR ucd = 'meta.id;meta.main'
    ...   )
    ... ORDER BY publication_date DESC, 2, 4
    ... """
    >>> table = eso.query_tap(query, which_tap="tap_cat")

List Coordinate and Source-ID Columns Across All Collections
------------------------------------------------------------

Use this to discover coordinate and source-ID columns across all published
catalogues, ordered by publication date and collection.

.. doctest-skip::

    >>> query = """
    ... SELECT publication_date, collection, T.table_name, column_name, ucd
    ... FROM TAP_SCHEMA.columns AS C, TAP_SCHEMA.tables AS T
    ... WHERE T.table_name = C.table_name
    ...   AND (
    ...       ucd = 'pos.eq.ra;meta.main'
    ...       OR ucd = 'pos.eq.dec;meta.main'
    ...       OR ucd = 'meta.id;meta.main'
    ...   )
    ... ORDER BY publication_date DESC, 2, 3, 5
    ... """
    >>> table = eso.query_tap(query, which_tap="tap_cat")

Spatial Query Example
=====================

Cone Search for PESSTO Transients Around ESO 154-10
---------------------------------------------------

Search the PESSTO master catalogue for transients in a circle of ``0.04 deg``
(``2.4 arcmin``) around galaxy ``ESO 154-10`` (ICRS position
``41.2863, -55.7406``).

.. doctest-skip::

    >>> query = """
    ... SELECT host_id, transient_id, transient_classification,
    ...        transient_raj2000, transient_decj2000
    ... FROM pessto_tran_cat_fits_V2
    ... WHERE CONTAINS(
    ...     POINT('', transient_raj2000, transient_decj2000),
    ...     CIRCLE('', 41.2863, -55.7406, 0.04)
    ... ) = 1
    ... """
    >>> table = eso.query_tap(query, which_tap="tap_cat")

The target coordinates can also be resolved online using a name resolver and then included in 
the query, as e.g.: 

.. doctest-skip::

    >>> import astropy.units as u
    >>> from astropy.coordinates import SkyCoord

    >>> target = SkyCoord.from_name("ESO 154-10")  
    >>> ra_deg = target.icrs.ra.to_value(u.deg)
    >>> dec_deg = target.icrs.dec.to_value(u.deg)
    >>> radius_deg = (2.4 * u.arcmin).to_value(u.deg)  

    >>> query = f"""
    ... SELECT host_id, transient_id, transient_classification,
    ...        transient_raj2000, transient_decj2000
    ... FROM pessto_tran_cat_fits_V2
    ... WHERE CONTAINS(
    ...     POINT('ICRS', transient_raj2000, transient_decj2000),
    ...     CIRCLE('ICRS', {ra_deg}, {dec_deg}, {radius_deg})
    ... ) = 1
    ... """
    >>> table = eso.query_tap(query, which_tap="tap_cat")

Metadata Join Example
=====================

Discover Join Keys for VVV Tables
---------------------------------

Use this to discover how ``VVV_CAT_V2`` can be joined with related ``VVV*`` tables.
This pattern is common for multi-epoch catalogue products: one source can have
many epoch-level measurements, so the measurement table may contain ``N`` rows
for the same object. In those cases, coordinates are often stored only in a
source/master table and not repeated ``N`` times in each epoch table. This
reduces duplication and helps avoid inconsistencies across tables.

The VVV catalogues are a representative example: ``VVV_CAT_V2`` provides the
source-level identifiers and coordinates, while tables such as
``VVV_MPHOT_Ks_V2`` (multi-epoch photometry) and ``VVV_VAR_V2`` (variability
metrics) are linked through source keys (e.g. ``SOURCEID``).

The resulting table shows join pairs as:

- ``from_table`` via ``from_column``
- ``target_table`` via ``target_column``

.. doctest-skip::

    >>> query = """
    ... SELECT k.from_table, kc.from_column, k.target_table, kc.target_column
    ... FROM TAP_SCHEMA.columns AS c, TAP_SCHEMA.keys AS k, TAP_SCHEMA.key_columns AS kc
    ... WHERE c.table_name='VVV_CAT_V2'
    ...   AND (
    ...       (k.from_table = c.table_name AND kc.from_column = c.column_name)
    ...       OR
    ...       (k.target_table = c.table_name AND kc.target_column = c.column_name)
    ...   )
    ...   AND k.key_id = kc.key_id
    ... ORDER BY table_name, column_name, 1, 3, 2
    ... """
    >>> table = eso.query_tap(query, which_tap="tap_cat")

After identifying the join keys (here, linking ``VVV_CAT_V2`` to
``VVV_MPHOT_Ks_V2`` and ``VVV_VAR_V2``), you can build a light curve while
keeping spatial constraints anchored to the master source table (see below).

Light-Curve Query Examples
==========================

Get a VVV Source Light Curve and Variability Metrics
----------------------------------------------------

Retrieve multi-epoch photometry and variability metrics for a known VVV source.

.. doctest-skip::

    >>> query = """
    ... SELECT TOP 10 VVV.IAUNAME, VVV.SOURCEID, VVV.RA2000, VVV.DEC2000,
    ...               M.MJD, M.KSMAG, M.KSERR,
    ...               V.KSMEANMAG, V.KSAMPL, KSPROBVAR
    ... FROM VVV_CAT_V2 AS VVV
    ... JOIN VVV_MPHOT_Ks_V2 AS M ON VVV.SOURCEID = M.SOURCEID
    ... JOIN VVV_VAR_V2 AS V ON VVV.SOURCEID = V.SOURCEID
    ... WHERE VVV.IAUNAME='VVV J135433.73-594836.43'
    ... ORDER BY 1, 5
    ... """
    >>> table = eso.query_tap(query, which_tap="tap_cat")

In this query:

- ``VVV`` is the VVV master catalogue alias.
- ``M`` is the multi-epoch photometry table alias.
- ``V`` is the variability table alias.


Get PESSTO Light-Curve Magnitudes in a Sky Region
-------------------------------------------------

Retrieve selected magnitudes from the PESSTO light-curve catalogue for
transients within ``0.05 deg`` (``3 arcmin``) around ESO 154-10.

.. doctest-skip::

    >>> query = """
    ... SELECT host_id, transient_id, transient_classification,
    ...        lc.B_VEGA_MAG, lc.B_VEGA_MAGERR,
    ...        lc.R_AB_MAG, lc.R_AB_MAGERR,
    ...        lc.R_VEGA_MAG, lc.R_VEGA_MAGERR
    ... FROM safcat.PESSTO_TRAN_CAT_V3 AS master
    ... JOIN safcat.PESSTO_MPHOT_V3 AS lc ON lc.SOURCE_ID = master.TRANSIENT_ID
    ... WHERE CONTAINS(
    ...     POINT('', transient_raj2000, transient_decj2000),
    ...     CIRCLE('', 41.2863, -55.7406, 0.05)
    ... ) = 1
    ... ORDER BY transient_id
    ... """
    >>> table = eso.query_tap(query, which_tap="tap_cat")

The light-curve table does not provide coordinates directly, so it is joined to
the PESSTO master catalogue for spatial filtering. To retrieve all available
magnitude columns instead of only ``B`` and ``R``, use ``lc.*`` in the
``SELECT`` clause.

This can also be done using a name resolver for the target coordinates, as previously shown above.

.. doctest-skip::

    >>> import astropy.units as u
    >>> from astropy.coordinates import SkyCoord

    >>> target = SkyCoord.from_name("ESO 154-10") 
    >>> ra_deg = target.icrs.ra.to_value(u.deg)
    >>> dec_deg = target.icrs.dec.to_value(u.deg)
    >>> radius_deg = (3 * u.arcmin).to_value(u.deg)  

    >>> query = f"""
    ... SELECT host_id, transient_id, transient_classification,
    ...        lc.B_VEGA_MAG, lc.B_VEGA_MAGERR,
    ...        lc.R_AB_MAG, lc.R_AB_MAGERR,
    ...        lc.R_VEGA_MAG, lc.R_VEGA_MAGERR
    ... FROM safcat.PESSTO_TRAN_CAT_V3 AS master
    ... JOIN safcat.PESSTO_MPHOT_V3 AS lc ON lc.SOURCE_ID = master.TRANSIENT_ID
    ... WHERE CONTAINS(
    ...     POINT('', transient_raj2000, transient_decj2000),
    ...     CIRCLE('', {ra_deg}, {dec_deg}, {radius_deg})
    ... ) = 1
    ... ORDER BY transient_id
    ... """
    >>> table = eso.query_tap(query, which_tap="tap_cat")
