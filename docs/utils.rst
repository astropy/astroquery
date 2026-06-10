.. doctest-skip-all

.. _astroquery.utils:

*************************************
Astroquery utils (`astroquery.utils`)
*************************************

Querying multiple coordinates
=============================

Several query methods that accept a single sky position per request (for
example ``Gaia.query_object``, ``Heasarc.query_region``,
``Alma.query_region``) also accept a vector
`~astropy.coordinates.SkyCoord` or a list of coordinates (or coordinate
strings). In that case astroquery submits one request per position and
combines the results: methods returning a `~astropy.table.Table` return a
single stacked table with an added ``query_index`` column mapping each row
back to the input position, while other return types come back as a list
in input order.

.. code-block:: python

    from astropy.coordinates import SkyCoord
    import astropy.units as u
    from astroquery.heasarc import Heasarc

    coords = SkyCoord([182.6, 10.7] * u.deg, [39.4, 41.3] * u.deg)
    result = Heasarc.query_region(coords, catalog='suzamaster', radius=2 * u.arcmin)

The requests are issued through a small worker pool with a minimum spacing
between submissions, so that looped queries stay well below request rates
that could degrade the archive services. None of the affected archives
publish a hard rate limit, so the defaults are deliberately conservative;
they can be tuned through ``astroquery.utils.multicoord.conf``:

.. code-block:: python

    from astroquery.utils.multicoord import conf

    conf.max_parallel_queries = 2   # parallel requests (default 3)
    conf.min_request_interval = 1.  # seconds between submissions (default 0.3)

Please be considerate: archive servers are a shared resource, raising these
values can get a client blocked, and where a service offers a native
multi-position interface (for example a TAP table upload), that is always
preferable to a long client-side loop.

Reference/API
=============

.. automodapi:: astroquery.utils
    :no-inheritance-diagram:

.. automodapi:: astroquery.utils.multicoord
    :no-inheritance-diagram:

.. automodapi:: astroquery.utils.timer
    :no-inheritance-diagram:

TAP/TAP+
--------

Table Access Protocol implementation. See :doc:`utils/tap`
