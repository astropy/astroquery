
.. doctest-skip-all
.. _astroquery.cds:

********************************
CDS Queries (`astroquery.cds`)
********************************

Getting started
===============

This module can be used to query the MocServer from the ``Centre de Données de Strasbourg`` (CDS).
This server aim to return a list of datasets (i.e. catalog, image, HiPS) matching specific constraints.
These constraints can be of two types :

- a spatial constraint referring for instance to a cone region, a polygon or a moc.
- a constraint acting on properties (or meta properties) of the datasets. This type of constraints allow the user to retrieve datasets satisfying a specific algebraic expression of properties.


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

    from astroquery.cds.core import cds

    from astroquery.cds.constraints import Constraints
    from astroquery.cds.spatial_constraints import Cone
    from astroquery.cds.output_format import OutputFormat

A cone search region is defined using the CircleSkyRegion module from
the regions package. Here, a cone is defined by a location (dec, ra)
expressed in degree and a radius.

.. code:: python3

    center = coordinates.SkyCoord(10.8, 32.2, unit="deg")
    radius = coordinates.Angle(1.5, 'deg')
    circle_sky_region = CircleSkyRegion(center, radius)

This above cone region can be seen as a spatial constraint for the
cds. The aim of the cds relies on returning all the datasets
which contain at least one source (i.e. a spatial object) lying in the
previously defined cone region. This internal CDS service involves a
server named MocServer which performs all the queries and returns 
the matching datasets.

A Constraints object allow us to specify the constraints that will be
sent to the cds so that it returns all the matching datasets. For
the purpose of this tutorial, we will only bind a Cone spatial
constraint to our query but keep in mind that it is also possible to
associate to the Constraints object a constraint on the dataset
properties. It is even possible to associate both of them (i.e. a
spatial constraint and a properties constraint) as we will see in the next section.

.. code:: python3

    cds_constraints = Constraints(sc=Cone(circle_sky_region, intersect='overlaps'))

Here we have created a Constraints object and we have bound to it a Cone
spatial constraint. The argument ``intersect`` specifies that the
datasets need to intersect the cone region so that they match the
cds query. Other possible ``intersect`` argument values are
``covers`` and ``enclosed``.

Now it is time to perform the query. We call the query\_region method
from the cds object that we imported and pass it the cds\_constraints object with an OutputFormat object which specify what we
want to retrieve. In the code below, we have chosen to retrieve all the
``ID``, ``dataproduct_type`` and ``moc_sky_fraction`` properties from
the matching datasets.

.. code:: python3

    datasets_d = cds.query_region(cds_constraints,
                                      OutputFormat(format=OutputFormat.Type.record,
                                                   field_l=['ID', 'dataproduct_type', 'moc_sky_fraction']))
    import pprint;
    pprint.pprint(datasets_d)


.. parsed-literal::

    Final Request payload before requesting to alasky
    {'DEC': '32.2',
     'RA': '10.8',
     'SR': '1.5',
     'casesensitive': 'true',
     'fields': 'ID, moc_sky_fraction',
     'fmt': 'json',
     'get': 'record',
     'intersect': 'overlaps'}
    <Response [200]>
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
their IDs. To get the properties of one dataset, say
``CDS/B/eso/eso_arc``, just do the following :

.. code:: python3

    print(datasets_d['CDS/B/eso/eso_arc'].properties)


.. parsed-literal::

    {'ID': 'CDS/B/eso/eso_arc', 'dataproduct_type': 'catalog', 'moc_sky_fraction': 0.008365}


It is also possible to get only the datasets ``ID``\ s, the ``number``
of matching datasets or just the ``moc`` resulting from the union of all
the mocs of the matching datasets. (See the OutputFormat definition class and its ``format`` type).

The result of a cds query depends on the OutputFormat object we have passed to the query_region method.
If we query for the ``ID``\ s of the datasets then we get a python list of all the  ``ID``\ s matching the condition.
If a user query for the ``number`` of datasets, he gets an int.
If you want all the record of the matching datasets (the ``ID`` \s plus its properties/fields) you get
as we have seen above, a dictionary indexed by the ``ID`` \s of the datasets and as each value a Dataset object.
This Dataset object allows you to query a specific service (if available for this dataset) such as a tap service, a cone search service...
The service then returns a VOTable containing all the matching sources of the dataset you have submitted a query.


.. code:: python3

    response = cds.query_region(cds_constraints,
                                      OutputFormat(format=OutputFormat.Type.moc,
                                                   moc_order=14))
    import pprint;
    pprint.pprint(response)


.. parsed-literal::

    Final Request payload before requesting to alasky
    {'DEC': '32.2',
     'RA': '10.8',
     'SR': '1.5',
     'casesensitive': 'true',
     'fmt': 'json',
     'get': 'moc',
     'intersect': 'overlaps',
     'order': 14}
    <Response [200]>
    {'10': [655471,
            ...,
            5201751],
     '11': [2621871,
            ...,
            20807031],
     '14': [],
     '6': [2562, 2563, 2568, 2569],
     '7': [10246, 10247, 10264, 10266, 10281, 10284, 10288],
     '8': [40971,
           ...,
           325085],
     '9': [163871,
           ...,
           1300351]}

Mixing a spatial constraint with a constraint on properties
===========================================================

We now want to bind a spatial and a properties constraints to the
Constraints object so that our cds query returns all the datasets
matching those two constraints.

.. code:: python3

    from astropy import coordinates
    from regions import CircleSkyRegion

    from astroquery.cds.core import cds

    from astroquery.cds.constraints import Constraints
    from astroquery.cds.spatial_constraints import Moc
    from astroquery.cds.property_constraint import *
    from astroquery.cds.output_format import OutputFormat

As for the spatial constraint, let is define a moc from an url

.. code:: python3

    moc = Moc.from_url(url='http://alasky.u-strasbg.fr/SDSS/DR9/color/Moc.fits', intersect='overlaps')

Let is define a properties constraint. Here we want to retrieve all
datasets satisfying the following expression : (ID = \*CDS\* &&
moc\_sky\_fraction <= 0.01)

In other words, we want to retrieve all datasets having the word CDS in their IDs and
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

Once we defined our two constraints (i.e. a spatial one and a properties
one), we can bind them to a Constraints object

.. code:: python3

    cds_constraints = Constraints(sc=moc, pc=properties_constraint)

And simply call the cds object to run the query

.. code:: python3

    response = cds.query_region(cds_constraints,
                                      OutputFormat(format=OutputFormat.Type.id))
    response


.. parsed-literal::

    Final Request payload before requesting to alasky
    {'casesensitive': 'true',
     'expr': 'moc_sky_fraction <= 0.01 && ID = *CDS*',
     'fmt': 'json',
     'get': 'id',
     'intersect': 'overlaps',
     'url': 'http://alasky.u-strasbg.fr/SDSS/DR9/color/Moc.fits'}




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



We have obtained from the cds the datasets which intersect the moc
found at the url http://alasky.u-strasbg.fr/SDSS/DR9/color/Moc.fits,
have the 'CDS' word in their IDs and finally, have a moc\_sky\_fraction
with at least 1%.

Reference/API
=============

.. automodapi:: astroquery.cds
    :no-inheritance-diagram:
