.. _simbad-evolutions:

########################
Simbad module evolutions
########################

***************************************
Major breaking changes in version 0.4.8
***************************************

In version 0.4.8, the SIMBAD astroquery module switched from SIMBAD's deprecated
interface to the TAP interface. This implied the following breaking changes:

- `~astroquery.simbad.SimbadClass.query_objects` outputs now have an additional column 
  ``user_specified_id`` containing the objects' names as specified by the user. The 
  votable_field option ``typed_id`` is removed,
- All query methods will return tables with column names in lowercase (it was uppercase
  in 0.4.7 and before) -- except for optical filter names that are case sensitive,
- the `~astroquery.simbad.SimbadClass.query_criteria` method is deprecated. See
  section :ref:`query_criteria_evolution`.

For a more extensive list of changes, you can have a look at `the changelog
<https://github.com/astropy/astroquery/blob/main/CHANGES.rst>`_.

.. _query_criteria_evolution:

****************************************
Translating query_criteria into criteria
****************************************

The method ``query_criteria`` is now deprecated in the SIMBAD module. It is replaced by
a ``criteria`` argument in the following methods:

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
    >>> CriteriaTranslator.parse("region(box, ICRS, 0 +0, 3d 1d) & otype='SNR'")
    "CONTAINS(POINT('ICRS', ra, dec), BOX('ICRS', 0.0, 0.0, 3.0, 1.0)) = 1 AND otypes.otype = 'SNR'"

This string can now be incorporated in any of the query methods that accept a ``criteria`` argument.

See a more elaborated example:

.. this test will fail when upstream issue https://github.com/gmantele/vollt/issues/154 is solved
.. then we'll have to replace "otypes" by "alltypes.otypes"

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> from astroquery.simbad.utils import CriteriaTranslator
    >>> # not a galaxy, and not a globular cluster
    >>> old_criteria = "maintype != 'Galaxy..' & maintype != 'Cl*..'"
    >>> simbad = Simbad()
    >>> # we add the main type and all the types that have historically been attributed to the object
    >>> simbad.add_votable_fields("otype", "alltypes")
    >>> result = simbad.query_catalog("M", criteria=CriteriaTranslator.parse(old_criteria))
    >>> result.sort("catalog_id")
    >>> result[["main_id", "catalog_id", "otype", "alltypes.otypes"]]
    <Table length=11>
     main_id  catalog_id otype              alltypes.otypes             
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
identified through a literature review at the moment at which the query is done.
All the former ``otype`` assignations are also stored in the ``otypes`` column. These can be either less
precise or false. See in the previous example M27 that is now classified as ``PN`` (Planetary Nebula)
and was in the past thought to be a ``G`` (Galaxy).

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

The ``label`` can also be used in a query if you want your code to be easier to read.

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

The ``path`` column in ``otypedef`` is a representation of the hierarchy of objects.
Here ``PN`` (Planetary Nebula) derives from ``Ev*`` (Evolved Star) which itself derives
from ``*`` (Star). This is the classification of objects in place in SIMBAD since 2020.
If you don't find an object type you used to look for in SIMBAD, you might be interested
in this `table of correspondence <http://simbad.cds.unistra.fr/guide/otypes.labels.txt>`_ 
between old and new labels for object types.

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

This return objects which types are indeed among the 17 types deriving from ``Ev*``
(Evolved Star). For example, ``pA*`` is a post-AGB Star.

.. _optical filters:

***************
Optical Filters
***************

Historically, there were only three optical filters in SIMBAD, ``U``, ``B``, and ``V``.
This is why one could add these columns to SIMBAD's output with ``ubv``. This is not
the case anymore.

There are two different ways to add fluxes to the result of a SIMBAD query. If you only need
a quick access to the value of the flux without extra information, you can add the votable
field corresponding to a specific optical filter. The list of filter names can be printed with 

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> options = Simbad.list_votable_fields()
    >>> options[options["type"] == "filter name"]
    <Table length=17>
     name     description        type   
    object       object         object  
    ------ ----------------- -----------
         U       Magnitude U filter name
         B       Magnitude B filter name
         V       Magnitude V filter name
         R       Magnitude R filter name
         I       Magnitude I filter name
         J       Magnitude J filter name
         H       Magnitude H filter name
         K       Magnitude K filter name
         u  Magnitude SDSS u filter name
         g  Magnitude SDSS g filter name
         r  Magnitude SDSS r filter name
         i  Magnitude SDSS i filter name
         z  Magnitude SDSS z filter name
         G  Magnitude Gaia G filter name
     F150W JWST NIRCam F150W filter name
     F200W JWST NIRCam F200W filter name
     F444W JWST NIRCan F444W filter name

There are currently 17 filters in SIMBAD, but more are added as new data is ingested.

.. Note::

    This is the only case-sensitive votable field, due to the fact that the filters ``U``
    and ``u`` (for example) are distinct.

A query for fluxes would then look like:

.. doctest-remote-data::
    
    >>> from astroquery.simbad import Simbad
    >>> simbad = Simbad()
    >>> simbad.add_votable_fields("U", "V", "B")
    >>> simbad.query_object("NGC 5678")[["main_id", "U", "V", "B"]]
    <Table length=1>
     main_id     U       V            B         
      object  float64 float64      float64      
    --------- ------- ------- ------------------
    NGC  5678      --      -- 12.100000381469727

However, this quick access does not allow to retrieve the flux error or the bibcode of the
article from which the information is extracted. To do so, prefer the ``flux`` votable field:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> simbad = Simbad()
    >>> simbad.add_votable_fields("flux")
    >>> result = simbad.query_object("BD-16  5701")
    >>> result[["main_id", "flux", "flux_err", "flux.filter", "flux.bibcode"]]
    <Table length=6>
      main_id      flux   flux_err flux.filter     flux.bibcode   
       object    float32  float32     object          object      
    ----------- --------- -------- ----------- -------------------
    BD-16  5701 10.322191 0.002762           G 2020yCat.1350....0G
    BD-16  5701      10.6     0.06           V 2000A&A...355L..27H
    BD-16  5701     9.205    0.023           J 2003yCat.2246....0C
    BD-16  5701     8.879    0.042           H 2003yCat.2246....0C
    BD-16  5701     8.777     0.02           K 2003yCat.2246....0C
    BD-16  5701     11.15     0.07           B 2000A&A...355L..27H

This gives more details than the quick view. Each line corresponds to a unique filter.
The ``bibcode`` column corresponds to the article in which the flux information was found.
We could also add a criteria to restrict the filters in the output:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> simbad = Simbad()
    >>> simbad.add_votable_fields("flux")
    >>> result = simbad.query_object("BD-16  5701", criteria="filter IN ('U', 'B', 'G')")
    >>> result[["main_id", "flux", "flux_err", "flux.filter", "flux.bibcode"]]
    <Table length=2>
      main_id      flux   flux_err flux.filter     flux.bibcode   
       object    float32  float32     object          object      
    ----------- --------- -------- ----------- -------------------
    BD-16  5701     11.15     0.07           B 2000A&A...355L..27H
    BD-16  5701 10.322191 0.002762           G 2020yCat.1350....0G

There was no match for ``U``, but the information is there for ``B`` and ``G``.