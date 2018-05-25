.. _query_on_meta_data:

Performing a complex CDS MOC query involving a constrain on meta data
----------------------------------------------------------------------

We now want to use the `CDS MOC Service`_ to filter data sets having a specific
set of meta data

.. code:: ipython3

    from astroquery.cds import cds

As an example, we would like to retrieve the number of data sets matching the query. These data sets
must :

-  belong to this `MOC_FILE`_
-  have the word 'CDS' in their IDs (constrain on the ``ID`` meta data)
-  cover at most 1% of the sky (constrain on the ``moc_sky_fraction`` meta data)

Meta data constrain is written like an algebraic expression involving the set of meta data to constrain. For more
details about how to write them, go to the `CDS MOC Service`_. Please refer to the section
Advanced queries & parameters part ii.

With that in mind, we can obtain these data sets by typing:

.. _MOC_FILE:
    http://alasky.u-strasbg.fr/SDSS/DR9/color/Moc.fits

.. code:: ipython3

    num_datasets = cds.query_region(region_type=cds.RegionType.MOC,
                                    url='http://alasky.u-strasbg.fr/SDSS/DR9/color/Moc.fits',
                                    output_format=cds.ReturnFormat.number,
                                    meta_data='ID = *CDS* && moc_sky_fraction <= 0.01')
    num_datasets




.. parsed-literal::

    13701

.. include:: references.rst

