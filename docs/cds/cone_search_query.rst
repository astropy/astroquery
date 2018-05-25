.. _query_cone_search:

Performing a CDS MOC query on a simple cone region
--------------------------------------------------

.. code:: ipython3

    from astropy import coordinates
    from astroquery.cds import cds


We define a cone in astropy as the combination of a center position and
a radius.

.. code:: ipython3

    center = coordinates.SkyCoord(10.8, 32.2, unit='deg')
    radius = coordinates.Angle(1.5, unit='deg')

The `CDS MOC Service`_ aims at returning all the data sets containing at
least one observation located in the previously defined
cone region.

For that purpose, we will call the :meth:`~astroquery.cds.CdsClass.query_region` method of ``cds`` with
the following parameters:

.. code:: ipython3

    cds.query_region(region_type=cds.RegionType.Cone,
                     center=center,
                     radius=radius)


And we get an ID list of the data sets matching the query:

.. parsed-literal::

    ['CDS/B/assocdata/obscore',
     'CDS/B/cb/lmxbdata',
     'CDS/B/cfht/cfht',
     'CDS/B/cfht/obscore',
     'CDS/B/chandra/chandra',
     'CDS/B/eso/eso_arc',
     'CDS/B/gcvs/gcvs_cat',
     'CDS/B/gcvs/nsv_cat',
     'CDS/B/gemini/obscore',
     ...]



The ``region_type`` parameter is required. It informs the :meth:`~astroquery.cds.CdsClass.query_region`
method about the type of region we are querying the `CDS MOC service`_ and
thus constraints the following parameters of the method.

You can find below the parameters associated to all the possible ``region_type`` parameter values :

-  ``cds.RegionType.Cone`` :

   -  center : `astropy.coordinates.SkyCoord <astropy.coordinates.SkyCoord>`
        the center position of the cone
   -  radius : `astropy.coordinates.Angle <astropy.coordinates.Angle>`
        the radius of the cone

-  ``cds.RegionType.Polygon`` :

   -  vertices : [`astropy.coordinates.SkyCoord <astropy.coordinates.SkyCoord>`]
        the positions forming the polygon

-  ``cds.RegionType.Moc`` parameter value involves either :

   -  filename : str
        the local path to a fits file describing the MOC
   -  url : str
        an url to a fits file describing the MOC
   -  moc : ``mocpy.MOC`` object
        the region expressed directly as a MOC object

An optional ``intersect`` parameter specifies the selection heuristic of
the data sets. This parameter can take only three different values :

- ``overlaps`` (default). The matching data sets are those overlapping the MOC region.
- ``covers``. The matching data sets are those covering the MOC region.
- ``encloses``. The matching data sets are those enclosing the MOC region.

An optional ``output_format`` parameter allows the user to specify the format
of the `CDS MOC service`_'s response. ``output_format`` must have a value among:

-  ``cds.ReturnFormat.id`` (default). The output is a ID list of the matching
   data sets
-  ``cds.ReturnFormat.record``. The output is a dictionary of
   :class:`astroquery.cds.Dataset <astroquery.cds.Dataset>` objects indexed by their ID
-  ``cds.ReturnFormat.number``. :meth:`~astroquery.cds.CdsClass.query_region` returns the number of matched data sets
-  ``cds.ReturnFormat.moc``. The output is a ``mocpy.MOC`` object corresponding
   to the union of the MOCs of the selected data sets
-  ``cds.ReturnFormat.i_moc``. The output is a ``mocpy.MOC`` object
   corresponding to the intersection of the MOCs of the selected data
   sets

For example, getting the data sets records is done like the following:

.. code:: ipython3

    datasets_d = cds.query_region(region_type=cds.RegionType.Cone,
                                  center=center,
                                  radius=radius,
                                  output_format=cds.ReturnFormat.record)

More optional parameters are available. For instance:

-  ``max_rec`` : int
    set a maximum number of data sets that can be returned
-  ``case_sensitive`` : bool
-  ``meta_var`` : [str]
    when the user asks for data sets records, it is possible to only ask for
    specific meta data. For example, if you want to retrieve only the
    ``moc_sky_fraction`` meta data of the matched data sets, then you pass
    to the ``meta_var`` param of :meth:`~astroquery.cds.CdsClass.query_region` the list ``['moc_sky_fraction']``
-  ``moc_order`` : int
    the moc order of the ``mocpy.MOC`` returned object in case the user asks for a MOC as the query output
-  ``meta_data`` : str
    allows the user to filter data sets following a specific configuration of meta data (see this :ref:`example <query_on_meta_data>`)

To get the set of meta data associated to a specific data set, say ``CDS/I/200/npm1rgal``, just do the following :

.. code:: ipython3

    datasets_d['CDS/I/200/npm1rgal'].properties


.. parsed-literal::

    {'ID': 'CDS/I/200/npm1rgal',
     'TIMESTAMP': 1524657847000.0,
     'bib_reference': '1987AJ.....94..501K',
     'cs_service_url': 'http://vizier.u-strasbg.fr/viz-bin/votable/-A?-source=I%2F200%2Fnpm1rgal&',
     'data_ucd': ['pos.eq.dec', 'phot.mag;em.opt.B', 'pos.eq.ra', 'meta.id'],
     'dataproduct_type': 'catalog',
     'moc_access_url': 'http://alasky.unistra.fr/footprints/tables/vizier/I_200_npm1rgal/MOC?nside=2048',
     'moc_order': 11.0,
     'moc_sky_fraction': 0.0009963,
     'nb_rows': 50517.0,
     'obs_astronomy_kw': ['Positional_Data', 'Galaxies'],
     'obs_collection': 'NPM1',
     'obs_collection_label': 'NPM1',
     'obs_copyright_url': 'http://cdsarc.u-strasbg.fr/viz-bin/Cat?I%2F200',
     'obs_description': 'The Catalogue',
     'obs_description_url': 'http://cdsarc.u-strasbg.fr/viz-bin/Cat?I%2F200',
     'obs_id': 'I/200/npm1rgal',
     'obs_initial_dec': 1.7907846593289463,
     'obs_initial_fov': 0.028629053431811713,
     'obs_initial_ra': 46.42822265624999,
     'obs_label': 'npm1rgal',
     'obs_regime': 'Optical',
     'obs_release_date': '2004-06-30T12:19:38Z',
     'obs_title': 'Lick Northern Proper Motion: NPM1 Ref. Galaxies (Klemola+ 1987) (npm1rgal)',
     'publisher_id': 'ivo://CDS',
     'tap_tablename': 'viz1.I/200/npm1rgal',
     'vizier_popularity': 3.0,
     'web_access_url': 'http://vizier.u-strasbg.fr/viz-bin/VizieR-2?-source=I%2F200%2Fnpm1rgal&'}



:class:`astroquery.cds.Dataset <astroquery.cds.Dataset>` objects allow you to query a specific service (if
available for this data set). Examples of services are the tap, cone search and ssa services.

For ``CDS/I/200/npm1rgal`` we can see that the meta data
``cs_service_url`` is available. Thus, it can be possible to query the
cone search service on this data set specifying the center position and
the radius of the cone. If all goes well, we will get an
`astropy.table.Table <astropy.table.Table>` object containing all the ``CDS/I/200/npm1rgal``
observations located in this cone.

Let's do this:

.. code:: ipython3

    votable = datasets_d['CDS/I/200/npm1rgal'].search(cds.ServiceType.cs, pos=(10.8, 32.2), radius=1.5)
    votable




.. parsed-literal::

    <Table masked=True length=9>
     _RAJ2000  _DEJ2000    _r      Name   ... Flag2 Flag3   _RA.icrs     _DE.icrs  
       deg       deg      deg             ...               "h:m:s"      "d:m:s"   
     float64   float64  float64   bytes8  ... uint8 uint8   bytes12      bytes12   
    --------- --------- -------- -------- ... ----- ----- ------------ ------------
      9.71152  31.54400 1.133477 +31.0014 ...     0     0 00 38 50.765 +31 32 38.40
     12.19638  31.95690 1.207892 +31.0015 ...     0     0 00 48 47.132 +31 57 24.85
     12.22010  31.95853 1.227253 +31.0016 ...     0     0 00 48 52.824 +31 57 30.71
      9.07023  31.99699 1.479329 +31.0013 ...     0     0 00 36 16.856 +31 59 49.18
     12.41883  32.16893 1.370420 +31.0017 ...     0     0 00 49 40.520 +32 10 08.14
     10.30302  32.37405 0.454763 +32.0024 ...     0     0 00 41 12.725 +32 22 26.59
      9.45192  32.60568 1.208313 +32.0023 ...     0     0 00 37 48.460 +32 36 20.44
     10.82190  32.71765 0.517981 +32.0026 ...     0     0 00 43 17.256 +32 43 03.54
     10.36668  32.79513 0.698383 +32.0025 ...     0     0 00 41 28.004 +32 47 42.46



The returned VOTable shows us why this data set has been returned by the
`CDS MOC Service`_ : there are several observations which are located in the same cone
defined as for the CDS MOC query.

.. include:: references.rst