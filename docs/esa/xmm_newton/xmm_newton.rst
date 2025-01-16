.. _astroquery.esa.xmm_newton:

****************************************************
ESA XMM-Newton Archive (`astroquery.esa.xmm_newton`)
****************************************************


The X-ray Multi-Mirror Mission, XMM-Newton, is an ESA X-ray observatory launched on 10 December 1999.
It carries 3 high-throughput X-ray telescopes with unprecedented effective area and an Optical Monitor,
the first flown on an X-ray observatory.

This package allows the access to the `XMM-Newton Science Archive <https://nxsa.esac.esa.int/nxsa-web/>`__.
It has been developed by the ESAC Science Data Centre (ESDC) with requirements provided by the
XMM-Newton Science Operations Centre.

========
Examples
========

--------------------------
1. Getting XMM-Newton data
--------------------------

.. Skipping becuase the download takes too long
.. doctest-skip::

  >>> from astroquery.esa.xmm_newton import XMMNewton
  >>>
  >>> XMMNewton.download_data('0505720401', level="PPS" ,extension="PDF", instname="M1",
  ...                         filename="result0505720401")   # doctest: +IGNORE_OUTPUT
  Downloading URL https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0505720401&level=PPS&extension=PDF&instname=M1 to result0505720401.tar ...
  |==============================================================| 7.4M/7.4M (100.00%)         9s

This will download all PPS files for the observation '0505720401' and instrument MOS1, with 'PDF' extension and
it will store them in a tar called 'result0505720401.tar'. The parameters available are detailed in the API.

For more details of the parameters check the section 3.4 at:
		'https://nxsa.esac.esa.int/nxsa-web/#aio'

--------------------------------------
2. Getting XMM-Newton proprietary data
--------------------------------------
To access proprietary data an extra variable is needed in the XMMNewton.download_data method. This variabe is prop which
can be True or False. If True a username and password is needed. A username and password can be passed by adding another
variable to the XMMNewton.download_data method called credentials_file. This variable is a string with the path to
~/.astropy/config/astroquery.cfg file. Inside this file add your desired username and password, e.g.

.. code-block::

    [xmm_newton]
    username = your_username
    password = your_password

If the credentials_file variable is not provided the method will ask for the username and password to be added manually
from the commandline

.. Skipping proprietary example
.. doctest-skip::

  >>> from astroquery.esa.xmm_newton import XMMNewton
  >>>
  >>> XMMNewton.download_data('0505720401', level="PPS", extension="PDF", instname="M1",
  ...                         filename="result0505720401.tar", prop=True)
  INFO: File result0505720401.tar downloaded to current directory [astroquery.esa.xmm_newton.core]

This will download all PPS files for the observation '0505720401' and instrument MOS1, with 'PDF' extension and any
proprietary data. It will store them in a tar called 'result0505720401.tar'.

-------------------------------
3. Getting XMM-Newton postcards
-------------------------------

.. doctest-remote-data::

  >>> from astroquery.esa.xmm_newton import XMMNewton
  >>>
  >>> XMMNewton.get_postcard('0505720401')        # doctest: +IGNORE_OUTPUT
  INFO: File P0505720401EPX000OIMAGE8000.PNG downloaded to current directory [astroquery.esa.xmm_newton.core]
  'P0505720401EPX000OIMAGE8000.PNG'

This will download the EPIC postcard for the observation '0505720401' and it will stored in a PNG called
'P0505720401EPX000OIMAGE8000.PNG'.

------------------------------------------
4. Getting XMM-Newton metadata through TAP
------------------------------------------

This function provides access to the XMM-Newton Science Archive database using the Table Access Protocol (TAP) and via the Astronomical Data
Query Language (ADQL).

.. doctest-remote-data::

  >>> from astroquery.esa.xmm_newton import XMMNewton
  >>>
  >>> result = XMMNewton.query_xsa_tap("select top 10 * from v_public_observations",
  ...                                  output_format='csv', output_file='results10.csv')
  >>> print(result)     # doctest: +IGNORE_OUTPUT
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
5. Getting table details of XSA TAP
-----------------------------------

.. doctest-remote-data::

  >>> from astroquery.esa.xmm_newton import XMMNewton
  >>> XMMNewton.get_tables()
  INFO: Retrieving tables... [astroquery.utils.tap.core]
  INFO: Parsing tables... [astroquery.utils.tap.core]
  INFO: Done. [astroquery.utils.tap.core]
  ['public.dual', 'tap_config.coord_sys', 'tap_config.properties', 'tap_schema.columns',
   'tap_schema.key_columns', 'tap_schema.keys', 'tap_schema.schemas',
   'tap_schema.tables', 'xsa.v_all_observations', 'xsa.v_epic_source',
   'xsa.v_epic_source_cat', 'xsa.v_epic_xmm_stack_cat', 'xsa.v_exposure',
   'xsa.v_instrument_mode', 'xsa.v_om_source', 'xsa.v_om_source_cat',
   'xsa.v_proposal', 'xsa.v_proposal_observation_info', 'xsa.v_publication',
   'xsa.v_publication_observation', 'xsa.v_publication_slew_observation',
   'xsa.v_public_observations', 'xsa.v_public_observations_new_odf_ingestion',
   'xsa.v_public_observations_new_pps_ingestion', 'xsa.v_rgs_source',
   'xsa.v_slew_exposure', 'xsa.v_slew_observation', 'xsa.v_slew_source',
   'xsa.v_slew_source_cat', 'xsa.v_target_type', 'xsa.v_uls_exposure_image',
   'xsa.v_uls_slew_exposure_image']

This will show the available tables in XSA TAP service in the XMM-Newton Science Archive.

-------------------------------------
6. Getting columns details of XSA TAP
-------------------------------------

.. doctest-remote-data::

  >>> from astroquery.esa.xmm_newton import XMMNewton
  >>> XMMNewton.get_columns('xsa.v_all_observations')
  INFO: Retrieving tables... [astroquery.utils.tap.core]
  INFO: Parsing tables... [astroquery.utils.tap.core]
  INFO: Done. [astroquery.utils.tap.core]
  ['bii', 'citext', 'dec', 'duration', 'end_utc', 'footprint_fov', 'heasarc_code', 'lii', 'moving_target',
  'observation_equatorial_spoint', 'observation_fov_scircle', 'observation_galactic_spoint', 'observation_id',
  'observation_oid', 'odf_proc_date', 'odf_version', 'position_angle', 'pps_proc_date', 'pps_version', 'proposal_id',
  'proposal_oid', 'proprietary_end_date', 'ra', 'ra_nom', 'revolution', 'sas_version', 'seq_id', 'start_utc', 'stc_s', 'with_science']

This will show the column details of the table 'v_all_observations' in XSA TAP service in the XMM-Newton Science Archive.

--------------------------------------------
7. Getting EPIC images from a given TAR file
--------------------------------------------

.. Skipping becuase the download takes too long
.. doctest-skip::

  >>> from astroquery.esa.xmm_newton import XMMNewton
  >>>
  >>> XMMNewton.download_data('0405320501')   # doctest: +IGNORE_OUTPUT
  Downloading URL http://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0405320501 to 0405320501.tar ...
  |===================================================================================================================================================| 540M/540M (100.00%)        57s
  >>> XMMNewton.get_epic_images('0405320501.tar', band=[1,2], instrument=['M1'])
  {1: {'M1': '/home/esa/0405320501/pps/P0405320501M1S002IMAGE_1000.FTZ'}, 2: {'M1': '/home/esa/0405320501/pps/P0405320501M1S002IMAGE_2000.FTZ'}}

This will extract the European Photon Imaging Camera (EPIC) images within the specified TAR file, bands, and instruments. It will also return a dictionary containing the paths to the extracted files.

------------------------------------------------------------------------------
8. Getting the European Photon Imaging Camera (EPIC) metadata from the XSA TAP
------------------------------------------------------------------------------

This function retrieves the EPIC metadata from a given target.

The target must be defined with either a source name or a `~astropy.coordinates.SkyCoord` object.

The EPIC metadata can be found in four tables in the XSA TAP:

- xsa.v_epic_source
- xsa.v_epic_source_cat
- xsa.v_epic_xmm_stack_cat
- xsa.v_slew_source_cat

.. doctest-remote-data::

  >>> from astroquery.esa.xmm_newton import XMMNewton
  >>> epic_source, cat_4xmm, stack_4xmm, slew_source = XMMNewton.get_epic_metadata(target_name="4XMM J122934.7+015657")

This will return the metadata within the four TAP tables in four `~astropy.table.Table` for the given target.


Troubleshooting
===============

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

.. code-block:: python

    >>> from astroquery.esa.xmm_newton import XMMNewton
    >>> XMMNewton.clear_cache()

If this function is unavailable, upgrade your version of astroquery.
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.


Reference/API
=============

.. automodapi:: astroquery.esa.xmm_newton
    :no-inheritance-diagram:
