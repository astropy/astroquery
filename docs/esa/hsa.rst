.. _astroquery.esa.hsa:

***********************************************
Herschel Science Archive (`astroquery.esa.hsa`)
***********************************************

`Herschel <https://www.cosmos.esa.int/web/herschel/home/>`__ was the fourth cornerstone in ESA's Horizon 2000 science programme, designed to observe the 'cool' universe.
It performed photometry and spectroscopy in the poorly explored 55-670 µm spectral range with a 3.5 m diameter
Cassegrain telescope, providing unique observing capabilities and bridging the gap between earlier infrared space
missions and groundbased facilities. Herschel successfully performed ~37000 science observations and ~6600 science
calibration observations which are publicly available to the worldwide astronomical community through the Herschel Science Archive.

This package allows the access to the `Herschel Science Archive <http://archives.esac.esa.int/hsa/whsa/>`__.

========
Examples
========

------------------------------
1. Getting Herschel data
------------------------------

.. doctest-remote-data::

  >>> from astroquery.esa.hsa import HSA
  >>>
  >>> HSA.download_data(observation_id='1342195355',retrieval_type='OBSERVATION', instrument_name='PACS')
  Downloading URL http://archives.esac.esa.int/hsa/whsa-tap-server/data?&retrieval_type=OBSERVATION&observation_id=1342195355&instrument_name=PACS to 1342195355.tar ... [Done]
  '1342195355.tar'

This will download the product of the observation '1342195355' with the instrument 'PACS' and
it will store them in a tar called '1342195355.tar'. The parameters available are detailed in the API.

For more details of the parameters check the section 6 of the 'Direct Product Access using TAP' in the 'HSA users guide' at:
		'http://archives.esac.esa.int/hsa/whsa/'

For more details about the products check:
                'https://www.cosmos.esa.int/web/herschel/data-products-overview'

-------------------------------
2. Getting Observation Products
-------------------------------

.. doctest-remote-data::

  >>> from astroquery.esa.hsa import HSA
  >>>
  >>> HSA.get_observation('1342195355', instrument_name='PACS')
  Downloading URL http://archives.esac.esa.int/hsa/whsa-tap-server/data?&retrieval_type=OBSERVATION&observation_id=1342195355&instrument_name=PACS to 1342195355.tar ... [Done]
  '1342195355.tar'

This will download the product of the observation '1342195355' with the instrument 'PACS' and
it will store them in a tar called '1342195355.tar'. The parameters available are detailed in the API.

`Notice`: There is no difference between the product retrieved with this method and `download_data`. `download_data` is a more generic
interface that allows the user to retrieve any product or metadata and `get_observation` allows the user to retrieve only observation products.

For more information check the section 6.1 of the of the 'direct Product Access using TAP' in the 'HSA users guide' at:
                'http://archives.esac.esa.int/hsa/whsa/'

For more details of the parameters check the section 6.2 of the 'Direct Product Access using TAP' in the 'HSA users guide' at:
		'http://archives.esac.esa.int/hsa/whsa/'

-------------------------------
3. Getting Herschel Postcard
-------------------------------

.. doctest-remote-data::

  >>> from astroquery.esa.hsa import HSA
  >>>
  >>> HSA.get_postcard('1342195355', instrument_name='PACS')
  Downloading URL http://archives.esac.esa.int/hsa/whsa-tap-server/data?&retrieval_type=POSTCARD&observation_id=1342195355&instrument_name=PACS to /home/dev/.astropy/cache/astroquery/HSA/data?&retrieval_type=POSTCARD&observation_id=1342195355&instrument_name=PACS ... [Done]
  '1342195355.jpg'

This will download the postcard (static representation in JPG-format of the final product) of the observation '1342195355' with the instrument 'PACS' and
it will store them in a tar called '1342195355.jpg'. The parameters available are detailed in the API.

For more details of the parameters check the section 6.2 of the 'Direct Product Access using TAP' in the 'HSA users guide' at:
		'http://archives.esac.esa.int/hsa/whsa/'

------------------------------------------
4. Getting Herschel metadata through TAP
------------------------------------------

This function provides access to the Herschel Science Archive database using the Table Access Protocol (TAP) and via the Astronomical Data
Query Language (`ADQL <https://www.ivoa.net/documents/ADQL/20180112/PR-ADQL-2.1-20180112.html>`__).

.. doctest-remote-data::

  >>> from astroquery.esa.hsa import HSA
  >>>
  >>> result = HSA.query_hsa_tap("select top 10 * from hsa.v_active_observation", output_format='csv', output_file='results.csv')
  >>> print(result)
                                aor                                      bii                 dec          duration  ... status            target_name             urn_version
  ------------------------------------------------------------ ------------------- ------------------- ---------- ... ------ ---------------------------------- -----------
                                              PPhot.Cart-perp  -33.71633333333334  -33.71633333333334  1759000.0 ... FAILED                          Cartwheel      925353
                                                    PPhot.Cart  -33.71633333333334  -33.71633333333334  1759000.0 ... FAILED                          Cartwheel      925352
  PPhoto-0005 - cosmos6 - cosmos_328-1 - XMMXCS J2215.9-1738-1 -17.633888888888887 -17.633888888888887 18149000.0 ... FAILED XMMXCS J2215.9-1738-1 cross scan-1      925351
                                                DRT-B-HD013246  -59.67941666666666  -59.67941666666666  2250000.0 ... FAILED                         HD013246-1      925350
                                                DRT-A-HD013246  -59.67941666666666  -59.67941666666666  2250000.0 ... FAILED                         HD013246-1      925348
                                    e0102green1_135  - hsc rec  -72.03119444444444  -72.03119444444444  4272000.0 ... FAILED                      1e0102.2-7219      925346
                                    e0102green1_45  - hsc rec  -72.03119444444444  -72.03119444444444  4272000.0 ... FAILED                      1e0102.2-7219      925344
                                    e0102blue1_135  - hsc rec  -72.03119444444444  -72.03119444444444  4272000.0 ... FAILED                      1e0102.2-7219      925342
                                      e0102blue1_45  - hsc rec  -72.03119444444444  -72.03119444444444  4272000.0 ... FAILED                      1e0102.2-7219      925340
                                              PPhot.AM06-perp  -74.22638888888889  -74.22638888888889  1759000.0 ... FAILED                         AM0644-741      925338

This will execute an ADQL query to download the first 10 observations in the Herschel Science Archive. The result of the query will be
stored in the file 'results.csv'. The result of this query can be printed by doing `print(result)`.

-----------------------------------
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

This will show the available tables in HSA TAP service in the Herschel Science Archive.

-------------------------------------
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

This will show the column details of the table 'hsa.v_active_observation' in HSA TAP service in the Herschel Science Archive.

-------------------------------------
7. Query Observations
-------------------------------------

.. code-block:: python

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

Retrieve a VOTable with the observation IDs of a given region

-------------------------------------
8. Procedure example
-------------------------------------

First retrieve the observation IDs based on a position on the sky. To achive this, query the TAP service.

.. code-block:: python

  >>> from astroquery.esa.hsa import HSA
  >>>
  >>> HSA.query_hsa_tap("select top 10 observation_id from hsa.v_active_observation where contains(point('ICRS', hsa.v_active_observation.ra, hsa.v_active_observation.dec),circle('ICRS', 100.2417,9.895, 1.1))=1", output_format='csv', output_file='results.cvs')
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

.. code-block:: python

  >>> HSA.download_data(observation_id='1342205057', retrieval_type='OBSERVATION', instrument_name='PACS')
  Downloading URL http://archives.esac.esa.int/hsa/whsa-tap-server/data?&retrieval_type=OBSERVATION&observation_id=1342205057&instrument_name=PACS to 1342205057.tar ... [Done]
  '1342205057.tar'

Reference/API
=============

.. automodapi:: astroquery.hsa
    :no-inheritance-diagram:
