.. _astroquery.nrao:

********************************
NRAO Queries (`astroquery.nrao`)
********************************

Getting started
===============

This module provides access to the `NRAO Archive <https://data.nrao.edu>`_,
backed by its Table Access Protocol (TAP) service. It supersedes the module
that queried the retired pre-2024 NRAO archive interface. The API follows the
ALMA module, on which this implementation is based.

The archive can be queried around a position with
`~astroquery.nrao.NraoClass.query_region`:

.. doctest-remote-data::

    >>> import astropy.units as u
    >>> from astropy.coordinates import SkyCoord
    >>> from astroquery.nrao import Nrao
    >>> coordinates = SkyCoord(187.27791 * u.deg, 2.05238 * u.deg)
    >>> result = Nrao.query_region(coordinates, radius=3 * u.arcmin, maxrec=5)
    >>> print(result['project_code', 'instrument_name', 'target_name'][:5])  # doctest: +IGNORE_OUTPUT
    project_code instrument_name target_name
    ------------ --------------- -----------
         13B-318            EVLA       3C273
         ...

or by object name (resolved with `~astropy.coordinates.SkyCoord.from_name`)
with `~astroquery.nrao.NraoClass.query_object`:

.. doctest-remote-data::

    >>> result = Nrao.query_object('3C273', maxrec=5)

General queries combining any of the supported constraints can be run with
`~astroquery.nrao.NraoClass.query`:

.. doctest-remote-data::

    >>> result = Nrao.query({'source_name': 'L1157', 'band_list': ['Q', 'K']},
    ...                     maxrec=5)

The list of supported query keywords is printed by
`~astroquery.nrao.NraoClass.help`:

.. doctest-skip::

    >>> Nrao.help()

Advanced queries
================

The underlying TAP service accepts ADQL queries against the
``tap_schema.obscore`` table through
`~astroquery.nrao.NraoClass.query_tap`:

.. doctest-remote-data::

    >>> result = Nrao.query_tap(
    ...     "select top 5 obs_id, project_code, proprietary_status "
    ...     "from tap_schema.obscore where "
    ...     "CONTAINS(POINT('ICRS',s_ra,s_dec),"
    ...     "CIRCLE('ICRS',187.27791,2.05238,0.05))=1")

Note that the NRAO TAP server stores ``s_region`` as text, so position
constraints must use ``CONTAINS(POINT(...), CIRCLE(...))`` rather than
``INTERSECTS`` with ``s_region``.

Reference/API
=============

.. automodapi:: astroquery.nrao
    :no-inheritance-diagram:
