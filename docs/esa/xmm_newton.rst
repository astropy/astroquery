.. doctest-skip-all

.. _astroquery.esa.xmm_newton:

****************************************
xmm_newton (`astroquery.esa.xmm_newton`)
****************************************


The X-ray Multi-Mirror Mission, XMM-Newton, is an ESA X-ray observatory launched on 10 December 1999. 
It carries 3 high-throughput X-ray telescopes with unprecedented effective area and an Optical Monitor, 
the first flown on an X-ray observatory.

This package allows the access to the `XMM-Newton Science Archive <http://nxsa.esac.esa.int/nxsa-web/>`__. 
It has been developed by the ESAC Science Data Centre (ESDC) with requirements provided by the 
XMM-Newton Science Operations Centre.

========
Examples
========

------------------------------
1. Getting XMM-Newton data
------------------------------

.. code-block:: python

  >>> from astroquery.esa.xmm_newton import XMMNewton
  >>>
  >>> XMMNewton.download_data('0505720401',level="PPS",extension="PDF",instname="M1",filename="result0505720401.tar")
  INFO: File result0505720401.tar downloaded to current directory [astroquery.esa.xmm_newton.core]

This will download all PPS files for the observation '0505720401' and instrument MOS1, with 'PDF' extension and 
it will store them in a tar called 'result0505720401.tar'. The parameters available are detailed in the API.       

For more details of the parameters check the section 3.4 at:
		'http://nxsa.esac.esa.int/nxsa-web/#aio'

-------------------------------
2. Getting XMM-Newton postcards
-------------------------------

.. code-block:: python

  >>> from astroquery.esa.xmm_newton import XMMNewton
  >>>
  >>> XMMNewton.get_postcard('0505720401')
  INFO: File P0505720401EPX000OIMAGE8000.PNG downloaded to current directory [astroquery.esa.xmm_newton.core]
  'P0505720401EPX000OIMAGE8000.PNG'

This will download the EPIC postcard for the observation '0505720401' and it will stored in a PNG called
'P0505720401EPX000OIMAGE8000.PNG'.

------------------------------------------
3. Getting XMM-Newton metadata through TAP 
------------------------------------------

This function provides access to the XMM-Newton Science Archive database using the Table Access Protocol (TAP) and via the Astronomical Data
Query Language (ADQL).

.. code-block:: python

  >>> from astroquery.esa.xmm_newton import XMMNewton
  >>>
  >>> result = XMMNewton.query_xsa_tap("select top 10 * from v_public_observations", output_format='csv', output_file='results10.csv')
  >>> print(result)
          bii             dec    duration ...      target      with_science
  -------------------- --------- -------- ... ---------------- ------------
  4.1331178178373715  55.99944    32913 ...    XTE J0421+560         true
  0.05069186370709437 -32.58167    17083 ...         HD159176         true
  0.05069186370709437 -32.58167     9362 ...         HD159176         true
  0.05069186370709437 -32.58167    10859 ...         HD159176         true
  -0.31119608673831345  6.135278    21939 ...          HD47129         true
  -0.31119608673831345  6.135278    21863 ...          HD47129         true
  -51.687075256085755  10.68917    26609 ... IRAS F00235+1024         true
  73.04737400339847  10.18639    25192 ... IRAS F12514+1027         true
  46.71747372703565 -15.78639    12101 ...      Denis-J1228         true
  -15.881772371450268 -77.61555    33986 ...         Cha-Ha-3         true

This will execute an ADQL query to download the first 10 observations in the XMM-Newton Science Archive. The result of the query will be 
stored in the file 'results10.csv'. The result of this query can be printed by doing print(result).
            
-----------------------------------
4. Getting table details of XSA TAP 
-----------------------------------

.. code-block:: python

  >>> from astroquery.esa.xmm_newton import XMMNewton
  >>>
  >>> XMMNewton.get_tables()
  INFO: Retrieving tables... [astroquery.utils.tap.core]
  INFO: Parsing tables... [astroquery.utils.tap.core]
  INFO: Done. [astroquery.utils.tap.core]
  ['tap_schema.columns', 'tap_schema.key_columns', 'tap_schema.keys', 'tap_schema.schemas', 
  'tap_schema.tables', 'xsa.dual', 'xsa.v_all_observations', 'xsa.v_epic_source', 
  'xsa.v_epic_source_cat', 'xsa.v_epic_xmm_stack_cat', 'xsa.v_exposure', 'xsa.v_instrument_mode', 
  'xsa.v_om_source', 'xsa.v_om_source_cat', 'xsa.v_proposal', 'xsa.v_proposal_observation_info', 
  'xsa.v_publication', 'xsa.v_publication_observation', 'xsa.v_publication_slew_observation', 
  'xsa.v_public_observations', 'xsa.v_rgs_source', 'xsa.v_slew_exposure', 'xsa.v_slew_observation', 
  'xsa.v_slew_source', 'xsa.v_slew_source_cat', 'xsa.v_target_type', 'xsa.v_uls_exposure_image', 
  'xsa.v_uls_slew_exposure_image']

This will show the available tables in XSA TAP service in the XMM-Newton Science Archive.
            
-------------------------------------
5. Getting columns details of XSA TAP 
-------------------------------------

.. code-block:: python

  >>> from astroquery.esa.xmm_newton import XMMNewton
  >>>
  >>> XMMNewton.get_columns('public.v_all_observations')
  INFO: Retrieving tables... [astroquery.utils.tap.core]
  INFO: Parsing tables... [astroquery.utils.tap.core]
  INFO: Done. [astroquery.utils.tap.core]
  ['bii', 'citext', 'dec', 'duration', 'end_utc', 'footprint_fov', 'heasarc_code', 'lii', 'moving_target', 
  'observation_equatorial_spoint', 'observation_fov_scircle', 'observation_galactic_spoint', 'observation_id', 
  'observation_oid', 'odf_proc_date', 'odf_version', 'position_angle', 'pps_proc_date', 'pps_version', 'proposal_id', 
  'proposal_oid', 'proprietary_end_date', 'ra', 'ra_nom', 'revolution', 'sas_version', 'start_utc', 'stc_s', 'with_science']

This will show the column details of the table 'v_all_observations' in XSA TAP service in the XMM-Newton Science Archive.

--------------------------------------------
6. Getting EPIC images from a given TAR file 
--------------------------------------------

.. code-block:: python

  >>> from astroquery.esa.xmm_newton import XMMNewton
  >>>
  >>> XMMNewton.get_epic_images('tarfile.tar', band=[1,2], instrument=['M1'])
  {1: {'M1': '/home/dev/esa/0405320501/pps/P0405320501M1S002IMAGE_1000.FTZ'}, 2: {'M1': '/home/dev/esa/0405320501/pps/P0405320501M1S002IMAGE_2000.FTZ'}}

This will extract the European Photon Imaging Camera (EPIC) images within the specified TAR file, bands, and instruments. It will also return a dictionary containing the paths to the extracted files.        

Reference/API
=============

.. automodapi:: astroquery.esa.xmm_newton
    :no-inheritance-diagram:
