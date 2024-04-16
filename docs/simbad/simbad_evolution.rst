.. _simbad-evolutions:

########################
Simbad module evolutions
########################

*********************************
Votable fields and Output options
*********************************

Votable fields are deprecated in favor of output options. Most of the former votable
fields can now be added to the output of Simbad queries with
`~astroquery.simbad.SimbadClass.add_output_columns`. The full list of options is available
with the `~astroquery.simbad.SimbadClass.list_output_options` method.

Some columns and tables have a new name under the TAP interface. The old name will be
recognized by `~astroquery.simbad.SimbadClass.add_output_columns`, but only the new name will
appear in the output.

A few ``votable_fields`` had options in parenthesis. This is no longer supported and can
be replaced by the ``criteria`` argument in ``query_***`` methods or by a custom ADQL
query called with `~astroquery.simbad.SimbadClass.query_tap`. The documentation and
former issues on astroquery's repository contain examples, but don't hesitate to open
a new issue if there is some missing information.

****************************************
Translating query_criteria into criteria
****************************************

The method ``query_criteria`` does not exist anymore in SIMBAD, but is replaced by a
``criteria`` argument in the following methods:

- `~astroquery.simbad.SimbadClass.query_object`
- `~astroquery.simbad.SimbadClass.query_objects`
- `~astroquery.simbad.SimbadClass.query_region`
- `~astroquery.simbad.SimbadClass.query_catalog`
- `~astroquery.simbad.SimbadClass.query_bibobj`
- `~astroquery.simbad.SimbadClass.query_bibcode`
- `~astroquery.simbad.SimbadClass.query_objectids`

This new argument expects a criteria formatted as a ``WHERE`` clause in an ADQL string,
it consists of:

- logical operators ``AND``, ``OR``, ``NOT``,
- comparison operators ``=``, ``!=`` (or its alternative notation ``<>``), ``<``,
  ``>``, ``<=``, ``>=``,
- range comparison ``BETWEEN`` (ex: range of spectral types ``sp_type BETWEEN 'F3' AND 'F5'``),
- membership check ``IN`` (ex: either active galaxy nucleus, or active galaxy
  nucleus candidate ``otype IN ('AGN', 'AG?')``),
- case-sensitive string comparison: ``LIKE``,
- null value check ``IS NULL``, ``IS NOT NULL``.

This list is extracted from the section 2.2.3 of the
`ADQL specification <https://ivoa.net/documents/ADQL/20231215/REC-ADQL-2.1.html>`__.

Here, for example, we add a criteria on the desired type of objects to a region query
in 2° around M11:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad(ROW_LIMIT=20).query_region("M11", "2d",
    ...                                   criteria="otype = 'Star..'")[["main_id", "ra", "dec"]]  # doctest: +IGNORE_OUTPUT
    <Table length=20>
              main_id                    ra                dec
                                        deg                deg
               object                 float64            float64
    ---------------------------- ------------------ ------------------
           ATO J283.9680-04.7022  283.9680584302754 -4.702210643396667
         2MASS J18553904-0441576         283.912704          -4.699355
         2MASS J18434437-0532364   280.934909910062 -5.543481872277222
                 IRAS 18410-0535 280.93514361343995 -5.534989946319999
    Gaia DR3 4255168174887091584  281.9199370352171 -4.607529439915277
                             ...                ...                ...
    Gaia DR3 4255168415418002432  281.8446179288175 -4.647683641737222
              OGLE GD-RRLYR-8997 281.93337499999996 -4.824888888888889
         2MASS J18471362-0444391 281.80677257235084    -4.744217391975
                 IRAS 18449-0454    281.89339967202     -4.85617020367
                       * bet Sct    281.79364256535     -4.74787304458
    Gaia DR2 4255222566334653952  282.4900966404579 -4.434419082480556

We only retrieve objects which main type (``otype``) is a star (``Star``)
or its descendants (``..``) -- see section on `Object types`_ --.

If you already have a string that was a valid criteria in ``query_criteria``,
there is a helper method to translate a criteria from ``query_criteria`` into a string
that will work as ``criteria`` in the other query methods cited above:

.. code-block:: python

    >>> from astroquery.simbad.utils import CriteriaTranslator
    >>> CriteriaTranslator.parse("region(box, GAL, 0 +0, 3d 1d) & otype='SNR'")
    "CONTAINS(POINT('ICRS', ra, dec), BOX('ICRS', 266.4049882865447, -28.936177761791473, 3.0, 1.0)) = 1  AND otype = 'SNR'"

This string can now be incorporated in any of the query methods that accept a ``criteria`` argument.

See a more elaborated example:

.. this test will fail when upstream issue https://github.com/gmantele/vollt/issues/154 is solved
.. then we'll have to replace "otypes" by "alltypes.otypes"

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> from astroquery.simbad.utils import CriteriaTranslator
    >>> # not a galaxy, and not a globular cluster
    >>> old_criteria = "otype != 'Galaxy..' & otype != 'Cl*..'"
    >>> simbad = Simbad()
    >>> # we add the main type and all the types that have historically been attributed to the object
    >>> simbad.add_output_columns("otype", "alltypes")
    >>> result = simbad.query_catalog("M", criteria=CriteriaTranslator.parse(old_criteria))
    >>> result.sort("catalog_id")
    >>> result[["main_id", "catalog_id", "otype", "otypes"]]
    <Table length=11>
     main_id  catalog_id otype                   otypes
      object    object   object                  object
    --------- ---------- ------ ----------------------------------------
        M   1      M   1    SNR                 HII|IR|Psr|Rad|SNR|X|gam
        M  24      M  24    As*                              As*|Cl*|GNe
        M  27      M  27     PN           *|G|HS?|IR|PN|UV|WD*|WD?|X|blu
        M  40      M  40      ?                                        ?
        M  42      M  42    HII                    C?*|Cl*|HII|OpC|Rad|X
        M  43      M  43    HII                               HII|IR|Rad
        M  57      M  57     PN              *|HS?|IR|PN|Rad|WD*|WD?|blu
    NGC  6994      M  73    err                                  Cl*|err
        M  76      M  76     PN                          *|IR|PN|Rad|WD*
        M  78      M  78    RNe                          C?*|Cl*|ISM|RNe
        M  97      M  97     PN *|HS?|IR|NIR|Opt|PN|Rad|UV|WD*|WD?|X|blu

And we indeed get objects from the Messier catalog (as `~astroquery.simbad.SimbadClass.query_catalog` is
meant to return), but with the additional criteria that these objects should be neither galaxies
nor clusters of stars.

************
Object types
************

The example above highlights the subtlety of assigning a type for every object. The SIMBAD database
evolves with the literature and the ``otype`` value reflects the most precise type that was
identified through a literature review.
But all the former ``otype`` assignations are also stored in the ``otypes`` column. These can be either less
precise or false. See in the previous example M27 that is now classified as ``PN`` (Planetary Nebula) and was in the
past thought to be a ``G`` (Galaxy).

The definitions of object types can be found either in SIMBAD's
`documentation on object types <http://simbad.cds.unistra.fr/guide/otypes.htx>`_
or with TAP queries. For example, to see the definition of ``PN``, one can do:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> result = Simbad.query_tap("SELECT * FROM otypedef WHERE otype = 'PN'")
    >>> result[["otype", "label", "description", "is_candidate", "path"]]
    <Table length=1>
    otype     label       description    is_candidate     path
    object    object         object         int16        object
    ------ ------------ ---------------- ------------ ------------
        PN PlanetaryNeb Planetary Nebula            0 * > Ev* > PN

Where ``otypedef`` is the table of SIMBAD containing the definitions of object types.

The ``label`` can also be used in a query.

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.query_tap("SELECT top 5 main_id, otype FROM basic WHERE otype = 'PlanetaryNeb'")  # doctest: +IGNORE_OUTPUT
    <Table length=5>
     main_id   otype
      object   object
    ---------- ------
       IC 4634     PN
    PN H  2-40     PN
    PN PC   12     PN
     NGC  6543     PN
     NGC  7027     PN

