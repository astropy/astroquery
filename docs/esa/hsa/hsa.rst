.. _astroquery.esa.hsa:

***************************************************
ESA Herschel Science Archive (`astroquery.esa.hsa`)
***************************************************

`Herschel <https://www.cosmos.esa.int/web/herschel/home/>`__ was the fourth
cornerstone in ESA's Horizon 2000 science programme, designed to observe the 'cool' universe.
It performed photometry and spectroscopy in the poorly explored 55-670 µm spectral range with a 3.5 m diameter
Cassegrain telescope, providing unique observing capabilities and bridging the gap between earlier infrared
space missions and groundbased facilities. Herschel successfully performed ~37000 science observations and
~6600 science calibration observations which are publicly available to the worldwide astronomical community
through the Herschel Science Archive.

This package allows the access to the `Herschel Science Archive <http://archives.esac.esa.int/hsa/whsa/>`_.

Examples
========

1. Getting Herschel data
------------------------

.. Skipping becuase of how long the download takes
.. doctest-skip::   

  >>> from astroquery.esa.hsa import HSA
  >>>
  >>> HSA.download_data(observation_id='1342195355',  retrieval_type='OBSERVATION',
  ...                   instrument_name='PACS')
  Downloading URL http://archives.esac.esa.int/hsa/whsa-tap-server/data?&retrieval_type=OBSERVATION&observation_id=1342195355&instrument_name=PACS to 1342195355.tar ... [Done]
  '1342195355.tar'

This will download the products of the observation '1342195355' with the instrument 'PACS' and
it will store them in a tar called '1342195355.tar'. The parameters available are detailed in the API.

For more details of the parameters check the section 6 of the ``Direct Product Access using TAP`` in the
`HSA users guide <http://archives.esac.esa.int/hsa/whsa/>`_.

For more details about the products check:
  https://www.cosmos.esa.int/web/herschel/data-products-overview


2. Getting Observation Products
-------------------------------

.. Skipping becuase of how long the download takes
.. doctest-skip::

  >>> from astroquery.esa.hsa import HSA
  >>>
  >>> HSA.get_observation('1342195355', instrument_name='PACS')
  Downloading URL http://archives.esac.esa.int/hsa/whsa-tap-server/data?&retrieval_type=OBSERVATION&observation_id=1342195355&instrument_name=PACS to 1342195355.tar ... [Done]
  '1342195355.tar'

This will download the product of the observation '1342195355' with the instrument 'PACS' and
it will store them in a tar called '1342195355.tar'. The parameters available are detailed in the API.

.. Note:: There is no difference between the product retrieved with this method and
          `~astroquery.esa.hsa.HSAClass.download_data`. `~astroquery.esa.hsa.HSAClass.download_data`
          is a more generic interface that allows the user to retrieve any product or metadata and
          `~astroquery.esa.hsa.HSAClass.get_observation` allows the user to retrieve only observation products.

For more information check the section 6.1 of the of the ``Direct Product Access using TAP`` in the
`HSA users guide`_.

For more details of the parameters check the section 6.2 of the ``Direct Product Access using TAP`` in the
`HSA users guide`_.


3. Getting Herschel Postcard
----------------------------

.. doctest-remote-data::

  >>> from astroquery.esa.hsa import HSA
  >>>
  >>> HSA.get_postcard('1342195355', instrument_name='PACS')  # doctest: +IGNORE_OUTPUT
  Downloading URL http://archives.esac.esa.int/hsa/whsa-tap-server/data?&retrieval_type=POSTCARD&observation_id=1342195355&instrument_name=PACS to /home/dev/.astropy/cache/astroquery/HSA/data?&retrieval_type=POSTCARD&observation_id=1342195355&instrument_name=PACS ... [Done]
  '1342195355.jpg'

This will download the postcard (static representation in JPG-format of the final product) of the observation
'1342195355' with the instrument 'PACS' and it will store them in a tar called '1342195355.jpg'.
The parameters available are detailed in the API.

For more details of the parameters check the section 6.2 of the ``Direct Product Access using TAP`` in the
`HSA users guide`_.


4. Getting Herschel metadata through TAP
----------------------------------------

This function provides access to the Herschel Science Archive database using the Table Access Protocol (TAP) and via the Astronomical Data
Query Language (`ADQL <https://www.ivoa.net/documents/ADQL/20180112/PR-ADQL-2.1-20180112.html>`__).

.. doctest-remote-data::

  >>> from astroquery.esa.hsa import HSA
  >>>
  >>> result = HSA.query_hsa_tap("select top 10 * from hsa.v_active_observation",
  ...                            output_format='csv', output_file='results.csv')
  >>> result.pprint(max_width=100)
                    aor                           bii         ...  target_name   urn_version
  --------------------------------------- ------------------- ... -------------- -----------
                          PP2-SWa-NGC3265  28.797292629881316 ...        NGC3265      915907
         PRISMAS_W33a_hifi3b_898GHz_A_D2O  -17.86672520275456 ...           W33A      806737
    GOODS-S_70_d+8+8_forward_r3_shortaxis  -27.80919396603746 ...  GOODS-S d+8+8      894819
        PSP2_HStars-Set12f - RedRectangle -10.637417697356986 ...  Red Rectangle      800938
                   SPIRE-A - G126.24-5.52  57.195030974713134 ...   G126.24-5.52      810242
  PSP1_PRISMAS_W31C_hifi6a_1477GHz_A_D2H+  -19.93074108498436 ...           W31C      920099
         Spire Level-2 GOODS-S 37  - copy  -27.81104151290488 ...        GOODS-S      898135
               PSP2_HStars-Set13  - 10216   13.27923027337195 ...      IRC+10216      801364
                    PACS-A - G345.39-3.97  -43.47405026924179 ... G345.39-3.97-1      883176
          PRISMAS_g34_hifi7b_1897GHz_B_C3  1.2495150652937468 ...      G34.3+0.1      921086

This will execute an ADQL query to download the first 10 observations in the `Herschel Science Archive`_.
The result of the query will be stored in the file ``results.csv``.


5. Getting table details of HSA TAP
-----------------------------------

.. doctest-remote-data::

  >>> from astroquery.esa.hsa import HSA
  >>>
  >>> HSA.get_tables()
  INFO: Retrieving tables... [astroquery.utils.tap.core]
  INFO: Parsing tables... [astroquery.utils.tap.core]
  INFO: Done. [astroquery.utils.tap.core]
  ['hpdp.latest_observation_hpdp', 'hpdp.vizier_links', 'hpdp.unique_observation_hpdp', 'hpdp.latest_unique_observation_requests', 'hpdp.files', 'hpdp.latest_requests', 'public.dual', 'public.image_formats', 'tap_schema.tables', 'tap_schema.columns', 'tap_schema.keys', 'tap_schema.schemas', 'tap_schema.key_columns', 'hsa.observation_science', 'hsa.proposal_coauthor', 'hsa.proposal_observation', 'hsa.instrument', 'hsa.observing_mode_per_instrument', 'hsa.spire_spectral_feature_finder_catalogue', 'hsa.hifi_spectral_line_smoothed', 'hsa.publication', 'hsa.quality_flag', 'hsa.v_active_observation', 'hsa.proposal_info', 'hsa.pacs_point_source_070', 'hsa.observing_mode', 'hsa.proposal', 'hsa.proposal_pi_user', 'hsa.spire_point_source_350', 'hsa.spire_point_source_250', 'hsa.v_publication', 'hsa.spire_point_source_500', 'hsa.pacs_point_source_100', 'hsa.v_proposal_observation', 'hsa.hifi_spectral_line_native', 'hsa.pacs_point_source_160', 'hsa.ancillary', 'hsa.metadata_expert_panels', 'pubtool.institutions', 'pubtool.v_first_pub_date', 'pubtool.v_first_pub_date_single', 'pubtool.archival_type', 'pubtool.publication', 'pubtool.publication_details', 'pubtool.authors_institutions', 'pubtool.publication_observation', 'pubtool.authors', 'updp2.latest_observation_updp', 'updp2.vizier_links', 'updp2.latest_unique_observation_requests', 'updp2.files', 'updp2.latest_requests', 'updp2.unique_observation_updp']

This will show the available tables in HSA TAP service in the `Herschel Science Archive`_.


6. Getting columns details of HSA TAP
-------------------------------------

.. doctest-remote-data::

  >>> from astroquery.esa.hsa import HSA
  >>>
  >>> HSA.get_columns('hsa.v_active_observation')
  INFO: Retrieving tables... [astroquery.utils.tap.core]
  INFO: Parsing tables... [astroquery.utils.tap.core]
  INFO: Done. [astroquery.utils.tap.core]
  ['aor', 'bii', 'dec', 'duration', 'end_time', 'fov', 'global_science_area', 'icon_image', 'icon_location', 'image_2_5_location', 'image_location', 'ingest_queue_oid', 'instrument_oid', 'is_active_version', 'is_public', 'lii', 'naif_id', 'num_publications', 'observation_id', 'observation_oid', 'observer', 'observing_mode_oid', 'obsstate', 'od_number', 'pa', 'polygon_fov', 'position', 'prop_end', 'proposal_id', 'quality_report_location', 'ra', 'science_area', 'science_category', 'spg_id', 'start_time', 'status', 'target_name', 'urn_version']

This will show the column details of the table ``'hsa.v_active_observation'`` in HSA TAP service in the
`Herschel Science Archive`_.


7. Query Region
---------------

.. doctest-remote-data::

  >>> from astroquery.esa.hsa import HSA
  >>> from astropy.coordinates import SkyCoord
  >>> from astropy import units as u
  >>>
  >>> c = SkyCoord(ra=100.2417*u.degree, dec=9.895*u.degree, frame='icrs')
  >>> result = HSA.query_region(c, 0.5)
  >>> result.pprint(max_width=100)
                        aor                            bii         ...   target_name    urn_version
                                                                ...
  ------------------------------------------- ------------------ ... ---------------- -----------
  KPOT_wlanger_1-HPoint-0007 - CII_G202.6+2.0 10.062774289985356 ... CII_G202.6+2.0-1      921022
                                      n2264-o   9.45754288889945 ...          NGC2264      919399
                                      n2264-n   9.45754288889945 ...          NGC2264      919398
                                      n2264-n  9.450299102175919 ...          NGC2264      898497
                                      n2264-o  9.450499719127244 ...          NGC2264      898535

Retrieve a VOTable with the observations metadata of a given region.


8. Query Observations
---------------------

.. doctest-remote-data::

  >>> from astroquery.esa.hsa import HSA
  >>> from astropy.coordinates import SkyCoord
  >>> from astropy import units as u
  >>>
  >>> c = SkyCoord(ra=100.2417*u.degree, dec=9.895*u.degree, frame='icrs')
  >>> HSA.query_observations(c, 0.5)
  <Table length=5>
  observation_id
      object
  --------------
      1342219315
      1342205057
      1342205056
      1342205056
      1342205057

Retrieve a VOTable with the observation IDs of a given region.


9. Procedure example
--------------------

First retrieve the observation IDs based on a position on the sky. To achive this, query the TAP service.

.. doctest-remote-data::

  >>> from astroquery.esa.hsa import HSA
  >>>
  >>> HSA.query_hsa_tap("select top 10 observation_id from hsa.v_active_observation where "
  ...                   "contains(point('ICRS', hsa.v_active_observation.ra, hsa.v_active_observation.dec), "
  ...                   "circle('ICRS', 100.2417,9.895, 1.1))=1", output_format='csv', output_file='results.csv')
  <Table length=9>
  observation_id
      int64
  --------------
      1342228342
      1342228371
      1342228372
      1342219315
      1342205057
      1342205056
      1342205058
      1342205056
      1342205057

In this example we are doing a circle search of 1.1 degrees in an ICRS (Right ascension [RA], Declination [DEC]) position (100.2417, 9.895).

For more information on how to use ADQL see:
    'https://www.ivoa.net/documents/latest/ADQL.html'

After obtaining the desire ID, download the product of the observation '1342205057' with the instrument 'PACS'.


.. doctest-skip::

  >>> HSA.download_data(observation_id='1342205057', retrieval_type='OBSERVATION', instrument_name='PACS')
  Downloading URL http://archives.esac.esa.int/hsa/whsa-tap-server/data?&retrieval_type=OBSERVATION&observation_id=1342205057&instrument_name=PACS to 1342205057.tar ... [Done]
  '1342205057.tar'


Troubleshooting
===============

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

.. code-block:: python

    >>> from astroquery.esa.hsa import HSA
    >>> HSA.clear_cache()

If this function is unavailable, upgrade your version of astroquery. 
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.

  
Reference/API
=============

.. automodapi:: astroquery.esa.hsa
    :no-inheritance-diagram:


.. testcleanup::

    >>> from astroquery.utils import cleanup_saved_downloads
    >>> cleanup_saved_downloads(['1342195355*', 'results.csv'])
