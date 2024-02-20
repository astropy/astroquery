.. _simbad-evolutions:

########################
Simbad module evolutions
########################

*********************************
Votable fields and Output options
*********************************

Votable fields are deprecated in favor of output options. Most of the former votable
fields can now be added to the output of Simbad queries with
`~astroquery.simbad.SimbadClass.add_to_output`. The columns and tables that have a new name
under the TAP interface will be recognized by `~astroquery.simbad.SimbadClass.add_to_output`.
Some Votable Fields that supported options in parenthesis are no
longer supported. These can be replaced by criteria in query_methods or by a custom ADQL
query called with `~astroquery.simbad.SimbadClass.query_tap`. The documentation and former
issues on astroquery's repository contain examples, but don't hesitate to open a new issue
if there is some missing information.

****************************************
Translating query_criteria into criteria
****************************************

The method `~astroquery.simbad.SimbadClass.query_criteria` is now deprecated in SIMBAD.
It is still possible to use it from astroquery for now, but any existing bug will not
be fixed. There are also a number of missing features.
This page shows how the former functionalities of `~astroquery.simbad.SimbadClass.query_criteria`
can be replaced.

The new interface to connect to SIMBAD is build on TAP and ADQL. 
To learn more about this, you can have a look at the
`~astroquery.simbad.SimbadClass.query_tap` :ref:`documentation <query-tap-documentation>`.

Since astroquery > 0.4.7, most of the ``query_***`` methods in the simbad module accept
a ``criteria`` argument, it concerns:

- `~astroquery.simbad.SimbadClass.query_object`
- `~astroquery.simbad.SimbadClass.query_objects`
- `~astroquery.simbad.SimbadClass.query_region`
- `~astroquery.simbad.SimbadClass.query_catalog`
- `~astroquery.simbad.SimbadClass.query_bibobj`
- `~astroquery.simbad.SimbadClass.query_bibcode`
- `~astroquery.simbad.SimbadClass.query_objectids`

There is a helper method to translate a criteria from
`~astroquery.simbad.SimbadClass.query_criteria` into a string that will work as ``criteria``
in the other query methods cited above:

.. code-block:: python

    >>> from astroquery.simbad.utils import CriteriaTranslator
    >>> CriteriaTranslator.parse("region(box, GAL, 0 +0, 3d 1d) & otype='SNR'")
    "CONTAINS(POINT('ICRS', ra, dec), BOX('ICRS', 266.4049882865447, -28.936177761791473, 3.0, 1.0)) = 1  AND otype = 'SNR'"

This string can then either be incorporated in a custom ADQL query called with
`~astroquery.simbad.SimbadClass.query_tap` or in any of the query methods that accept a ``criteria`` argument.
See for example:

.. this test will fail when upstream issue https://github.com/gmantele/vollt/issues/154 is solved
.. then we'll have to replace "otypes" by "alltypes.otypes"

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> from astroquery.simbad.utils import CriteriaTranslator
    >>> # not a galaxy, and not a globular cluster
    >>> old_criteria = "otype != 'Galaxy..' & otype != 'Cl*..'"
    >>> simbad = Simbad()
    >>> # we add the main type and all the types that have historically been attributed to the object
    >>> simbad.add_to_output("otype", "alltypes")
    >>> result = simbad.query_catalog("M", criteria=CriteriaTranslator.parse(old_criteria))
    >>> result[["main_id", "catalog_id", "otype", "otypes"]]
    <Table length=11>
     main_id  catalog_id otype                   otypes             
      object    object   object                  object                 
    --------- ---------- ------ ----------------------------------------
        M  27      M  27     PN           *|G|HS?|IR|PN|UV|WD*|WD?|X|blu
        M  24      M  24    As*                              As*|Cl*|GNe
        M  40      M  40      ?                                        ?
        M  78      M  78    RNe                          C?*|Cl*|ISM|RNe
    NGC  6994      M  73    err                                  Cl*|err
        M  43      M  43    HII                               HII|IR|Rad
        M  42      M  42    HII                    C?*|Cl*|HII|OpC|Rad|X
        M   1      M   1    SNR                     HII|IR|Rad|SNR|X|gam
        M  76      M  76     PN                          *|IR|PN|Rad|WD*
        M  97      M  97     PN *|HS?|IR|NIR|Opt|PN|Rad|UV|WD*|WD?|X|blu
        M  57      M  57     PN              *|HS?|IR|PN|Rad|WD*|WD?|blu

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

The definitions for object types can be found either in SIMBAD's
`documentation on object types <http://simbad.cds.unistra.fr/guide/otypes.htx>`_ or with TAP queries.
To see the definition of ``PN``, one can do:

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
The label can also be used in a query.

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

And the ``path`` column is a representation of the hierarchy of objects. Here ``PN`` (Planetary Nebula) derives
from ``Ev*`` (Evolved Star) which itself derives from ``*`` (Star). This is the classification of objects
in place in SIMBAD since 2020. If you don't find an object type you used to see with
`~astroquery.simbad.SimbadClass.query_criteria`, you might be interested in this
`table of correspondence <http://simbad.cds.unistra.fr/guide/otypes.labels.txt>`_ between old and new labels
for object types.

An interesting feature brought by the hierarchy of objects is the ``..`` notation. For example,
``Ev*..`` means any object type that derives from evolved star.

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.query_tap("SELECT top 5 main_id, otype FROM basic WHERE otype = 'Ev*..'")  # doctest: +IGNORE_OUTPUT 
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

Historically, there were only three filters in SIMBAD, ``U``, ``B``, and ``V``. This is not
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
the output with `~astroquery.simbad.SimbadClass.add_to_output` (here ``flux`` adds all
columns about fluxes) and then select only the interesting filters with a ``criteria``
argument:

.. this will fail when upstream bug https://github.com/gmantele/vollt/issues/154 is fixed.
.. "filter" should be replaced by "flux.filter" and "bibcode" by "flux.bibcode".

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> simbad = Simbad()
    >>> simbad.add_to_output("flux")
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