And the ``path`` column is a representation of the hierarchy of objects. Here ``PN``
(Planetary Nebula) derives from ``Ev*`` (Evolved Star) which itself derives from ``*``
(Star). This is the classification of objects in place in SIMBAD since 2020. If you
don't find an object type you used to look for in SIMBAD, you might be interested in this
`table of correspondence <http://simbad.cds.unistra.fr/guide/otypes.labels.txt>`_ between
old and new labels for object types.

An interesting feature brought by the hierarchy of objects is the ``..`` notation. For example,
``Ev*..`` means any object type that derives from evolved star.

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.query_tap("SELECT top 5 main_id, otype "
    ...                  "FROM basic WHERE otype = 'Ev*..'")  # doctest: +IGNORE_OUTPUT
    <Table length=5>
           main_id         otype
            object         object
    ---------------------- ------
           IRAS 07506-0345    pA*
    D33 J013331.3+302946.9    cC*
    D33 J013253.5+303810.2    Ce*
                 [SC83] G4    Ce*
              SSTGC 444055    LP*

This return objects which types are indeed among the 17 types deriving from ``Ev*`` (Evolved Star).

*******
Filters
*******

.. Note::

    This section explains the deprecated ``ubv``, ``flux(u)``, and ``fluxdata(u)`` notations.

Historically, there were only three filters in SIMBAD, ``U``, ``B``, and ``V``. This is why
one could add these columns to SIMBAD's output with ``ubv``. This is not
the case anymore, and a suggested workflow now looks like this:

1. Get the list of filters currently in Simbad
==============================================

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.query_tap("SELECT * FROM filter")
    <Table length=17>
       description    filtername  unit
          object        object   object
    ----------------- ---------- ------
          Magnitude U          U    mag
          Magnitude B          B    mag
          Magnitude V          V    mag
          Magnitude R          R    mag
          Magnitude I          I    mag
          Magnitude J          J    mag
          Magnitude H          H    mag
          Magnitude K          K    mag
     Magnitude SDSS u          u    mag
     Magnitude SDSS g          g    mag
     Magnitude SDSS r          r    mag
     Magnitude SDSS i          i    mag
     Magnitude SDSS z          z    mag
     Magnitude Gaia G          G    mag
    JWST NIRCam F150W      F150W    mag
    JWST NIRCam F200W      F200W    mag
    JWST NIRCan F444W      F444W    mag

There are currently 17 filters, but more are added as new data is ingested.
The important information is in the column ``filtername``.

2. Apply a criteria in your query
=================================

You can now use this filter name in a criteria string. For example, to get
fluxes for a specific object, one can use `~astroquery.simbad.SimbadClass.query_object`
as a first base (it selects a single object by its name), add different fields to
the output with `~astroquery.simbad.SimbadClass.add_output_columns` (here ``flux`` adds all
columns about fluxes) and then select only the interesting filters with a ``criteria``
argument:

.. this will fail when upstream bug https://github.com/gmantele/vollt/issues/154 is fixed.
.. "filter" should be replaced by "flux.filter" and "bibcode" by "flux.bibcode".

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> simbad = Simbad()
    >>> simbad.add_output_columns("flux")
    >>> result = simbad.query_object("BD-16  5701", criteria="filter IN ('U', 'B', 'G')")
    >>> result[["main_id", "flux", "flux_err", "filter", "bibcode"]]
    <Table length=2>
      main_id      flux   flux_err filter       bibcode
       object    float32  float32  object        object
    ----------- --------- -------- ------ -------------------
    BD-16  5701     11.15     0.07      B 2000A&A...355L..27H
    BD-16  5701 10.322191 0.002762      G 2020yCat.1350....0G

Here, we looked for flux measurements for ``BD-16 5701`` with three filters. There was no
match for ``U``, but the information is there for ``B`` and ``G``. The ``bibcode``
column is the source of the flux information.

.. replace ``bibcode`` by ``flux.bibcode`` here when https://github.com/gmantele/vollt/issues/154 is fixed.