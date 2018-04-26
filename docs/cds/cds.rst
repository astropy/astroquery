
.. doctest-skip-all
.. _astroquery.cds:

********************************
Querying the CDS MOC Service (`astroquery.cds`)
********************************

Getting started
===============

This module provides a python interface for querying the MOC service from the `Centre de Données de Strasbourg` (CDS).
The CDS MOC service is available at : http://alasky.unistra.fr/MocServer/query

The CDS MOC Server tool aims at retrieving as fast as possible the list of astronomical data sets (catalogs, surveys, ...) having at least one observation in a specifical sky region. The default result is an ID list but one can ask for different output formats :

* The number of the data sets.
* A dictionary containing the lists of meta-data for all the resulting data sets. These lists of meta-data are each indexed by the ID of the data set they are referring to.
* A MOC resulting from the union/intersection of all the MOC of the resulting data sets.
* An ID list (default result).

MOC Server is based on Multi-Order Coverage maps (MOC) described in the IVOA REC standard.

The CDS MOC Server tool contains a list of meta-data and a MOC for approx ~20000 data sets (catalogs, surveys, ...).
When requesting for the data sets having at least one observation in a sky region, the CDS MOC Server does the following :
    1. The sky region (cone, polygon, MOC) is converted into a MOC at the order 29 (max order)
    2. For each of the 20000 data sets, the MOC server performs the intersection of the MOC from the data set with the one defined at the past step.
    3. The data sets matching the query are those giving a non-empty MOC intersection.
   
In addition to filtering astronomical data sets with a specifical sky region, it is also possible to search for data sets having a specifical set of meta-data. For instance, one can ask for the data sets covering at least 50% of the sky (moc_sky_fraction meta-data >= 50%). Examples of meta-data (or data set properties) are listed here : http://alasky.unistra.fr/MocServer/query?get=example&fmt=ascii

Requirements
----------------------------------------------------
The following packages are required for the use of the ``cds``:

* mocpy : https://github.com/cds-astro/mocpy
* pyvo : https://pyvo.readthedocs.io/en/latest/
* regions : https://astropy-regions.readthedocs.io/en/latest/installation.html

Performing a ``cds`` query on a simple cone region
====================================================

.. code:: python3

    from astropy import coordinates
    from regions import CircleSkyRegion

    from astroquery.cds import cds
    from astroquery.cds import Constraints, Cone
    from astroquery.cds import OutputFormat

A cone region is defined using the CircleSkyRegion module from
the regions package. Here, a cone is defined by a location (dec, ra)
expressed in degrees plus a radius.

.. code:: python3

    center = coordinates.SkyCoord(10.8, 32.2, unit="deg")
    radius = coordinates.Angle(1.5, 'deg')
    circle_sky_region = CircleSkyRegion(center, radius)

This cone region can be seen as a spatial constraint. The aim of the ``cds`` relies on returning all the data sets containing at least one observation (i.e. a spatial object) lying in the cone region.

A Constraints object allows us to specify the constraints that will be
sent to the CDS MOC service before the MOC server performs the query (see the MOC server heuristic explained above for selecting data sets). For the purpose of this tutorial, we will only bind a Cone spatial
constraint to our Constraints object but keep in mind that it is also possible to bind to it a meta-data constraint. It is even possible to instanciate a Constraints object linked to both of them (i.e. a
spatial constraint and a property/meta-data constraint) as we will see in the next section.

.. code:: python3

    cds_constraints = Constraints(sc=Cone(circle_sky_region, intersect='overlaps'))

Here we have created a Constraints object and we have bound a Cone
spatial constraint to it. The argument `intersect` specifies the rule for the CDS MOC service to select or not a data set. Three values for this parameter are possible : ``overlaps``, ``covers`` or ``enclosed``. For intersect=``overlaps``, a data set is returned when its MOC overlaps the spatial constraint defined MOC.

Now it is time to perform the query. We call the query\_region method
from the ``cds`` by passing to it the cds\_constraints object and an OutputFormat object which specifies what we
want to retrieve. 

As explained in the introduction, one can ask for different output formats. The OutputFormat object presents different optional parameters:

* format : specify if the user wants a list of data sets ID (default), the number of data sets, a MOC, etc...
* field_l : the list of meta data fields to return if the user asks for the meta datas of the matching data sets.
* moc_order : the order of the MOC to return if the user asks for a MOC
* max_rec : the max number of data sets that the CDS MOC service is allowed to return

In the code below, we have chosen to retrieve the
``ID``, ``dataproduct_type``, ``moc_sky_fraction`` meta data fields from
the matching data sets.

.. code:: python3

    # We are asking for a dictionary of data sets. Each data sets is indexed by its ID
    datasets_d = cds.query_region(cds_constraints,
                                  OutputFormat(format=OutputFormat.Type.record,
                                               field_l=['ID', 'dataproduct_type', 'moc_sky_fraction']))
    import pprint;
    pprint.pprint(datasets_d)


.. parsed-literal::

    {'CDS/B/assocdata/obscore': <cds.dataset.Dataset object at 0x7fb6a2379c88>,
     'CDS/B/cb/lmxbdata': <cds.dataset.Dataset object at 0x7fb6a2379ef0>,
     'CDS/B/cfht/cfht': <cds.dataset.Dataset object at 0x7fb6a2379e80>,
     'CDS/B/cfht/obscore': <cds.dataset.Dataset object at 0x7fb6a2379eb8>,
     'CDS/B/chandra/chandra': <cds.dataset.Dataset object at 0x7fb6a2379da0>,
     'CDS/B/eso/eso_arc': <cds.dataset.Dataset object at 0x7fb6a45b8f98>,
     'CDS/B/gcvs/gcvs_cat': <cds.dataset.Dataset object at 0x7fb6a44845f8>,
     'CDS/B/gcvs/nsv_cat': <cds.dataset.Dataset object at 0x7fb6a44847f0>,
     'CDS/B/gemini/obscore': <cds.dataset.Dataset object at 0x7fb6a4484dd8>,
     'CDS/B/hst/hstlog': <cds.dataset.Dataset object at 0x7fb6a4484e80>,
     'CDS/B/hst/obscore': <cds.dataset.Dataset object at 0x7fb6a4484f98>,
      ...}


To get the meta-data/properties of one data set, say
``CDS/B/eso/eso_arc``, just do the following:

.. code:: python3

    print(datasets_d['CDS/B/eso/eso_arc'].properties)


.. parsed-literal::

    {'ID': 'CDS/B/eso/eso_arc', 'dataproduct_type': 'catalog', 'moc_sky_fraction': 0.008365}


If I would just have wanted the ID list of the matching data sets, I would have written:

.. code:: python3

    # We are asking for the ID list of the matching data sets.
    id_l = cds.query_region(cds_constraints,
                            OutputFormat(format=OutputFormat.Type.id))
                            
                 
Or for a mocpy.MOC object resulting from the union of all the MOCs of the matching data sets:
 
.. code:: python3

    # We are asking for a mocpy.MOC object of order 15
    moc = cds.query_region(cds_constraints,
                           OutputFormat(format=OutputFormat.Type.moc), moc_order=15)


When requesting for data set records (i.e. a dictionary of cds.dataset.Dataset objects each indexed by the data set ID it is referring to), it is possible to query specific services on these data sets (tap, simple cone search, ...). Let is performing a new CDS MOC service query in which we want to retrieve all the meta-data fields of the matching data sets. After that, we will print the list of meta-data of ``CDS/B/cb/lmxbdata``:

.. code:: python3

    # We are asking for all data set records
    datasets_d = cds.query_region(cds_constraints,
                                  OutputFormat(format=OutputFormat.Type.record))
    import pprint;
    pprint.pprint(datasets_d['CDS/B/cb/lmxbdata'].properties)
    

.. parsed-literal::

    {'ID': 'CDS/B/cb/lmxbdata',
 'TIMESTAMP': 1524657845000.0,
 'bib_reference': '2003A&A...404..301R',
 'cs_service_url': 'http://vizier.u-strasbg.fr/viz-bin/votable/-A?-source=B%2Fcb%2Flmxbdata&',
 'data_ucd': ['src.spType',
              'pos.eq.ra',
              'meta.id',
              'src.class',
              'phys.mass;arith.ratio',
              'phys.mass',
              'pos.eq.dec',
              'time.period',
              'phys.luminosity;arith.ratio',
              'phot.mag;em.opt.V',
              'src.orbital.inclination'],
 'dataproduct_type': 'catalog',
 'moc_access_url': 'http://alasky.unistra.fr/footprints/tables/vizier/B_cb_lmxbdata/MOC?nside=2048',
 'moc_order': 11.0,
 'moc_sky_fraction': 2.066e-06,
 'nb_rows': 108.0,
 'obs_astronomy_kw': ['Binaries:cataclysmic', 'Novae'],
 'obs_collection': 'CV',
 'obs_collection_label': ['CB', 'CV'],
 'obs_copyright_url': 'http://cdsarc.u-strasbg.fr/viz-bin/Cat?B%2Fcb',
 'obs_description': 'Catalogue of Low-Mass X-Ray Binaries',
 'obs_description_url': 'http://cdsarc.u-strasbg.fr/viz-bin/Cat?B%2Fcb',
 'obs_id': 'B/cb/lmxbdata',
 'obs_initial_dec': 32.90817697165526,
 'obs_initial_fov': 0.028629053431811713,
 'obs_initial_ra': 65.4345703125,
 'obs_label': 'lmxbdata',
 'obs_release_date': '2010-03-21T13:03:47Z',
 'obs_title': 'Cataclysmic Binaries, LMXBs, and related objects (Ritter+, '
              '2004) (lmxbdata)',
 'publisher_id': 'ivo://CDS',
 'tap_tablename': 'viz7.B/cb/lmxbdata',
 'vizier_popularity': 3.0,
 'web_access_url': 'http://vizier.u-strasbg.fr/viz-bin/VizieR-2?-source=B%2Fcb%2Flmxbdata&'}
 
 
We can see that the data set ``CDS/B/cb/lmxbdata`` contains a field called ``cs_service_url`` and refers to the url of the cone search service for this data set.
Querying this cone search service on this data set is pretty simple. If we want to get the observations from ``CDS/B/cb/lmxbdata`` belonging in the cone of center ``pos`` and of radius ``radius`` we do:

.. code:: python3

    votable = datasets_d['CDS/B/cb/lmxbdata'].search(Dataset.ServiceType.cs, pos=(10.8, 32.2), radius=1.5)
    votable


.. parsed-literal::

    <Table masked=True length=1>
    _RAJ2000 _DEJ2000    _r      Name   ...   mag1   Orb.Per  SpType2  Refs
      deg      deg      deg             ...   mag       d
    float64  float64  float64  bytes12  ... float32  float64   bytes7 bytes4
    -------- -------- ------- --------- ... ------- --------- ------- ------
     11.2033  33.0092 0.87761 0042+3244 ...    18.8 11.600000           Refs


The returned VOTable shows us why the data set has been returned by the CDS MOC service.
Indeed, one can see that there is one source from the data set 'CDS/B/cb/lmxbdata' that is located in the same cone that we used for the the past ``cds`` query.


Mixing a spatial constraint with a meta-data constraint
===========================================================

We now want to bind a spatial and a meta-data constraint to the
Constraints object so that our ``cds`` query returns all the data sets
matching those two different constraints.

.. code:: python3

    from astroquery.cds import cds

    from astroquery.cds import Constraints, Moc, PropertyConstraint
    from astroquery.cds import OutputFormat

As for the spatial constraint, let is define a moc from an url

.. code:: python3
    
    # moc is a cds.Moc object created an url to a FITS file
    moc = Moc.from_url(url='http://alasky.u-strasbg.fr/SDSS/DR9/color/Moc.fits', intersect='overlaps')

Let is define the meta-data/properties constraint. Here we want to retrieve the
data sets having the word CDS in their IDs and
having a moc\_sky\_fraction of at least 1%. This corresponds to the following algebraic expression:
(ID = \*CDS\* && moc\_sky\_fraction <= 0.01)

This constraint is then defined like the following:

.. code:: python3

    properties_constraint = PropertyConstraint(ParentNode(
        OperandExpr.Inter,
        ChildNode("moc_sky_fraction <= 0.01"),
        ChildNode("ID = *CDS*")
    ))
    # or simply pass the algebraical expression as a string
    properties_constraint = PropertyConstraint('ID = *CDS* && moc_sky_fraction <= 0.01')

Let is bind those constraints to a Constraints object.

.. code:: python3

    cds_constraints = Constraints(sc=moc, pc=properties_constraint)

And do a ``cds`` query on this Constraints object:

.. code:: python3

    response = cds.query_region(cds_constraints,
                                OutputFormat(format=OutputFormat.Type.id))
    response


.. parsed-literal::

    ['CDS/B/avo.rad/catalog',
     'CDS/B/avo.rad/wsrt',
     'CDS/B/bax/bax',
     'CDS/B/cb/cbdata',
     'CDS/B/cb/lmxbdata',
     'CDS/B/cb/pcbdata',
     'CDS/B/cfht/cfht',
     'CDS/B/cfht/obscore',
     ...]


We have obtained the data sets having at least one observation in the MOC
found at the url http://alasky.u-strasbg.fr/SDSS/DR9/color/Moc.fits,
having the CDS word in their IDs and finally, covering at least 1% of the sky.

Reference/API
=============

.. automodapi:: astroquery.cds
    :no-inheritance-diagram:
