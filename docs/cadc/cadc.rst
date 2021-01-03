.. doctest-skip-all

.. _astroquery.cadc:

************************
Cadc (`astroquery.cadc`)
************************

The Canadian Astronomy Data Centre (CADC) is a world-wide distribution
centre for astronomical data obtained from telescopes. The CADC
specializes in data mining, processing, distribution and transferring
of very large astronomical datasets.

This package allows the access to the data at the `CADC
<https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/>`_.

============
Basic Access
============

.. note::

    ``astroquery.cadc`` is dependent on the ``pyvo`` package. Please
    install it prior to using the ``astroquery.cadc`` module.

The CADC hosts a number of collections and
`~astroquery.cadc.CadcClass.get_collections` returns a list of all
these collections:

.. code-block:: python

    >>> from astroquery.cadc import Cadc
    >>> cadc = Cadc()
    >>> for collection, details in sorted(cadc.get_collections().items()):
    ...    print('{} : {}'.format(collection, details))
    ...
    APASS : {'Description': 'The APASS collection at the CADC', 'Bands': ['Optical', 'Infrared', '']}
    BLAST : {'Description': 'The BLAST collection at the CADC', 'Bands': ['', 'Millimeter']}
    CFHT : {'Description': 'The CFHT collection at the CADC', 'Bands': ['Infrared|Optical', '', 'Optical', 'Infrared']}
    CFHTMEGAPIPE : {'Description': 'The CFHTMEGAPIPE collection at the CADC', 'Bands': ['Infrared', 'Optical']}
    CFHTTERAPIX : {'Description': 'The CFHTTERAPIX collection at the CADC', 'Bands': ['Optical', 'Infrared']}
    CFHTWIRWOLF : {'Description': 'The CFHTWIRWOLF collection at the CADC', 'Bands': ['Infrared']}
    CGPS : {'Description': 'The CGPS collection at the CADC', 'Bands': ['Infrared', 'Radio', 'Millimeter', '']}
    CHANDRA : {'Description': 'The CHANDRA collection at the CADC', 'Bands': ['X-ray']}
    DAO : {'Description': 'The DAO collection at the CADC', 'Bands': ['UV|EUV|X-ray|Gamma-ray', '', 'EUV|X-ray|Gamma-ray', 'Infrared|Optical', 'Optical|UV|EUV|X-ray|Gamma-ray', 'Infrared', 'Optical', 'X-ray|Gamma-ray', 'Infrared|Optical|UV|EUV|X-ray|Ga']}
    DAOPLATES : {'Description': 'The DAOPLATES collection at the CADC', 'Bands': ['Optical', '']}
    DRAO : {'Description': 'The DRAO collection at the CADC', 'Bands': ['Radio']}
    FUSE : {'Description': 'The FUSE collection at the CADC', 'Bands': ['UV', '']}
    GEMINI : {'Description': 'The GEMINI collection at the CADC', 'Bands': ['Gamma-ray', 'Infrared|Optical|UV|EUV|X-ray|Ga', 'Infrared', 'Optical', 'Infrared|Optical', '']}
    HST : {'Description': 'The HST collection at the CADC', 'Bands': ['', 'Infrared', 'Optical', 'UV']}
    HSTHLA : {'Description': 'The HSTHLA collection at the CADC', 'Bands': ['Optical', 'Infrared', 'UV']}
    IRIS : {'Description': 'The IRIS collection at the CADC', 'Bands': ['Infrared']}
    JCMT : {'Description': 'The JCMT collection at the CADC', 'Bands': ['', 'Millimeter']}
    JCMTLS : {'Description': 'The JCMTLS collection at the CADC', 'Bands': ['Millimeter', '']}
    MACHO : {'Description': 'The MACHO collection at the CADC', 'Bands': ['Optical']}
    MOST : {'Description': 'The MOST collection at the CADC', 'Bands': ['Optical']}
    NEOSSAT : {'Description': 'The NEOSSAT collection at the CADC', 'Bands': ['Optical']}
    NGVS : {'Description': 'The NGVS collection at the CADC', 'Bands': ['Infrared|Optical', '', 'Optical']}
    NOAO : {'Description': 'The NOAO collection at the CADC', 'Bands': ['Optical', 'Infrared']}
    OMM : {'Description': 'The OMM collection at the CADC', 'Bands': ['Optical', 'Infrared', '']}
    SDSS : {'Description': 'The SDSS collection at the CADC', 'Bands': ['Infrared', 'Optical']}
    SUBARU : {'Description': 'The SUBARU collection at the CADC', 'Bands': ['Optical']}
    TESS : {'Description': 'The TESS collection at the CADC', 'Bands': ['Optical']}
    UKIRT : {'Description': 'The UKIRT collection at the CADC', 'Bands': ['', 'Optical', 'Infrared']}
    VGPS : {'Description': 'The VGPS collection at the CADC', 'Bands': ['Radio']}
    VLASS : {'Description': 'The VLASS collection at the CADC', 'Bands': ['', 'Radio']}
    XMM : {'Description': 'The XMM collection at the CADC', 'Bands': ['Optical', 'UV', 'X-ray']}


The most basic ways to access the CADC data and metadata is by
region or by name. The following example queries CADC for Canada
France Hawaii Telescope (CFHT) data for a given region and resolves
the URLs for downloading the corresponding data.

.. code-block:: python

    >>> from astroquery.cadc import Cadc
    >>> cadc = Cadc()
    >>> result = cadc.query_region('08h45m07.5s +54d18m00s', collection='CFHT')
    >>> print(result)
      observationURI  sequenceNumber metaReadGroups ...           accMetaChecksum2                lastModified2          maxLastModified2
                                                    ...
    ----------------- -------------- -------------- ... ------------------------------------ ----------------------- -----------------------
    caom:CFHT/2366432        2366432                ... md5:2a6a9b9d399b5ef84899f83206eecd0d 2019-01-08T10:03:36.057 2019-01-08T10:17:16.206
    caom:CFHT/2366188        2366188                ... md5:af8096be4d9d9186b2cc39fb6bd9914c 2019-01-07T11:27:37.922 2019-01-07T18:25:49.914
    caom:CFHT/2480747        2480747                ... md5:c24ace389b760c290a5bf31842fb4ea9 2020-09-09T12:47:39.890 2020-09-09T12:47:39.890
    caom:CFHT/2366188        2366188                ... md5:935330f6f4bb8211eaa8d84c76fbec33 2019-02-07T12:41:55.814 2019-11-06T08:37:00.616
    caom:CFHT/2376828        2376828                ... md5:7c84ae4b76485a28336f03b2b5af18b3 2019-03-04T08:19:23.766 2019-03-04T10:55:53.572
    caom:CFHT/2366432        2366432                ... md5:3bddcbca4ce44a337d6ed2fd7a99507d 2019-02-07T12:24:09.625 2019-11-06T08:37:54.590
    caom:CFHT/2376828        2376828                ... md5:a3e8ccba7bc69d14a07d261d8615cc47 2019-04-10T22:14:33.111 2019-11-06T08:56:14.246
    caom:CFHT/2480747        2480747                ... md5:a7cccd9710cbca222dc8f8b1eedff3b5 2020-09-09T12:47:39.890 2020-09-09T12:47:39.890

    >>> urls = cadc.get_data_urls(result)
    >>> for url in urls:
    ...     print(url)
    ...
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2366432o.fits.fz?RUNID=njvos75ijcw0vo4r
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2366188o.fits.fz?RUNID=njvos75ijcw0vo4r
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2480747p.fits.fz?RUNID=njvos75ijcw0vo4r
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2366188p.fits.fz?RUNID=njvos75ijcw0vo4r
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2376828o.fits.fz?RUNID=njvos75ijcw0vo4r
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2366432p.fits.fz?RUNID=njvos75ijcw0vo4r
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2376828p.fits.fz?RUNID=njvos75ijcw0vo4r
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2480747o.fits.fz?RUNID=njvos75ijcw0vo4r


The next example queries all the data in the same region and filters
the results on the name of the target (as an example - any other
filtering possible) and resolves the URLs for both the primary and
auxiliary data (in this case preview files)

.. code-block:: python

    >>> from astroquery.cadc import Cadc
    >>> cadc = Cadc()
    >>> result = cadc.query_region('08h45m07.5s +54d18m00s')
    >>> print(len(result))
    3032

    >>> urls = cadc.get_data_urls(result[result['target_name'] == 'Nr3491_1'],
    ...                           include_auxiliaries=True)
    >>> for url in urls:
    ...    print(url)
    ...
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2376828o_preview_zoom_1024.jpg?RUNID=tqlxhnxndjs1xhd3
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2376828o_preview_256.jpg?RUNID=tqlxhnxndjs1xhd3
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2376828o_preview_1024.jpg?RUNID=tqlxhnxndjs1xhd3
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2376828o.fits.fz?RUNID=tqlxhnxndjs1xhd3
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2376828p_preview_1024.jpg?RUNID=tqlxhnxndjs1xhd3
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2376828p_preview_256.jpg?RUNID=tqlxhnxndjs1xhd3
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2376828p_preview_zoom_1024.jpg?RUNID=tqlxhnxndjs1xhd3
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2376828p.fits.fz?RUNID=tqlxhnxndjs1xhd3


CADC data can also be queried on the target name. Note that the name
is not resolved. Instead it is matched against the target name in
the CADC metadata.

.. code-block:: python

    >>> from astroquery.cadc import Cadc
    >>> cadc = Cadc()
    >>> result = cadc.query_name('M31')
    >>> print(len(result))
    103949

    >>> result = cadc.query_name('Nr3491_1')
    >>> print(result)
      observationURI  sequenceNumber metaReadGroups ...           accMetaChecksum2                lastModified2          maxLastModified2
                                                    ...
    ----------------- -------------- -------------- ... ------------------------------------ ----------------------- -----------------------
    caom:CFHT/2376828        2376828                ... md5:a3e8ccba7bc69d14a07d261d8615cc47 2019-04-10T22:14:33.111 2019-11-06T08:56:14.246
    caom:CFHT/2376828        2376828                ... md5:7c84ae4b76485a28336f03b2b5af18b3 2019-03-04T08:19:23.766 2019-03-04T10:55:53.572


If only a subsection of the FITS file is needed, CADC can query an
area and resolve the cutout of a result.

.. code-block:: python

    >>> from astropy import units as u
    >>> from astroquery.cadc import Cadc
    >>> cadc = Cadc()
    >>> coords = '01h45m07.5s +23d18m00s'
    >>> radius = 0.01*u.deg
    >>> images = cadc.get_images(coords, radius, collection='CFHT')
    >>> for image in images:
    ...    print(image)
    ...
    [<astropy.io.fits.hdu.image.PrimaryHDU object at 0x7f3805a06ef0>]
    [<astropy.io.fits.hdu.image.PrimaryHDU object at 0x7f3805b23b38>]


Alternatively, if the query result is large and data does not need to be
in memory, lazy access to the downloaded FITS file can be used.

.. code-block:: python

    >>> from astropy import units as u
    >>> from astropy.coordinates import SkyCoord
    >>> from astroquery.cadc import Cadc
    >>> cadc = Cadc()
    >>> coords = SkyCoord(10, 20, unit='deg')
    >>> radius = 0.01*u.deg
    >>> readable_objs = cadc.get_images_async(coords, radius,
    ...                                       collection='CFHT')
    >>> for obj in readable_objs:
    ...    print(obj)
    ...
    Downloaded object from URL https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2234132o.fits.fz&RUNID=pot39nwwtaht03wc&POS=CIRCLE+26.2812589776878+23.299999818906816+0.01 with ID 140045451168112
    Downloaded object from URL https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2368279p.fits.fz&RUNID=pot39nwwtaht03wc&POS=CIRCLE+26.2812589776878+23.299999818906816+0.01 with ID 140045451142576
    Downloaded object from URL https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2228383o.fits.fz&RUNID=pot39nwwtaht03wc&POS=CIRCLE+26.2812589776878+23.299999818906816+0.01 with ID 140045452176880
    Downloaded object from URL https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2228675o.fits.fz&RUNID=pot39nwwtaht03wc&POS=CIRCLE+26.2812589776878+23.299999818906816+0.01 with ID 140045452234864
    Downloaded object from URL https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2234131o.fits.fz&RUNID=pot39nwwtaht03wc&POS=CIRCLE+26.2812589776878+23.299999818906816+0.01 with ID 140045451147584
    Downloaded object from URL https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2228675p.fits.fz&RUNID=pot39nwwtaht03wc&POS=CIRCLE+26.2812589776878+23.299999818906816+0.01 with ID 140045451345584
    Downloaded object from URL https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2228383p.fits.fz&RUNID=pot39nwwtaht03wc&POS=CIRCLE+26.2812589776878+23.299999818906816+0.01 with ID 140045451344912
    Downloaded object from URL https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2234131p.fits.fz&RUNID=pot39nwwtaht03wc&POS=CIRCLE+26.2812589776878+23.299999818906816+0.01 with ID 140045451345104
    Downloaded object from URL https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2234132p.fits.fz&RUNID=pot39nwwtaht03wc&POS=CIRCLE+26.2812589776878+23.299999818906816+0.01 with ID 140045451343808
    Downloaded object from URL https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2368279o.fits.fz&RUNID=pot39nwwtaht03wc&POS=CIRCLE+26.2812589776878+23.299999818906816+0.01 with ID 140045451344768


If the cutout URLs from a complicated query
are needed, the result table can be passed into the
`~astroquery.cadc.CadcClass.get_image_list` function, along with the
cutout coordinates and radius.

.. code-block:: python

    >>> from astroquery.cadc import Cadc
    >>> from astropy import units as u
    >>> cadc = Cadc()
    >>> coords = '01h45m07.5s +23d18m00s'
    >>> radius = 0.1*u.deg
    >>> results = cadc.query_region(coords, radius, collection='CFHT')
    >>> filtered_results = results[results['time_exposure'] > 120.0]
    >>> image_list = cadc.get_image_list(filtered_results, coords, radius)
    >>> print(image_list)
    ['https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2368278o.fits.fz&RUNID=dbuswaj4zwruzi92&POS=CIRCLE+26.2812589776878+23.299999818906816+0.1',
    'https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2368278p.fits.fz&RUNID=dbuswaj4zwruzi92&POS=CIRCLE+26.2812589776878+23.299999818906816+0.1',
    'https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2368279p.fits.fz&RUNID=dbuswaj4zwruzi92&POS=CIRCLE+26.2812589776878+23.299999818906816+0.1',
    'https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2368279o.fits.fz&RUNID=dbuswaj4zwruzi92&POS=CIRCLE+26.2812589776878+23.299999818906816+0.1']


Note that the examples above are for accessing data anonymously. Users
with access to proprietary data can use authenticated sessions
to instantiate the `~astroquery.cadc.CadcClass` class or call
`~astroquery.cadc.CadcClass.login` on it before querying or accessing
the data.

CADC metadata is available through a TAP service. While the above
interfaces offer a quick and simple access to the data, the TAP
interface presented in the next sections allows for more complex
queries.

=============================
Query CADC metadata using TAP
=============================

Cadc TAP access is based on a TAP+ REST service. TAP+ is an extension
of `Table Access Protocol (TAP) <http://www.ivoa.net/documents/TAP>`_
specified by the `International Virtual Observatory Alliance (IVOA)
<http://www.ivoa.net>`_.

The TAP query language is `Astronomical Data Query Language (ADQL)
<http://www.ivoa.net/documents/ADQL/2.0>`_, which is similar to
Structured Query Language (SQL), widely used to query databases.

TAP provides two operation modes:

* Synchronous: the response to the request will be generated as soon
  as the request received by the server.  (In general, avoid using
  this method for queries that take a long time to run before the first
  rows are returned as it might lead to timeouts on the client side.)
* Asynchronous: the server will start a job that will execute the
  request.  The first response to the request is the required
  information (a link) to obtain the job status.  Once the job is
  finished, the results can be retrieved.

The functions can be run as an authenticated user, the
`~astroquery.cadc.CadcClass.list_async_jobs` function will error if
not authenticated. For authentication you need an account with the
CADC, go to http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/, choose a
language, click on Login in the top right area, click on the Request
an Account link, enter your information and wait for confirmation of
your account creation.

There are two types of authentication:

* Username/Password:
  :code:`Cadc().login(user='yourusername', password='yourpassword')`

* Certificate:
  :code:`Cadc().login(certificate_file='path/to/certificate/file')`

For certificate authentication to get a certificate go to
https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/, choose a language,
login, click on your name where the login button used to be,
from the drop-down menu click Obtain a Certificate and save the
certificate. When adding authentication used the path to where you
saved the certificate. Remember that certificates expire and you will
need to get a new one.

When logging in, both forms of authentication are
allowed. Authentication will be applied to each subsequent call. When
a job is created with authentication any further calls will require
authentication.

There is one way to logout which will cancel any kind of authentication
that was used:

* Logout:
  :code:`Cadc.logout()`

CADC metadata is modeled using the `CAOM (Common Archive Observation
Model) <https://www.opencadc.org/caom2/>`_.


======================
Examples of TAP access
======================

---------------------------
1. Non authenticated access
---------------------------

1.1. Get tables
~~~~~~~~~~~~~~~~~

To get a list of table objects:

.. code-block:: python

    >>> from astroquery.cadc import Cadc
    >>> cadc = Cadc()
    >>> tables = cadc.get_tables(only_names=True)
    >>> for table in tables:
    ...     print(table)
    ...
    caom2.Observation
    caom2.Plane
    caom2.Artifact
    caom2.Part
    caom2.Chunk
    caom2.ObservationMember
    caom2.ProvenanceInput
    caom2.EnumField
    caom2.ObsCoreEnumField
    caom2.distinct_proposal_id
    caom2.distinct_proposal_pi
    caom2.distinct_proposal_title
    caom2.HarvestSkipURI
    caom2.SIAv1
    ivoa.ObsCore
    ivoa.ObsFile
    ivoa.ObsPart
    tap_schema.schemas
    tap_schema.tables
    tap_schema.columns
    tap_schema.keys
    tap_schema.key_columns


1.2. Get table
~~~~~~~~~~~~~~~~

To get a single table object:

.. code-block:: python

    >>> from astroquery.cadc import Cadc
    >>> cadc = Cadc()
    >>> table=cadc.get_table(table='caom2.Observation')
    >>> for col in table.columns:
    ...     print(col.name)
    ...
    observationURI
    obsID
    collection
    observationID
    algorithm_name
    type
    intent
    sequenceNumber
    metaRelease
    metaReadGroups
    proposal_id
    proposal_pi
    proposal_project
    proposal_title
    proposal_keywords
    target_name
    target_targetID
    target_type
    target_standard
    target_redshift
    target_moving
    target_keywords
    targetPosition_coordsys
    targetPosition_coordinates_cval1
    targetPosition_equinox
    targetPosition_coordinates_cval2
    telescope_name
    telescope_geoLocationX
    telescope_geoLocationY
    telescope_geoLocationZ
    telescope_keywords
    requirements_flag
    instrument_name
    instrument_keywords
    environment_seeing
    environment_humidity
    environment_elevation
    environment_tau
    environment_wavelengthTau
    environment_ambientTemp
    environment_photometric
    members
    typeCode
    metaProducer
    lastModified
    maxLastModified
    metaChecksum
    accMetaChecksum



1.3 Run synchronous query
~~~~~~~~~~~~~~~~~~~~~~~~~~

A synchronous query will not store the results at server side. These
queries must be used when the amount of data to be retrieved is
'small'.

There is a limit of 2000 rows. If you need more than that, you must
use asynchronous queries.

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

.. code-block:: python

    >>> from astroquery.cadc import Cadc
    >>> cadc = Cadc()
    >>> results = cadc.exec_sync("SELECT top 100 observationID, intent FROM caom2.Observation")
    >>> print(results)
           observationID          intent
    ---------------------------- -------
                    C090503_0500 science
      c4d_151207_032018_opd_u_v3 science
                       ct3264072 science
                        tu558265 science
                       ct2318747 science
                       tu1826354 science
           c4d_150601_015113_ori science
                        tu212518 science
           k4i_041101_174620_zri science
                        tu072083 science
           psg_170118_012214_ori science
    k4n_131022_051755_opd_KXs_v3 science
          c15s_080828_031158_ori science
      c4d_160214_072405_opi_r_v1 science
                             ...     ...
      c4d_150902_000343_opd_i_v1 science
          c09i_141005_231309_sri science
          kcfs_081028_074111_ori science
                        tu802011 science
      c4d_141122_004603_oow_u_v3 science
          c15s_071230_081528_ori science
          c15s_070924_203941_zri science
                       tu1116697 science
                       ct3429663 science
            dao_c182_2020_005631 science
            dao_c182_2020_005632 science
                    C090317_0114 science
                        cp828585 science
          c09i_060720_044639_ori science
            GS-2004A-Q-27-43-006 science
    Length = 100 rows


Query saving results in a file:

.. code-block:: python

    >>> from astroquery.cadc import Cadc
    >>> cadc = Cadc()
    >>> job = cadc.exec_sync("SELECT TOP 10 observationID, obsID FROM caom2.Observation AS Observation",
    ...                      output_file='test_output_noauth.tsv', output_format='tsv')

1.5 Synchronous query with temporary uploaded table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A table can be uploaded to the server in order to be used in a query.

.. code-block:: python

    >>> from astroquery.cadc import Cadc
    >>> cadc = Cadc()
    >>> upload_resource = 'data/votable.xml'
    >>> j = cadc.exec_sync("SELECT * FROM tap_upload.test_table_upload",
    ...                    uploads=upload_resource,
    ...                    output_file="test_output_table")
    >>> print(j.get_results())
             uri                    contentChecksum            ...   contentType
                                                               ...
    --------------------- ------------------------------------ ... ----------------
    ad:IRIS/I001B1H0.fits md5:b6ead425ae84289246e4528bbdd7da9a ... application/fits
    ad:IRIS/I001B2H0.fits md5:a6b082ca530bf5db5a691985d0c1a6ca ... application/fits
    ad:IRIS/I001B3H0.fits md5:2ada853a8ae135e16504aeba4e47489e ... application/fits


1.6 Asynchronous query
~~~~~~~~~~~~~~~~~~~~~~

Asynchronous queries save results at server side. These queries can
be accessed at any time.

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

.. code-block:: python

    >>> from astroquery.cadc import Cadc
    >>> cadc = Cadc()
    >>> job = cadc.create_async("SELECT TOP 100 observationID, instrument_name, target_name FROM caom2.Observation AS Observation")
    >>> job.run().wait()
    >>> job.raise_if_error()
    >>> print(job.fetch_result().to_table())
           observationID         instrument_name            target_name
    ---------------------------- ---------------- --------------------------------
                    C090503_0500           CPAPIR                             SH87
      c4d_151207_032018_opd_u_v3            decam                          Field14
                       ct3264072          andicam                          2227-08
                        tu558265         mosaic_2                    xcs0058940301
                       ct2318747         ccd_spec                             test
                       tu1826354            decam                               B1
           c4d_150601_015113_ori            decam                             junk
                        tu212518          newfirm Mask for K4N09B_20091129_783db2b
           k4i_041101_174620_zri        ir_imager                        TEST bias
                        tu072083          newfirm Mask for K4N07B_20071113_776684b
           psg_170118_012214_ori          goodman                          NGC1672
    k4n_131022_051755_opd_KXs_v3          newfirm Mask for K4N13B_20131020_89c812c
          c15s_080828_031158_ori         ccd_spec                              082
      c4d_160214_072405_opi_r_v1            decam        MAGLITES field: 5354-01-r
      c4d_141122_004603_oki_u_v3            decam                           Field4
     c4d_140505_000543_opw_VR_v1            decam                          AiYN1Qv
                             ...              ...                              ...
          c09i_140321_044944_ori       ccd_imager twhya filter1 = dia, filter2 = g
      c4d_150902_000343_opd_i_v1            decam                         C6p13c1A
          c09i_141005_231309_sri       ccd_imager                            sflat
          kcfs_081028_074111_ori         ccd_spec                         HD 22780
                        tu802011       mosaic_1_1                            86326
      c4d_141122_004603_oow_u_v3            decam                           Field4
          c15s_071230_081528_ori         ccd_spec                         HD 95578
          c15s_070924_203941_zri         ccd_spec                             Bias
                       tu1116697         mosaic_2                             sm43
                       ct3429663         mosaic_2                             test
            dao_c182_2020_005631 Newtonian Imager                  s2020ihc(150@0)
            dao_c182_2020_005632 Newtonian Imager                  s2020ihc(150@0)
                    C090317_0114           CPAPIR                           2M1106
                        cp828585          spartan             WISEJ1741+2533 x-6y5
          c09i_060720_044639_ori       ccd_imager                    G2239n05d1243
            GS-2004A-Q-27-43-006           GMOS-S                            LMCF4
    Length = 100 rows
 

1.7 Load job
~~~~~~~~~~~~~~~~~~~~~~

Asynchronous jobs can be loaded. You need the jobid in order to load
the job.


.. code-block:: python

    >>> from astroquery.cadc import Cadc
    >>> cadc = Cadc()
    >>> job = cadc.create_async("SELECT TOP 100 observationID, instrument_name, target_name FROM caom2.Observation AS Observation")
    >>> job.run().wait()
    >>> job.raise_if_error()
    >>> loaded_job = cadc.load_async_job(jobid=job.job_id)
    >>> print(loaded_job.fetch_result().to_table())
           observationID         instrument_name            target_name
    ---------------------------- ---------------- --------------------------------
                    C090503_0500           CPAPIR                             SH87
      c4d_151207_032018_opd_u_v3            decam                          Field14
                       ct3264072          andicam                          2227-08
                        tu558265         mosaic_2                    xcs0058940301
                       ct2318747         ccd_spec                             test
                       tu1826354            decam                               B1
           c4d_150601_015113_ori            decam                             junk
                        tu212518          newfirm Mask for K4N09B_20091129_783db2b
           k4i_041101_174620_zri        ir_imager                        TEST bias
                        tu072083          newfirm Mask for K4N07B_20071113_776684b
           psg_170118_012214_ori          goodman                          NGC1672
    k4n_131022_051755_opd_KXs_v3          newfirm Mask for K4N13B_20131020_89c812c
          c15s_080828_031158_ori         ccd_spec                              082
      c4d_160214_072405_opi_r_v1            decam        MAGLITES field: 5354-01-r
      c4d_141122_004603_oki_u_v3            decam                           Field4
     c4d_140505_000543_opw_VR_v1            decam                          AiYN1Qv
                             ...              ...                              ...
          c09i_140321_044944_ori       ccd_imager twhya filter1 = dia, filter2 = g
      c4d_150902_000343_opd_i_v1            decam                         C6p13c1A
          c09i_141005_231309_sri       ccd_imager                            sflat
          kcfs_081028_074111_ori         ccd_spec                         HD 22780
                        tu802011       mosaic_1_1                            86326
      c4d_141122_004603_oow_u_v3            decam                           Field4
          c15s_071230_081528_ori         ccd_spec                         HD 95578
          c15s_070924_203941_zri         ccd_spec                             Bias
                       tu1116697         mosaic_2                             sm43
                       ct3429663         mosaic_2                             test
            dao_c182_2020_005631 Newtonian Imager                  s2020ihc(150@0)
            dao_c182_2020_005632 Newtonian Imager                  s2020ihc(150@0)
                    C090317_0114           CPAPIR                           2M1106
                        cp828585          spartan             WISEJ1741+2533 x-6y5
          c09i_060720_044639_ori       ccd_imager                    G2239n05d1243
            GS-2004A-Q-27-43-006           GMOS-S                            LMCF4
    Length = 100 rows


---------------------------
2. Authenticated access
---------------------------

Some capabilities (shared tables, persistent jobs, etc.) are only
available to authenticated users.

One authentication option is to instantiate the
`~astroquery.cadc.CadcClass` class with a pre-existing,
`pyvo.auth.authsession.AuthSession` or `requests.Session` object that
contains the necessary credentials. Note that the session will be
used for all the service interaction. The former session attempts to
pair the credentials with the auth methods in the service capabilities
while the latter sends the credentials with all requests.

The second option is to use the `~astroquery.cadc.CadcClass.login`
method.

After a successful authentication, user credentials will be used
until the `~astroquery.cadc.CadcClass.logout` method is called.

All previous methods (`~astroquery.cadc.CadcClass.get_tables`,
`~astroquery.cadc.CadcClass.get_table`,
`~astroquery.cadc.CadcClass.run_query`) explained for non authenticated
users are applicable for authenticated ones.


2.1 Login/Logout
~~~~~~~~~~~~~~~~~

Login with username and password:

.. code-block:: python

    >>> from astroquery.cadc import Cadc
    >>> cadc = Cadc()
    >>> cadc.login(user='userName', password='userPassword')


Login with certificate:

.. code-block:: python

    >>> from astroquery.cadc import Cadc
    >>> cadc = Cadc()
    >>> cadc.login(certificate_file='/path/to/cert/file')


To perform a logout:


.. code-block:: python

    >>> from astroquery.cadc import Cadc
    >>> cadc = Cadc()
    >>> cadc.logout()

Reference/API
=============

.. automodapi:: astroquery.cadc
    :no-inheritance-diagram:
