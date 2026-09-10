.. _astroquery.lco:

****************************************************
LCO Archive Queries (`astroquery.lco`)
****************************************************

Getting Started
===============

This module searches the `science archive <https://archive.lco.global>`_ of
`Las Cumbres Observatory <https://lco.global>`_, a global network of robotic telescopes.
The archive holds one record per **frame**: a single exposure from one instrument,
either raw or reduced.

Anyone can query the archive without logging in, which returns every frame
whose proprietary period has expired. Logging in with an API token additionally
returns the proprietary frames belonging to your proposals; see
`Authentication`_ below.

Every query returns a `~astropy.table.Table` of frame metadata, including a
download link for each frame. The `Downloading Data`_ section below describes
how to download the frames from a query. For more information on


Positional Queries
------------------

`~astroquery.lco.LcoArchiveQuery.query_region` searches by position. Given only
a position, it returns the frames whose footprint contains that point:

.. doctest-remote-data::

    >>> from astroquery.lco import LcoArchive
    >>> from astropy import coordinates, units as u
    >>> coord = coordinates.SkyCoord(210.802429, 54.348750, unit="deg")
    >>> frames = LcoArchive.query_region(coord, reduction_level=91,
    ...                                  start="2024-03-01", end="2024-03-08")
    >>> print(frames["basename", "target_name", "site_id", "exposure_time"][:5])
                basename            target_name site_id exposure_time
                                                              s
    ------------------------------- ----------- ------- -------------
    tfn1m001-fa11-20240304-0217-e91   SN2023ixf     tfn       399.999
    tfn1m001-fa11-20240304-0216-e91   SN2023ixf     tfn         400.0
    tfn1m014-fa20-20240304-0345-e91   SN2023ixf     tfn          90.0
    tfn1m001-fa11-20240304-0163-e91   SN2023ixf     tfn          90.0
    tfn1m001-fa11-20240304-0162-e91   SN2023ixf     tfn          90.0

Adding ``radius`` searches a cone instead, returning frames whose footprint
*overlaps* the region rather than covers the point. A box search is available
by passing ``width`` and ``height`` together:

.. doctest-remote-data::

    >>> frames = LcoArchive.query_region(coord, radius=0.2*u.deg,
    ...                                  reduction_level=91,
    ...                                  start="2024-03-01", end="2024-03-08")
    >>> frames = LcoArchive.query_region(coord, width=0.4*u.deg, height=0.4*u.deg,
    ...                                  reduction_level=91,
    ...                                  start="2024-03-01", end="2024-03-08")

A cone is sent to the archive as a 32-vertex polygon, so the match is
approximate at the sub-arcsecond level.


Object Name Queries
-------------------

`~astroquery.lco.LcoArchiveQuery.query_object` searches on the target name the
observer submitted with the observation request. It does not resolve the name
or search on position, so use ``query_region`` if you want everything covering
a target regardless of what it was called. The default parameter of ``exact=True``
performs a case-sensitive exact match. Set it to ``False`` to perform a
case-insensitive contains query:

.. doctest-remote-data::

    >>> from astroquery.lco import LcoArchive
    >>> frames = LcoArchive.query_object("SN2023ixf", exact=True, reduction_level=91,
    ...                                  start="2024-03-01", end="2024-03-08")
    >>> print(frames["basename", "instrument_id", "reduction_level"][:5])
                basename            instrument_id reduction_level
    ------------------------------- ------------- ---------------
    tfn1m001-fa11-20240304-0217-e91          fa11              91
    tfn1m001-fa11-20240304-0216-e91          fa11              91
    tfn1m014-fa20-20240304-0345-e91          fa20              91
    tfn1m001-fa11-20240304-0163-e91          fa11              91
    tfn1m001-fa11-20240304-0162-e91          fa11              91


Criteria Queries
----------------

`~astroquery.lco.LcoArchiveQuery.query_criteria` searches on any combination of
frame criteria. A list of the criteria is available at
`~astroquery.lco.LcoArchiveQuery.list_criteria`, while a more in depth
explanation of the available criteria can be found on
`LCO's Developer Docs <https://developers.lco.global/#data-format-definition37>`_.

.. doctest-remote-data::

    >>> from astroquery.lco import LcoArchive
    >>> LcoArchive.list_criteria()   # doctest: +ELLIPSIS
    ['basename', 'basename_exact', 'configuration_type', 'covers', ...]

.. doctest-remote-data::

    >>> from astroquery.lco import LcoArchive
    >>> frames = LcoArchive.query_criteria(site_id="lsc",
    ...                                    configuration_type="BIAS",
    ...                                    reduction_level=0, instrument_id="kb98",
    ...                                    start="2024-03-02", end="2024-03-03")
    >>> print(frames["basename", "site_id", "telescope_id", "configuration_type"][:3])
                basename            site_id telescope_id configuration_type
    ------------------------------- ------- ------------ ------------------
    lsc0m409-kb98-20240302-0017-b00     lsc         0m4a               BIAS
    lsc0m409-kb98-20240302-0016-b00     lsc         0m4a               BIAS
    lsc0m409-kb98-20240302-0015-b00     lsc         0m4a               BIAS

The same criteria can be passed to ``query_region`` and ``query_object``, which
narrow a positional or name search rather than replacing it.

``start`` and ``end`` bound the observation date and accept a string, an
`~astropy.time.Time`, or a `~datetime.datetime`. A query should **always** be
narrowed by ``start`` and ``end`` to reduce load on the database.

``reduction_level`` is ``0`` for raw data and ``91`` for reduced.

Two criteria accept several values at once,
``include_configuration_type`` and ``exclude_configuration_type``:

.. doctest-remote-data::

    >>> frames = LcoArchive.query_criteria(site_id="lsc", instrument_id="kb98",
    ...                                    exclude_configuration_type=["BIAS", "DARK"],
    ...                                    start="2024-03-02",
    ...                                    end="2024-03-03")   # doctest: +IGNORE_WARNINGS

All other criteria expect a single value only.


Discovering Criteria Values
-------------------------------

The ``list_*`` methods list which sites, telescopes,
instruments, filters, configuration types or proposals are available to filter:

.. doctest-remote-data::

    >>> LcoArchive.list_sites()
    ['bpl', 'coj', 'cpt', 'elp', 'lsc', 'mfg', 'ogg', 'sor', 'sqa', 'tfn', 'tlv', 'tst']
    >>> LcoArchive.list_configuration_types()   # doctest: +IGNORE_OUTPUT
    ['ARC', 'BIAS', 'CATALOG', 'DARK', 'DOMEFLAT', ...]

An unrecognised criterion is rejected before any request is made, and the error
lists the ones that are accepted:

.. doctest-remote-data::

    >>> LcoArchive.query_criteria(not_a_criteria="fa16")
    Traceback (most recent call last):
    ...
    ValueError: 'not_a_criteria' is not a supported LCO archive filter. Supported filters are: basename, ...


How Many Rows You Get
---------------------

Queries return at most ``row_limit`` frames, 100 by default. When the archive
holds more than were returned, a ``MaxResultsWarning`` is printed.

.. doctest-remote-data::

    >>> frames = LcoArchive.query_criteria(site_id="lsc", row_limit=3,
    ...                                    start="2024-03-02", end="2024-03-03")   # doctest: +SHOW_WARNINGS
    MaxResultsWarning: Results truncated to 3 frames. Pass row_limit=-1 to retrieve every matching frame.

Pass ``row_limit=-1`` to retrieve every match, paging through the archive as
needed.

.. doctest-skip::

    >>> LcoArchive.ROW_LIMIT = 500


Downloading Data
----------------

`~astroquery.lco.LcoArchiveQuery.download_files` downloads the data files for the
frames in a result table:

.. doctest-remote-data::

    >>> from astroquery.lco import LcoArchive
    >>> frames = LcoArchive.query_criteria(
    ...     basename_exact="lsc0m409-kb98-20240302-0017-b00")
    >>> LcoArchive.download_files(frames, download_dir=".")   # doctest: +IGNORE_OUTPUT
    ['./lsc0m409-kb98-20240302-0017-b00.fits.fz']

Files already present are skipped unless you pass ``overwrite=True``. You can
also pass frame ids instead of a table, in which case each one is looked up so
that its download link is fresh:

.. doctest-skip::

    >>> LcoArchive.download_files([69021388, 69081552], download_dir=".")

The download links the archive returns are presigned and expire in 48 hours.
Query again to refresh it, or use `~astroquery.lco.LcoArchiveQuery.get_frame`,
which returns the full record for a single frame including the fields the result
table leaves out (``area``, ``version_set`` and ``related_frames``):

.. doctest-remote-data::

    >>> frame = LcoArchive.get_frame(69008745)
    >>> frame["basename"]
    'lsc0m409-kb98-20240302-0017-b00'
    >>> sorted(frame)[:4]
    ['BLKUID', 'DATE_OBS', 'DAY_OBS', 'EXPTIME']


Thumbnails
----------

Passing ``include_thumbnails=True`` asks the archive for JPEG preview links
alongside the metadata, which adds ``thumbnail_url`` and ``thumbnail_filename``
columns. ``thumbnail_size`` chooses between ``'small'`` and ``'large'``:

.. doctest-remote-data::

    >>> from astroquery.lco import LcoArchive
    >>> frames = LcoArchive.query_criteria(site_id="cpt", instrument_id="sq39",
    ...                                    reduction_level=91,
    ...                                    include_thumbnails=True,
    ...                                    thumbnail_size="large",
    ...                                    start="2025-03-02T18:00",
    ...                                    end="2025-03-02T19:00")
    >>> print(frames["thumbnail_filename"][0])
    cpt0m439-sq39-20250302-0135-e91-large_thumbnail.jpg
    >>> LcoArchive.download_thumbnails(frames[:1], download_dir=".")   # doctest: +IGNORE_OUTPUT

Not every frame has a thumbnail — the archive only began storing them in
2025 — and frames without one are skipped.


Authentication
==============

Queries work without logging in and return the public archive. To reach the
proprietary frames on your own proposals, log in with the API token from your
`LCO profile page <https://observe.lco.global/accounts/profile/>`_:

.. doctest-skip::

    >>> from astroquery.lco import LcoArchive
    >>> LcoArchive.login(token="your-api-token")
    >>> LcoArchive.authenticated()
    True

You can log in with your observing portal username instead, which exchanges
your credentials for a token. The password is read from your system keyring if
it is stored there, and prompted for otherwise; pass ``store_password=True`` to
save it for later sessions:

.. doctest-skip::

    >>> LcoArchive.login(username="your-username")

Every query method behaves identically once you are logged in — the difference
is only in what the archive returns. Authenticated sessions also page through
results 1000 frames at a time rather than 100.


Configuration
=============

The module reads four configuration items, which can be changed at runtime through
``astroquery.lco.conf``:

* ``archive_url``: The archive to query. Defaults to
  https://archive-api.lco.global.

* ``token_url``: Where a username and password are exchanged for an API token.
  This is the LCO observing portal rather than the archive, and defaults to
  https://observe.lco.global/api/api-token-auth/.

* ``timeout``: Seconds to wait for the archive to respond. Defaults to ``30``.

* ``row_limit``: The default maximum number of frames a query returns. Defaults
  to ``100``; set it to ``-1`` to retrieve every match for a query.

.. doctest-skip::

    >>> from astroquery.lco import conf
    >>> conf.timeout = 60


.. testcleanup::

    >>> from astroquery.utils import cleanup_saved_downloads
    >>> cleanup_saved_downloads(['lsc0m409-kb98-20240302-0017-b00.fits.fz',
    ...                          'cpt0m439-sq39-20250302-0135-e91-large_thumbnail.jpg'])


Reference/API
=============

.. automodapi:: astroquery.lco
    :no-inheritance-diagram:
