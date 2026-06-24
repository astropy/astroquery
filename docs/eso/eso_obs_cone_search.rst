
**************************
Observations - Cone Search 
**************************

In the simplest case, archive queries can be performed using a positional
(cone) search, which returns all data products within a given angular radius
around a specified sky position. This approach is particularly useful when
searching for reduced (Phase 3) data products around well-known targets or
regions on the sky.

.. note:: 
    This is typically done within the ``astroquery`` using the ``query_region`` or ``query_object`` methods. However, these methods are not yet implemented for ``astroquery.eso``. Instead, cone searches can be performed by passing the appropriate parameters to the existing query methods, such as :meth:`~astroquery.eso.EsoClass.query_surveys`, :meth:`~astroquery.eso.EsoClass.query_instrument`, and :meth:`~astroquery.eso.EsoClass.query_main`.

Query for Reduced Data
======================

This example demonstrates how to perform a basic cone search for publicly available **HAWK-I reduced data products** around the Galactic Center (Sgr A\*) using :meth:`~astroquery.eso.EsoClass.query_surveys`. Sgr A\* is located at right ascension 266.41683° and declination –29.00781°. We perform a search within a 0.05-degree radius (~3 arcminutes).

.. doctest-remote-data::

    >>> import astropy.units as u 
    >>> ra = 266.41683 *u.deg # degrees
    >>> dec = -29.00781 *u.deg # degrees
    >>> radius = 0.05 *u.deg # degrees

If coordinates are not known, you can use the :class:`~astropy.coordinates.SkyCoord` class to create them. Here, we create a SkyCoord object for Sgr A\*.

.. doctest-remote-data::

    >>> from astropy.coordinates import SkyCoord  
    >>> coords = SkyCoord.from_name("Sgr A*") 
    >>> ra = coords.ra
    >>> dec = coords.dec
    >>> radius = 0.05 *u.deg 

With the defined coordinates and radius, we can now perform the cone search using :meth:`~astroquery.eso.EsoClass.query_surveys`. This method allows us to filter results based on specific columns, such as ``instrument_name``.

.. doctest-remote-data::

    >>> from astroquery.eso import Eso
    >>> eso = Eso()

.. doctest-remote-data::

    >>> table = eso.query_surveys(
    ...             cone_ra=ra.value,
    ...             cone_dec=dec.value,
    ...             cone_radius=radius.to(u.deg).value,
    ...             column_filters={"instrument_name": "HAWKI"}
    ...                           )

Note that ``cone_ra``, ``cone_dec``, and ``cone_radius`` parameters are specified in degrees, but as float values (so we use ``.value`` to extract the float from the ``astropy.units.Quantity``).

Query for Raw Data
==================

Similar cone search functionality is also available through :meth:`~astroquery.eso.EsoClass.query_instrument` and :meth:`~astroquery.eso.EsoClass.query_main` by passing the same ``cone_ra``, ``cone_dec``, and ``cone_radius`` arguments. 

Instrument-Specific Cone Search
-------------------------------

Cone search for raw data products can be performed using the instrument-specific method, such as :meth:`~astroquery.eso.EsoClass.query_instrument`. This example searches for HAWK-I raw data products around the same coordinates as above.

.. doctest-remote-data::

    >>> table = eso.query_instrument(
    ...             "HAWKI",
    ...             cone_ra=ra.value,
    ...             cone_dec=dec.value,
    ...             cone_radius=radius.to(u.deg).value
    ...                           )

Generic Cone Search
-------------------

Cone search for raw data products can also be performed using the more generic method, :meth:`~astroquery.eso.EsoClass.query_main`. This allows you to search across all instruments without specifying one, with the following example searching for HAWK-I raw data products around the same coordinates as above.

.. doctest-remote-data::

    >>> table = eso.query_main(
    ...             "HAWKI",
    ...             cone_ra=ra.value,
    ...             cone_dec=dec.value,
    ...             cone_radius=radius.to(u.deg).value
    ...                           )

Download Data
=============

To download the data returned by the query, you can use the :meth:`~astroquery.eso.EsoClass.retrieve_data` method. This method takes a list of data product IDs (``dp_id``) and downloads the corresponding files from the ESO archive.

.. doctest-remote-data::
    >>> eso.retrieve_data(table["dp_id"]) # doctest: +SKIP

The ``data_files`` list points to the decompressed dataset filenames that have been locally downloaded. The default location of the decompressed datasets can be adjusted by providing a ``destination`` keyword in the call to :meth:`~astroquery.eso.EsoClass.retrieve_data`.

.. doctest-remote-data::
    >>> data_files = eso.retrieve_data(table["dp_id"], destination="./eso_data/") # doctest: +SKIP