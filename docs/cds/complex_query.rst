
Performing a complex CDS MOC query involving a constraint on meta datas
-----------------------------------------------------------------------

We now want to bind a spatial and a properties constraints to the
Constraints object so that our mocserver query returns all the datasets
matching those two constraints.

.. code:: ipython3

    from astroquery.cds import cds

We want to retrieve the 'number' of the data sets :

-  belonging to the MOC defined at the url :
   http://alasky.u-strasbg.fr/SDSS/DR9/color/Moc.fits
-  having the word 'CDS' in their IDs (meta data)
-  covering at most 1% of the sky (meta data)

Meta data constraints are written like an algebraic expression. For more
details about how to write them, go to :
http://alasky.unistra.fr/MocServer/query

With that in mind, we can obtain these data sets by typing:

.. code:: ipython3

    num_datasets = cds.query_region(type=cds.RegionType.MOC,
                                    url='http://alasky.u-strasbg.fr/SDSS/DR9/color/Moc.fits',
                                    format=cds.ReturnFormat.number,
                                    meta_data='ID = *CDS* && moc_sky_fraction <= 0.01')
    num_datasets




.. parsed-literal::

    13701


