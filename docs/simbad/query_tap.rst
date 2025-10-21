.. _query-tap-documentation:

`~astroquery.simbad.SimbadClass.query_tap` (for Table Access Protocol) is the one
query to rule them all. It allows one to access all the information in SIMBAD with the
Astronomical Data Query Language (ADQL). ADQL is a flavor of the Structured
Query Language (SQL) adapted to astronomy. To learn more about this language,
see the `ADQL documentation <https://ivoa.net/documents/ADQL/index.html>`__
or the `Simbad ADQL cheat sheet <http://simbad.cds.unistra.fr/simbad/tap/help/adqlHelp.html>`__.

Structure of an ADQL query
--------------------------

The method `~astroquery.simbad.SimbadClass.query_tap` is called with a string containing the
ADQL query.

.. code-block:: SQL

  /*ADQL queries start with selecting the columns that will be in the output. Usually,
  the column name is sufficient. If there is a need to lift ambiguity, add the table
  name first (table_name.column_name). This is also where the number of rows is fixed
  (here 5).*/
  SELECT TOP 5 basic.ra, basic.dec, main_id, nbref
  /*Then comes the declaration of the tables to be included in the query. Here *basic* and
  *ident*. Their common column is named *oid* in *basic* and *oidref* in *ident*.*/
  FROM basic JOIN ident ON basic.oid = ident.oidref
  /*The conditions come after. This query filters otypes that are not in any
  cluster of star (Cl*) sub-category (..), specific redshifts, and the results should
  have an NGC name in their list of names.*/
  WHERE (otype != 'Cl*..') AND (rvz_redshift < 1) AND (id LIKE 'NGC%')
  /*The result is then sorted so that the top 5 selected corresponds to
  the objects cited by the largest number of papers.*/
  ORDER BY nbref DESC

This ADQL query can be called with `~astroquery.simbad.SimbadClass.query_tap`:

.. nbref changes often so we ignore the output here
.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.query_tap("""SELECT TOP 5 basic.ra, basic.dec, main_id, nbref
    ...                  FROM basic JOIN ident ON basic.oid = ident.oidref
    ...                  WHERE (otype != 'Cl*..') AND (rvz_redshift < 1)
    ...                  AND (id LIKE 'NGC%')
    ...                  ORDER BY nbref DESC""") # doctest: +IGNORE_OUTPUT
        <Table length=5>
            ra                dec         main_id  nbref
           deg                deg
         float64            float64        object  int32
    ------------------ ------------------ -------- -----
    10.684708333333333 41.268750000000004    M  31 12412
    13.158333333333333 -72.80027777777778 NAME SMC 10875
       187.70593076725 12.391123246083334    M  87  7040
    148.96845833333333  69.67970277777778    M  82  5769
        23.46206906218 30.660175111980003    M  33  5737

And voilà, we get the 5 NGC objects that are the most cited in literature, are not clusters
of stars, and have a redshift < 1. The following sections cover methods that help build ADQL
queries. A showcase of more complex queries comes after.

Available tables
----------------

SIMBAD is a relational database. This means that it is a collection of tables with
links between them. You can access a `graphic representation of Simbad's tables and
their relations <http://simbad.cds.unistra.fr/simbad/tap/tapsearch.html>`__ or print
the names and descriptions of each table with the
`~astroquery.simbad.SimbadClass.list_tables` method:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.list_tables() # doctest: +IGNORE_OUTPUT
    <Table length=30>
      table_name                                  description
        object                                       object
    ------------- ----------------------------------------------------------------------------
            basic                                    General data about an astronomical object
              ids                                             all names concatenated with pipe
         alltypes                                      all object types concatenated with pipe
            ident                                        Identifiers of an astronomical object
              cat                                                              Catalogues name
             flux                      Magnitude/Flux information about an astronomical object
        allfluxes                             all flux/magnitudes U,B,V,I,J,H,K,u_,g_,r_,i_,z_
           filter                                                 Description of a flux filter
          has_ref Associations between astronomical objects and their bibliographic references
              ref                                                      Bibliographic reference
           author                                          Author of a bibliographic reference
           h_link                                              hierarchy of membership measure
      mesHerschel                                                   The Herschel observing Log
           biblio                                                                 Bibliography
         keywords                                                  List of keywords in a paper
           mesXmm                                                           XMM observing log.
    mesVelocities                                   Collection of HRV, Vlsr, cz and redshifts.
           mesVar                         Collection of stellar variability types and periods.
           mesRot                                               Stellar Rotational Velocities.
            mesPM                                                Collection of proper motions.
           mesPLX                                      Collection of trigonometric parallaxes.
         otypedef                               all names and definitions for the object types
           mesIUE                            International Ultraviolet Explorer observing log.
           mesISO                              Infrared Space Observatory (ISO) observing log.
          mesFe_h                  Collection of metallicity, as well as Teff, logg for stars.
      mesDiameter                                             Collection of stellar diameters.
      mesDistance                   Collection of distances (pc, kpc or Mpc) by several means.
           otypes                           List of all object types associated with an object
           mesSpT                                                Collection of spectral types.
         journals                             Description of all used journals in the database

To join tables, any columns sharing the same name are possible links between tables.
To find the other possible joins, the `~astroquery.simbad.SimbadClass.list_linked_tables` method
can be useful. Here we look for possible links with the ``mesDiameter`` table

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.list_linked_tables("mesDiameter")
    <Table length=1>
     from_table from_column target_table target_column
       object      object      object        object
    ----------- ----------- ------------ -------------
    mesDiameter      oidref        basic           oid

The output indicates that the ``mesDiameter`` table can be linked to ``basic`` with the following
join statement: ``[...] mesDiameter JOIN basic ON mesDiameter.oidref = basic.oid [...]``.

.. graphviz:: simbad-er.gv
    :layout: neato
    :caption: A quick view of SIMBAD's tables. Hover the links to see the linked columns.
    :alt: This interactive graph summarizes the information that can be obtained with `~astroquery.simbad.SimbadClass.list_tables` and `~astroquery.simbad.SimbadClass.list_linked_tables`.

Available columns
-----------------

`~astroquery.simbad.SimbadClass.list_columns` lists the columns in all or a subset of SIMBAD tables.
Calling it with no argument returns the 289 columns of SIMBAD. To restrict the output to
some tables, add their name. To get the columns of the tables ``ref`` and ``biblio``:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.list_columns("ref", "biblio")
    <Table length=13>
    table_name column_name   datatype  ...  unit         ucd       
      object      object      object   ... object       object     
    ---------- ----------- ----------- ... ------ -----------------
        biblio      biblio     VARCHAR ...         meta.bib.bibcode
        biblio      oidref      BIGINT ...              meta.record
           ref      "year"    SMALLINT ...           time.publiYear
           ref    abstract UNICODECHAR ...              meta.record
           ref     bibcode        CHAR ...         meta.bib.bibcode
           ref         doi     VARCHAR ...             meta.ref.doi
           ref     journal     VARCHAR ...         meta.bib.journal
           ref   last_page     INTEGER ...            meta.bib.page
           ref    nbobject     INTEGER ...        meta.id;arith.sum
           ref      oidbib      BIGINT ...              meta.record
           ref        page     INTEGER ...            meta.bib.page
           ref       title UNICODECHAR ...               meta.title
           ref      volume     INTEGER ...          meta.bib.volume

`~astroquery.simbad.SimbadClass.list_columns` can also be called with a keyword argument.
This returns columns from any table for witch the given keyword is either in the table name,
in the column name or in its description. This is not case-sensitive.

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.list_columns(keyword="Radial velocity")
    <Table length=9>
      table_name    column_name   ...  unit                   ucd
        object         object     ... object                 object
    ------------- --------------- ... ------ -------------------------------------
            basic     rvz_bibcode ...          meta.bib.bibcode;spect.dopplerVeloc
            basic         rvz_err ... km.s-1         stat.error;spect.dopplerVeloc
            basic    rvz_err_prec ...
            basic        rvz_qual ...            meta.code.qual;spect.dopplerVeloc
            basic      rvz_radvel ... km.s-1                spect.dopplerVeloc.opt
            basic rvz_radvel_prec ...
            basic        rvz_type ...
            basic  rvz_wavelength ...        instr.bandpass;spect.dopplerVeloc.opt
    mesVelocities          origin ...                                    meta.note

Example TAP queries
-------------------

This section lists more complex queries by looking at use cases from former astroquery issues.

Getting all bibcodes containing a certain type of measurement for a given object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The measurement tables -- the ones with names starting with ``mes``-- have a bibcode column
that corresponds to the paper in which the information was found.

This query joins the tables ``ident`` to get all possible names of the object and ``mesrot``
that is the measurement table for rotations. Their common column is ``oidref``.

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> query = """SELECT DISTINCT bibcode AS "Rotation Measurements Bibcodes"
    ...     FROM ident JOIN mesrot USING(oidref)
    ...     WHERE id = 'Sirius';
    ...     """
    >>> bibcodes = Simbad.query_tap(query)
    >>> bibcodes.sort("Rotation Measurements Bibcodes")
    >>> bibcodes
    <Table length=8>
    Rotation Measurements Bibcodes
                object            
    ------------------------------
               1970CoAsi.239....1B
               1970CoKwa.189....0U
               1995ApJS...99..135A
               2002A&A...393..897R
               2005yCat.3244....0G
               2011A&A...531A.143D
               2016A&A...589A..83G
               2023ApJS..266...11B

This returns six papers in which the SIMBAD team found rotation data for Sirius.

Criteria on region, measurements and object types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here we search for objects that are not stars and have a redshift<0.4 in a cone search. All this information
is in the ``basic`` column. The ``star..`` syntax refers to any type of star.

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> query = """SELECT ra, dec, main_id, rvz_redshift, otype
    ...         FROM basic
    ...         WHERE otype != 'star..'
    ...         AND CONTAINS(POINT('ICRS', basic.ra, basic.dec), CIRCLE('ICRS', 331.92, +12.44 , 0.25)) = 1
    ...         AND rvz_redshift <= 0.4"""
    >>> Simbad.query_tap(query)
    <Table length=11>
           ra              dec                 main_id          rvz_redshift otype
          deg              deg
        float64          float64                object            float64    object
    --------------- ------------------ ------------------------ ------------ ------
    331.86493815752     12.61105991847 SDSS J220727.58+123639.8      0.11816    EmG
    331.80665742545      12.5032406228 SDSS J220713.60+123011.7       0.1477    EmG
         332.022027           12.29211 SDSS J220805.28+121731.5      0.12186      G
         331.984091          12.573282 SDSS J220756.18+123423.8      0.13824      G
    331.87489584192      12.5830568196 SDSS J220729.97+123458.8      0.03129      G
    331.77233978222 12.314639195540002  2MASX J22070538+1218523        0.079      G
         331.796426          12.426641 SDSS J220711.14+122535.9      0.07886      G
    331.68420630414      12.3609942055  2MASX J22064423+1221397       0.1219      G
         331.951995          12.431051 SDSS J220748.47+122551.7      0.16484      G
         332.171805          12.430204 SDSS J220841.23+122548.7      0.14762      G
         332.084711          12.486509 SDSS J220820.33+122911.4      0.12246      G

This returns a few galaxies 'G' and emission-line galaxies 'EmG'.

Get the members of a galaxy cluster
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All membership information is in the ``h_link`` table. We first need to retrieve the ``oidref``
corresponding to the parent cluster SDSSCGB 350. This is done is the sub-query between parenthesis.
Then, the ``basic`` table is joined with ``h_link`` and the sub-query result.

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> query = """SELECT main_id AS "child id",
    ...         otype, ra, dec, membership,
    ...         cluster_table.id AS "parent cluster"
    ...         FROM (SELECT oidref, id FROM ident WHERE id = 'SDSSCGB 350') AS cluster_table,
    ...         basic JOIN h_link ON basic.oid = h_link.child
    ...         WHERE h_link.parent = cluster_table.oidref;
    ...         """
    >>> Simbad.query_tap(query)
    <Table length=7>
            child id         otype          ra         ... membership parent cluster
                                           deg         ...  percent
             object          object      float64       ...   int16        object
    ------------------------ ------ ------------------ ... ---------- --------------
               SDSSCGB 350.4      G 243.18303333333336 ...         75    SDSSCGB 350
    SDSS J161245.36+281652.4      G 243.18900464937997 ...         75    SDSSCGB 350
               SDSSCGB 350.1      G 243.18618110644002 ...         75    SDSSCGB 350
                LEDA 1831614      G         243.189153 ...         75    SDSSCGB 350
                LEDA 1832284      G         243.187819 ...        100    SDSSCGB 350
               SDSSCGB 350.1      G 243.18618110644002 ...        100    SDSSCGB 350
                LEDA 1831614      G         243.189153 ...        100    SDSSCGB 350

Query a long list of objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To query a list of objects (or coordinates, of bibliographic references), we can use the
ADQL criteria ``IN`` like so:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.query_tap("SELECT main_id, otype FROM basic WHERE main_id IN ('M1', 'M2', 'M3')")
    <Table length=3>
    main_id otype
     object object
    ------- ------
      M   1    SNR
      M   2    GlC
      M   3    GlC


And that would work perfectly... until we reach the character limit for the ADQL query. This
is one of the example use case where the upload table capability is very useful. You can create/use
an `~astropy.table.Table` containing the desired list and use it in a ``JOIN`` to replace an ``IN``:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> from astropy.table import Table
    >>> list_of_objects = Table([["M1", "M2", "M3"]], names=["Messier_objects"])
    >>> query = """SELECT main_id, otype FROM basic
    ...            JOIN TAP_UPLOAD.messiers
    ...            ON basic.main_id = TAP_UPLOAD.messiers.Messier_objects
    ...         """
    >>> Simbad.query_tap(query, messiers=list_of_objects)
    <Table length=3>
    main_id otype
     object object
    ------- ------
      M   1    SNR
      M   2    GlC
      M   3    GlC

.. note::
   The uploaded tables are limited to 200000 lines. You might need to break your query into smaller
   chunks if you have longer tables.