.. doctest-skip-all

.. _astroquery.alma:

********************************
ALMA Queries (`astroquery.alma`)
********************************

Example Notebooks
=================
A series of example notebooks can be found here:

 * `What has ALMA observed toward all Messier objects? (an example of querying many sources) <http://nbviewer.jupyter.org/gist/keflavich/e798e10e3bf9a93d1453>`_
 * `ALMA finder chart of the Cartwheel galaxy and public Cycle 1 data quicklooks <http://nbviewer.jupyter.org/gist/keflavich/d5af22578094853e2d24>`_
 * `Finder charts toward many sources with different backgrounds <http://nbviewer.jupyter.org/gist/keflavich/2ef877ec90d774645fee>`_
 * `Finder chart and downloaded data from Cycle 0 observations of Sombrero Galaxy <http://nbviewer.jupyter.org/gist/keflavich/9934c9412d8f58299962>`_

Getting started
===============

`astroquery.alma` provides the astroquery interface to the ALMA archive.  It
supports object and region based querying and data staging and retrieval.

You can get interactive help to find out what keywords to query for:

.. code-block:: python

   >>> from astroquery.alma import Alma
   >>> Alma.help()
    Most common ALMA query keywords are listed below. These keywords are part
    of the ALMA ObsCore model, an IVOA standard for metadata representation
    (3rd column). They were also present in original ALMA Web form and, for
    backwards compatibility can be accessed with their old names (2nd column).
    More elaborate queries on the ObsCore model are possible with `query_sia`
    or `query_tap` methods
    Description                         Original ALMA keyword               ObsCore keyword
    -------------------------------------------------------------------------------------------------------

    Position
      Source name (astropy Resolver)    source_name_resolver                SkyCoord.from_name
      Source name (ALMA)                source_name_alma                    target_name
      RA Dec (Sexagesimal)              ra_dec                              s_ra, s_dec
      Galactic (Degrees)                galactic                            gal_longitude, gal_latitude
      Angular resolution (arcsec)       spatial_resolution                  spatial_resolution
      Largest angular scale (arcsec)    spatial_scale_max                   spatial_scale_max
      Field of view (arcsec)            fov                                 s_fov

    Energy
      Frequency (GHz)                   frequency                           frequency
      Bandwidth (GHz)                   bandwidth                           bandwidth
      Spectral resolution (KHz)         spectral_resolution                 em_resolution
      Band                              band_list                           band_list

    Time
      Observation date                  start_date                          t_min
      Integration time (s)              integration_time                    t_exptime

    Polarization
      Polarisation type (Single, Dual, Full) polarisation_type              pol_states

    Observation
      Line sensitivity (10 km/s) (mJy/beam) line_sensitivity                sensitivity_10kms
      Continuum sensitivity (mJy/beam)  continuum_sensitivity               cont_sensitivity_bandwidth
      Water vapour (mm)                 water_vapour                        pvw

    Project
      Project code                      project_code                        proposal_id
      Project title                     project_title                       obs_title
      PI name                           pi_name                             obs_creator_name
      Proposal authors                  proposal_authors                    proposal_authors
      Project abstract                  project_abstract                    proposal_abstract
      Publication count                 publication_count                   NA
      Science keyword                   science_keyword                     science_keyword

    Publication
      Bibcode                           bibcode                             bib_reference
      Title                             pub_title                           pub_title
      First author                      first_author                        first_author
      Authors                           authors                             authors
      Abstract                          pub_abstract                        pub_abstract
      Year                              publication_year                    pub_year

    Options
      Public data only                  public_data                         data_rights
      Science observations only         science_observations                calib_level

Authentication
==============

Users can log in to acquire proprietary data products.  Login is performed
via the ALMA CAS (central authentication server).

.. code-block:: python

    >>> from astroquery.alma import Alma
    >>> alma = Alma()
    >>> # First example: TEST is not a valid username, it will fail
    >>> alma.login("TEST") # doctest: +SKIP
    TEST, enter your ALMA password:

    Authenticating TEST on asa.alma.cl...
    Authentication failed!
    >>> # Second example: pretend ICONDOR is a valid username
    >>> alma.login("ICONDOR", store_password=True) # doctest: +SKIP
    ICONDOR, enter your ALMA password:

    Authenticating ICONDOR on asa.alma.cl...
    Authentication successful!
    >>> # After the first login, your password has been stored
    >>> alma.login("ICONDOR") # doctest: +SKIP
    Authenticating ICONDOR on asa.alma.cl...
    Authentication successful!

Your password will be stored by the `keyring
<https://pypi.python.org/pypi/keyring>`_ module.
You can choose not to store your password by passing the argument
``store_password=False`` to ``Alma.login``.  You can delete your password later
with the command ``keyring.delete_password('astroquery:asa.alma.cl',
'username')``.

Querying Targets and Regions
============================

You can query by object name or by circular region:

.. code-block:: python

    >>> from astroquery.alma import Alma
    >>> m83_data = Alma.query_object('M83')
    >>> print(len(m83_data))
    830
    >>> m83_data.colnames
    ['obs_publisher_did', 'obs_collection', 'facility_name', 'instrument_name',
    'obs_id', 'dataproduct_type', 'calib_level', 'target_name', 's_ra',
    's_dec', 's_fov', 's_region', 's_resolution', 't_min', 't_max',
    't_exptime', 't_resolution', 'em_min', 'em_max', 'em_res_power',
    'pol_states', 'o_ucd', 'access_url', 'access_format', 'proposal_id',
    'data_rights', 'gal_longitude', 'gal_latitude', 'band_list',
    'em_resolution', 'bandwidth', 'antenna_arrays', 'is_mosaic',
    'obs_release_date', 'spatial_resolution', 'frequency_support',
    'frequency', 'velocity_resolution', 'obs_creator_name', 'pub_title',
    'first_author', 'authors', 'pub_abstract', 'publication_year',
    'proposal_abstract', 'schedblock_name', 'proposal_authors',
    'sensitivity_10kms', 'cont_sensitivity_bandwidth', 'pwv', 'group_ous_uid',
    'member_ous_uid', 'asdm_uid', 'obs_title', 'type', 'scan_intent',
    'science_observation', 'spatial_scale_max', 'qa2_passed', 'bib_reference',
    'science_keyword', 'scientific_category', 'lastModified']


Please note that some of the column names are duplicated. First group of names
(the ones containing "_") are column names as they appear in the ALMA ObsCore
model while the second group are copies created to maintain backwards
compatibility with previous version of the library.


Region queries are just like any other in astroquery:


.. code-block:: python

    >>> from astropy import coordinates
    >>> from astropy import units as u
    >>> galactic_center = coordinates.SkyCoord(0*u.deg, 0*u.deg,
    ...                                        frame='galactic')
    >>> gc_data = Alma.query_region(galactic_center, 1*u.deg)
    >>> print(len(gc_data))
    383

Querying by other parameters
============================

As of version 0.3.4, you can also query other fields by keyword. For example,
if you want to find all projects with a particular PI, you could do:

.. code-block:: python

   >>> rslt = Alma.query_object('W51', pi_name='*Ginsburg*', public=False)

The ''query_sia'' method offers another way to query ALMA using the IVOA SIA
subset of keywords returning results in 'ObsCore' format.

.. code-block:: python

    >>> Alma.query_sia(query_sia(pol='XX'))

Finally, the ''query_tap'' method is the most general way of querying the ALMA
metadata. This method is used to send queries to the service using the
'ObsCore' columns as constraints. The returned result is also in 'ObsCore'
format.

.. code-block:: python

    >>> Alma.query_tap("select * from ivoa.obscore where target_name like '%M83%'")

Use the ''help_tap'' method to learn about the ALMA 'ObsCore' keywords and
their types.

.. code-block:: python

    >>> Alma.help_tap()
    Table to query is "voa.ObsCore".
    For example: "select top 1 * from ivoa.ObsCore"
    The scheme of the table is as follows.

      Name                 Type            Unit       Description
    ------------------------------------------------------------------------------------------
      access_format        char(9)                    Content format of the data
      access_url           char(72*)                  URL to download the data
      antenna_arrays       char(660*)                 Blank-separated list of Pad:Antenna pairs, i.e., A109:DV09 J504:DV02 J505:DV05 for antennas DV09, DV02 and DV05 sitting on pads A109, J504, and J505, respectively.
      asdm_uid             char(32*)                  UID of the ASDM containing this Field.
      authors              char(4000*)                Full list of first author and all co-authors
      band_list            char(30*)                  Space delimited list of bands
      bandwidth            double          GHz        Total Bandwidth
      bib_reference        char(30*)                  Bibliography code
      calib_level          int                        calibration level (2 or 3). 2 if product_type = MOUS, 3 if product_type = GOUS
      cont_sensitivity_bandwidth double          mJy/beam   Estimated noise in the aggregated continuum bandwidth. Note this is an indication only, it does not include the effects of flagging or dynamic range limitations.
      data_rights          char(11)                   Access to data.
      dataproduct_type     char(5*)                   type of product
      em_max               double          m          stop spectral coordinate value
      em_min               double          m          start spectral coordinate value
      em_res_power         double                     typical spectral resolution
      em_resolution        double          m          Estimated frequency resolution from all the spectral windows, using median values of channel widths.
      facility_name        char(3)                    telescope name
      first_author         char(256*)                 The first author as provided by <a href="http://telbib.eso.org">telbib.eso.org</a>.
      frequency            double          GHz        Observed (tuned) reference frequency on the sky.
      frequency_support    char(4000*)     GHz        All frequency ranges used by the field
      gal_latitude         double          deg        Galactic latitude of the observation for RA/Dec. Estimated using PyEphem and RA/Dec.
      gal_longitude        double          deg        Galactic longitude of the observation for RA/Dec. Estimated using PyEphem and RA/Dec.
      group_ous_uid        char(64*)                  Group OUS ID
      instrument_name      char(4)                    instrument name
      is_mosaic            char(1)                    Flag to indicate if this ASDM represents a mosaic or not.
      lastModified         char(*)                    Time stamp of last modification of the metadata
      member_ous_uid       char(64*)                  Member OUS ID
      o_ucd                char(35)                   UCD describing the observable axis (pixel values)
      obs_collection       char(4)                    short name for the data collection
      obs_creator_name     char(256*)                 case-insensitive partial match over the full PI name. Wildcards can be used
      obs_id               char(64*)                  internal dataset identifier
      obs_publisher_did    char(33*)                  publisher dataset identifier
      obs_release_date     char(*)                    timestamp of date the data becomes publicly available
      obs_title            char(256*)                 Case-insensitive search over the project title
      pol_states           char(64*)                  polarization states present in the data
      proposal_abstract    char(4000*)                Text search on the proposal abstract. Only abstracts will be returned which contain the given text. The search is case-insensitive.
      proposal_authors     char(2000*)                Full name of CoIs .
      proposal_id          char(64*)                  Identifier of proposal to which NO observation belongs.
      pub_abstract         char(4000*)                Case insensitive text search through the abstract of the publication.
      pub_title            char(256*)                 Case insensitive search through the title of the publication.
      publication_year     int                        The year the publication did appear in the printed version of the refereed journal.
      pwv                  float           mm         Estimated precipitable water vapour from the XML_CALWVR_ENTITIES table.
      qa2_passed           char(1)                    Quality Assessment 2 status: does the Member / Group OUS fulfil the PI's requirements?
      s_dec                double          deg        DEC of central coordinates
      s_fov                double          deg        size of the region covered (~diameter of minimum bounding circle)
      s_ra                 double          deg        RA of central coordinates
      s_region             char(*)         deg        region bounded by observation
      s_resolution         double          deg        typical spatial resolution
      scan_intent          char(256*)                 Scan intent list for the observed field.
      schedblock_name      char(128*)                 Name of the Scheduling Block used as a template for executing the ASDM containing this Field.
      science_keyword      char(200*)                 None
      science_observation  char(1)                    Flag to indicate whether this is a science observation.
      scientific_category  char(200*)                 None
      sensitivity_10kms    double          mJy/beam   Estimated noise in an nominal 10km/s bandwidth. Note this is an indication only, it does not include the effects of flagging or Hanning smoothing, and a 10km/s bandwidth may not be achievable with the data as taken.
      spatial_resolution   double          arcsec     Average of the maximum and minimum spatial resolution values of all spectral windows
      spatial_scale_max    double          arcsec     Due to the fact that radio antennas can not be placed infinitely close, measurements do have a smallest separation which translates into a maximal angular distance beyond which features can not be resolved reliably any more. Adding observations with the ALMA Total Power array can add those missing largest scales.
      t_exptime            double          s          exposure time of observation
      t_max                double          d          end time of observation (MJD)
      t_min                double          d          start time of observation (MJD)
      t_resolution         double          s          typical temporal resolution
      target_name          char(256*)                 name of intended target
      type                 char(16*)                  Type flags.
      velocity_resolution  double          m/s        Estimated velocity resolution from all the spectral windows, from frequency resolution.

Downloading Data
================

You can download ALMA data with astroquery, but be forewarned, cycle 0 and
cycle 1 data sets tend to be >100 GB!


.. code-block:: python

   >>> import numpy as np
   >>> uids = np.unique(m83_data['Member ous id'])
   >>> print(uids)
        Member ous id
    -----------------------
     uid://A002/X3216af/X31
    uid://A002/X5a9a13/X689


You can then stage the data and see how big it is (you can ask for one or more
UIDs):


.. code-block:: python

   >>> link_list = Alma.stage_data(uids)
   INFO: Staging files... [astroquery.alma.core]
   >>> link_list['size'].sum()
   159.26999999999998

You can then go on to download that data.  The download will be cached so that repeat
queries of the same file will not re-download the data.  The default cache
directory is ``~/.astropy/cache/astroquery/Alma/``, but this can be changed by
changing the ``cache_location`` variable:

.. code-block:: python

   >>> myAlma = Alma()
   >>> myAlma.cache_location = '/big/external/drive/'
   >>> myAlma.download_files(link_list, cache=True)

You can also do the downloading all in one step:

.. code-block:: python

   >>> myAlma.retrieve_data_from_uid(uids[0])

Downloading FITS data
=====================

If you want just the QA2-produced FITS files, you can download the tarball,
extract the FITS file, then delete the tarball:

.. code-block:: python

    >>> from astroquery.alma.core import Alma
    >>> from astropy import coordinates
    >>> from astropy import units as u
    >>> orionkl = coordinates.SkyCoord('5:35:14.461 -5:21:54.41', frame='fk5',
    ...                                unit=(u.hour, u.deg))
    >>> result = Alma.query_region(orionkl, radius=0.034*u.deg)
    >>> uid_url_table = Alma.stage_data(result['Member ous id'])
    >>> # Extract the data with tarball file size < 1GB
    >>> small_uid_url_table = uid_url_table[uid_url_table['size'] < 1]
    >>> # get the first 10 files...
    >>> filelist = Alma.download_and_extract_files(small_uid_url_table[:10]['URL'])

You might want to look at the READMEs from a bunch of files so you know what kind of S/N to expect:

.. code-block:: python

    >>> filelist = Alma.download_and_extract_files(uid_url_table['URL'], regex='.*README$')


Further Examples
================
There are some nice examples of using the ALMA query tool in conjunction with other astroquery
tools in :doc:`../gallery`, especially :ref:`gallery-almaskyview`.

Reference/API
=============

.. automodapi:: astroquery.alma
    :no-inheritance-diagram:

.. automodapi:: astroquery.alma.utils
    :no-inheritance-diagram:
