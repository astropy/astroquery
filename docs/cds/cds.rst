
.. doctest-skip-all
.. _astroquery.cds:

********************************
CDS Queries (`astroquery.cds`)
********************************

Getting started
===============

This module can be used to query the MocServer from the ``Centre de Données de Strasbourg`` (CDS).
This server aims to return a list of data sets (i.e. catalog, image, HiPS) matching specific constraints.
These constraints can be of two types :

- a spatial constraint referring for instance to a cone region, a polygon or a moc (i.e. a mocpy object. See https://github.com/cds-astro/mocpy)
- a constraint acting on the properties (or meta properties) of the data sets. This type of constraints allows the user to retrieve data sets satisfying a specific algebraic expression involving the data sets properties.


Requirements
----------------------------------------------------
The following packages are required for the use of this module:

* mocpy
* pyvo
* regions

Performing a cds query on a simple cone region
====================================================

.. code:: python3

    from astropy import coordinates
    from regions import CircleSkyRegion

    from astroquery.cds import cds
    from astroquery.cds import Constraints, Cone
    from astroquery.cds import OutputFormat

A cone search region is defined using the CircleSkyRegion module from
the regions package. Here, a cone is defined by a location (dec, ra)
expressed in degrees and a radius.

.. code:: python3

    center = coordinates.SkyCoord(10.8, 32.2, unit="deg")
    radius = coordinates.Angle(1.5, 'deg')
    circle_sky_region = CircleSkyRegion(center, radius)

This cone region can be seen as a spatial constraint. The aim of the cds relies on returning all the data sets
which contain at least one source (i.e. a spatial object) lying in the cone region. This internal CDS service involves a
server named MocServer which performs all the queries and returns
the list of matched data sets.

A Constraints object allows us to specify the constraints that will be
sent to the cds so that it returns all the matched data sets. For
the purpose of this tutorial, we will only bind a Cone spatial
constraint to our query but keep in mind that it is also possible to
associate to the Constraints object a constraint on the data sets
properties. It is even possible to associate both of them (i.e. a
spatial constraint and a properties constraint) as we will see in the next section.

.. code:: python3

    cds_constraints = Constraints(sc=Cone(circle_sky_region, intersect='overlaps'))

Here we have created a Constraints object and we have bound a Cone
spatial constraint to it. The argument ``intersect`` specifies that data sets have to intersect the cone region to be selected by the mocserver and returned to the user.
Other possible ``intersect`` argument values are ``covers`` and ``enclosed``.

Now it is time to perform the query. We call the query\_region method
from the cds object that we imported and pass it the cds\_constraints object with an OutputFormat object which specifies what we
want to retrieve. In the code below, we have chosen to retrieve all the
``ID``, ``dataproduct_type`` and ``moc_sky_fraction`` properties from
the matching data sets.

.. code:: python3

    datasets_d = cds.query_region(cds_constraints,
                                      OutputFormat(format=OutputFormat.Type.record,
                                                   field_l=['ID', 'dataproduct_type', 'moc_sky_fraction', 'cs_service_url']))
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


We get a dictionary of cds.dataset.Dataset objects indexed by
their IDs. To get the properties of one data set, say
``CDS/B/eso/eso_arc``, just do the following :

.. code:: python3

    print(datasets_d['CDS/B/eso/eso_arc'].properties)


.. parsed-literal::

    {'ID': 'CDS/B/eso/eso_arc', 'dataproduct_type': 'catalog', 'moc_sky_fraction': 0.008365}


It is also possible to get only the data sets ``IDs``, the ``number``
of matching data sets or just the ``moc`` resulting from the union of all
the mocs of the matching data sets. (See the OutputFormat definition class and its ``format`` type).

The result of a cds query depends on the OutputFormat object we have passed to the query_region method.
If we query for the ``IDs`` of the data sets then we get a python list of all the matched data sets ``IDs``.
If a user query for the ``number`` of data sets, he gets an int.
If you want all the records of the matched data sets (the ``IDs`` plus its properties/fields) you get
as we have seen above, a dictionary of cds.dataset.Dataset objects indexed by their ``IDs``.

This cds.dataset.Dataset object allows you to query a specific service (if available for this data set) such as a tap service, a cone search service...
The service then returns a VOTable containing all the matching sources of the data set you have submitted the query.
We can see that the data set CDS/B/cb/lmxbdata contains the field cs_service_url referring the url of the cone search service for this data set.
To query this service, we call the following command, specifying that we want to query the Simple Cone Search service with a cone of center `pos` and of radius `radius`.

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

The returned VOTable shows us why the data set has been returned by the mocserver from the cds:

There is a source from the data set 'CDS/B/cb/lmxbdata' that lies into the cone constraint defined for the past mocserver query.


Mixing a spatial constraint with a constraint on properties
===========================================================

We now want to bind a spatial and a properties constraints to the
Constraints object so that our cds query returns all the data sets
matching those two constraints.

.. code:: python3

    from astroquery.cds import cds

    from astroquery.cds import Constraints, Moc, PropertyConstraint
    from astroquery.cds import OutputFormat

As for the spatial constraint, let is define a moc from an url

.. code:: python3

    moc = Moc.from_url(url='http://alasky.u-strasbg.fr/SDSS/DR9/color/Moc.fits', intersect='overlaps')

Let is define a properties constraint. Here we want to retrieve all
data sets satisfying the following expression : (ID = \*CDS\* &&
moc\_sky\_fraction <= 0.01)

In other words, we want to retrieve all the data sets having the word CDS in their IDs and
having a moc\_sky\_fraction of at least 1%.

A properties constraint is written like an algebraic tree of
equalities/inequalities. For instance, the above algebraic expression
will be defined such as :

.. code:: python3

    properties_constraint = PropertyConstraint(ParentNode(
        OperandExpr.Inter,
        ChildNode("moc_sky_fraction <= 0.01"),
        ChildNode("ID = *CDS*")
    ))
    # or simply write the algebraical expression as a string
    properties_constraint = PropertyConstraint('ID = *CDS* && moc_sky_fraction <= 0.01')

Once we defined our two constraints (i.e. a spatial one and a properties
one), we can bind them to a Constraints object

.. code:: python3

    # moc is a cds.Moc object created from a mocpy object, a json moc, a local path or an url to a FITS file
    cds_constraints = Constraints(sc=moc, pc=properties_constraint)

And simply call the cds object to run the query as usual

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


We have obtained from the cds the data sets which intersect the moc
found at the url http://alasky.u-strasbg.fr/SDSS/DR9/color/Moc.fits,
have the CDS word in their `ID` and finally, have a `moc_sky_fraction`
with at least 1%.

Reference/API
=============

.. automodapi:: astroquery.cds
    :no-inheritance-diagram:
