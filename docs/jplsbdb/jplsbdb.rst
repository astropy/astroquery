.. doctest-skip-all

.. _astroquery.jplsbdb:

*************************************************************************
JPL SBDB Queries (`astroquery.jplsbdb`/astroquery.solarsystem.jpl.sbdb)
*************************************************************************

Overview
========


The :class:`~astroquery.jplsbdb.SBDBClass` class provides
an interface to the `Small-Body Database Browser
<https://ssd.jpl.nasa.gov/sbdb.cgi>`_ (SBDB) maintained by the `JPL
Solar System Dynamics group <http://ssd.jpl.nasa.gov/>`_.

The SBDB provides detailed information on a specific known small body,
including it's orbit, close approaches with major planets, available
radar observations, detailed information on virtual impactors,
discovery circumstances, and a few select physical properties.

This module enables the query of these information for an individual
object into a formatted `~collections.OrderedDict` structure using
`~astropy.units` and `~numpy.ndarray` objects where possible.  It
furthermore provides the means to query a list of objects based on
their primary designation and using a wildcard symbol. This module
uses the SBDB API as described in the `SBDB API documentation
<https://ssd-api.jpl.nasa.gov/doc/sbdb.html>`_ and hence closely
follows the definitions in that document with some simplifications.

Because of its relevance to Solar System science, this service can
also be accessed from the topical submodule
`astroquery.solarsystem.jpl`. The functionality of that service is
identical to the one presented here.

Example
=======

The most simple query to obtain information for a specific Solar
System small-body works as follows:

.. code-block:: python

   >>> from astroquery.jplsbdb import SBDB
   >>> sbdb = SBDB.query('3552')
   >>> print(sbdb)
   OrderedDict([('object', OrderedDict([('shortname', '3552 Don Quixote'), ('neo', True), ('orbit_class', OrderedDict([('name', 'Amor'), ('code', 'AMO')])), ('pha', False), ('spkid', '2003552'), ('kind', 'an'), ('orbit_id', '188'), ('fullname', '3552 Don Quixote (1983 SA)'), ('des', '3552'), ('prefix', None)])), ('signature', OrderedDict([('source', 'NASA/JPL Small-Body Database (SBDB) API'), ('version', '1.0')])), ('orbit', OrderedDict([('source', 'JPL'), ('cov_epoch', Unit("2.45657e+06 d")), ('moid_jup', Unit("0.441 AU")), ('t_jup', '2.315'), ('condition_code', '0'), ('not_valid_before', None), ('rms', '0.51'), ('model_pars', []), ('orbit_id', '188'), ('producer', 'Otto Matic'), ('first_obs', '1983-09-10'), ('soln_date', '2018-07-06 06:55:08'), ('two_body', None), ('epoch', Unit("2.4582e+06 d")), ('elements', OrderedDict([('e', '0.709'), ('e_sig', '4.8e-08'), ('a', Unit("4.26 AU")), ('a_sig', Unit("2.3e-08 AU")), ('q', Unit("1.24 AU")), ('q_sig', Unit("2e-07 AU")), ('i', Unit("31.1 deg")), ('i_sig', Unit("1.1e-05 deg")), ('om', Unit("350 deg")), ('om_sig', Unit("1e-05 deg")), ('w', Unit("316 deg")), ('w_sig', Unit("1.1e-05 deg")), ('ma', Unit("355 deg")), ('ma_sig', Unit("3.9e-06 deg")), ('tp', Unit("2.45825e+06 d")), ('tp_sig', Unit("3.5e-05 d")), ('per', Unit("3210 d")), ('per_sig', Unit("2.6e-05 d")), ('n', Unit("0.112 deg / d")), ('n_sig', Unit("9.2e-10 deg / d")), ('ad', Unit("7.27 AU")), ('ad_sig', Unit("4e-08 AU"))])), ('equinox', 'J2000'), ('data_arc', '12717'), ('not_valid_after', None), ('n_del_obs_used', None), ('sb_used', 'SB431-N16'), ('n_obs_used', '869'), ('comment', None), ('pe_used', 'DE431'), ('last_obs', '2018-07-05'), ('moid', Unit("0.334 AU")), ('n_dop_obs_used', None)]))])

This function orders the parsed data into a dictionary. This
representation of the results is convenient but not easy to read for a
human. :meth:`~astroquery.jplsbdb.SBDBClass.schematic`
will use the output dictionary and transform it into a human-readable
schematic. Please consult the `Data Output section
<https://ssd-api.jpl.nasa.gov/doc/sbdb.html#data-output>`__ of the SBDB API
documentation to learn more about the meaning of the different output fields:

.. code-block:: python

   >>> print(SBDB.schematic(sbdb))
   +-+ object:
   | +-- shortname: 3552 Don Quixote
   | +-- neo: True
   | +-+ orbit_class:
   | | +-- name: Amor
   | | +-- code: AMO
   | +-- pha: False
   | +-- spkid: 2003552
   | +-- kind: an
   | +-- orbit_id: 188
   | +-- fullname: 3552 Don Quixote (1983 SA)
   | +-- des: 3552
   | +-- prefix: None
   +-+ signature:
   | +-- source: NASA/JPL Small-Body Database (SBDB) API
   | +-- version: 1.0
   +-+ orbit:
   | +-- source: JPL
   | +-- cov_epoch: 2.45657e+06 d
   | +-- moid_jup: 0.441 AU
   | +-- t_jup: 2.315
   | +-- condition_code: 0
   | +-- not_valid_before: None
   | +-- rms: 0.51
   | +-- model_pars: []
   | +-- orbit_id: 188
   | +-- producer: Otto Matic
   | +-- first_obs: 1983-09-10
   | +-- soln_date: 2018-07-06 06:55:08
   | +-- two_body: None
   | +-- epoch: 2.4582e+06 d
   | +-+ elements:
   | | +-- e: 0.709
   | | +-- e_sig: 4.8e-08
   | | +-- a: 4.26 AU
   | | +-- a_sig: 2.3e-08 AU
   | | +-- q: 1.24 AU
   | | +-- q_sig: 2e-07 AU
   | | +-- i: 31.1 deg
   | | +-- i_sig: 1.1e-05 deg
   | | +-- om: 350 deg
   | | +-- om_sig: 1e-05 deg
   | | +-- w: 316 deg
   | | +-- w_sig: 1.1e-05 deg
   | | +-- ma: 355 deg
   | | +-- ma_sig: 3.9e-06 deg
   | | +-- tp: 2.45825e+06 d
   | | +-- tp_sig: 3.5e-05 d
   | | +-- per: 3210 d
   | | +-- per_sig: 2.6e-05 d
   | | +-- n: 0.112 deg / d
   | | +-- n_sig: 9.2e-10 deg / d
   | | +-- ad: 7.27 AU
   | | +-- ad_sig: 4e-08 AU
   | +-- equinox: J2000
   | +-- data_arc: 12717
   | +-- not_valid_after: None
   | +-- n_del_obs_used: None
   | +-- sb_used: SB431-N16
   | +-- n_obs_used: 869
   | +-- comment: None
   | +-- pe_used: DE431
   | +-- last_obs: 2018-07-05
   | +-- moid: 0.334 AU
   | +-- n_dop_obs_used: None

The schematic shows the different levels in the dictionary. Note that
:meth:`~astroquery.jplsbdb.SBDBClass.schematic` actually
only returns a string; in order to display it properly, it has to be
passed to a ``print``
function. :meth:`~astroquery.jplsbdb.SBDBClass.schematic`
can also be applied to individual items of the dictionary, e.g.,
``print(sbdb['orbit'])``.

In this example, there are three top-level items (``object``,
``orbit``, ``signature``), each of which is an
`~collections.OrderedDict` itself, containing additional information:
``object`` contains general object information on the object's
dynamical type and identifiers, whereas ``orbit`` contains detailed
information on the target's orbit. ``signature`` simply provides
information on SBDB and the API version used.

``orbit`` contains a number of items describing the target's orbit. In
order to use one of these items, you can access it like any dictionary
item:

.. code-block:: python

   >>> sbdb['orbit']['moid_jup']
   0.441 AU

Note that many of the items in the output dictionary are associated
with `~astropy.units` which can be readily used for
transformations. For instance, if you are interested in the minimum
orbit intersection distance of the target with respect to Jupiter
(``moid_jup``) expressed in km instead of au, you can use:

.. code-block:: python

   >>> print(sbdb['orbit']['moid_jup'].to('km'))
   65972660.9787

The vast majority of parameter names are identical to those used in
the `SBDB API documentation
<https://ssd-api.jpl.nasa.gov/doc/sbdb.html>`_, please refer to this
document for exact definitions.

The most significant difference between data obtained through
:class:`~astroquery.jplsbdb.SBDBClass` and directly
through the `SBDB API <https://ssd-api.jpl.nasa.gov/doc/sbdb.html>`_
is the formatting. Where possible and useful, dictionary style
formatting has been replaced with `~numpy.ndarray` structure to make
the data easier to access (see e.g., ``sbdb['orbit']['elements']`` in
the above example).


Name Search
-----------

The `SBDB API <https://ssd-api.jpl.nasa.gov/doc/sbdb.html>`_ provides
a name search tool that enables the listing of existing target names
using a wildcard symbol (``'*'``). For instance, if you are interested
in all NEOs with designations starting with "2018 AA", you would use
the following query:

.. code-block:: python

    >>> sbdb = SBDB.query('2018 AA*', neo_only=True)

Note that in case of a name search not the entire output is queries
per target, but only a list of objects matching this pattern:

.. code-block:: python

    >>> sbdb['list']
    OrderedDict([('pdes', ['2018 AA4', '2018 AA12']), ('name', ['(2018 AA4)', '(2018 AA12)'])])

Customizing your Query
======================

The default :meth:`~astroquery.jplsbdb.SBDBClass.query`
offers only a limited amount of target information. The full potential
of the `SBDB API <https://ssd-api.jpl.nasa.gov/doc/sbdb.html>`_ can be
tapped using the optional parameters of
:meth:`~astroquery.jplsbdb.SBDBClass.query`. The
following listing shows the optional parameters of
:meth:`~astroquery.jplsbdb.SBDBClass.query` and how they
translate to the `SBDB API
<https://ssd-api.jpl.nasa.gov/doc/sbdb.html>`_. Note that most options
are or boolean nature and can be triggered by simply assigning
``True`` to them.

* ``id_type``: available options [``'search'``, ``'spk'``, ``'des'``]
  translate into the different SBDB API search modes [``sstr``,
  ``spk``, ``des``]; the default search mode is ``'search'``

* ``neo_only``: outputs only information for Near-Earth Objects
  (NEOs); corresponds to SBDB API option ``neo``; default value:
  ``False``

* ``alternate_id``: provides information on alternate ids, for
  instance in the case of double designations; ``True`` activates the
  SBDB API options ``alt-des`` and ``alt-spk``; default value:
  ``False``

* ``full_precision``: enables full precision output; corresponds to
  SBDB API option ``full_prec``; default value: ``False``

* ``solution_epoch``: outputs the orbit data at the JPL orbit-solution
  epoch instead of the standard Minor Planet Center epoch; corresponds
  to SBDB API option ``soln_epoch``; default value: ``False``

* ``covariance``: outputs the orbital covariance (if available) in the
  form specified: ``'mat'`` in full matrix form, ``'vec'`` in
  upper-triangular vector-stored form, ``'src'`` in upper-triangular
  vector-stored square-root form; corresponds to SBDB API option
  ``cov``; default value: ``None`` (no output)

* ``validity``: output ``not_valid_before`` and ``not_valid_after``
  validity ranges for the orbit in Julian Date format; ``True``
  corresponds to SBDB API ``nv_fmt='jd'``; default value: ``False``

* ``alternate_orbit``: output information on alternate orbits (e.g.,
  in the case of comets); corresponds to SBDB API ``alt-orbits``;
  default value: ``False``

* ``phys``: output available information on physical properties;
  corresponds to SBDB API ``phys-par``; default value: ``False``

* ``close_approach``: output information on close approaches with
  major bodies; ``True`` corresponds to SBDB API ``ca-data='true'``
  together with ``ca-time='both'``, ``ca-tunc='both'``,
  ``ca-unc='true'``; default value: ``False``

* ``radar``: output information on radar observations; ``True``
  corresponds to ``radar-obs='true'`` together with ``r-name='true'``,
  ``r-observer='true'``, and ``r-notes='true'``; default value:
  ``False``

* ``virtual-impactor``: output information on virtual impactor status;
  corresponds to SBDB API ``vi-data``; default value: ``False``

* ``discovery``: output information on discovery circumstance;
  ``True`` corresponds to SBDB API ``discovery='true'`` and
  ``raw-citation='true'``; default value: ``False``



Acknowledgements
================

This submodule makes use of the `JPL Horizons
<https://ssd.jpl.nasa.gov/sbdb.cgi>`_ system.

The development of this submodule is funded through NASA PDART
Grant No. 80NSSC18K0987 to the `sbpy project <http://sbpy.org>`_.


Reference/API
=============

.. automodapi:: astroquery.jplsbdb
    :no-inheritance-diagram:
