.. doctest-skip-all

.. _astroquery.xmm_newton:

************************************
xmm_newton (`astroquery.xmm_newton`)
************************************


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
1. Getting XMM-Newton products
------------------------------

.. code-block:: python

  >>> from astroquery.xmm_newton import XMMNewton
  >>>
  >>> XMMNewton.download_product('0505720401',level="PPS",extension="PDF",instname="M1",filename="result0505720401.tar")

This will download all PPS files for the observation '0505720401' and instrument MOS1, with 'PDF' extension and 
it will store them in a tar called 'result0505720401.tar'. The parameters available are:

	observation_id : string
		id of the observation to be downloaded 10 digits, mandatory, example: 0144090201
		
	level : string
		level to download, optional, by default everything is downloaded, values: ODF, PPS
		
	instname : string
		instrument name, optional, two characters, by default everything, values: OM, R1, R2, M1, M2, PN
		
	instmode : string
		instrument mode, optional, examples: Fast, FlatFieldLow, Image, PrimeFullWindow
		
	filter : string
		filter, optional, examples: Closed, Open, Thick, UVM2, UVW1, UVW2, V

	expflag : string
		exposure flag, optional, by default everything, values: S, U, X(not applicable)

	expno : integer
		exposure number with 3 digits, by default all exposures, examples: 001, 003

	name : string
		product type, optional, 6 characters, by default all product types, examples: 3COLIM, ATTTSR, EVENLI, SBSPEC, EXPMAP, SRCARF

	datasubsetno : character
		data subset number, optional, by default all, examples: 0, 1

	sourceno : hex value
		source number, optional, by default all sources, example: 00A, 021, 001

	extension : string
		file format, optional, by default all formats, values: ASC, ASZ, FTZ, HTM, IND, PDF, PNG

	filename : string
		file name to be used to store the file, optional

	verbose : bool
		optional, default 'False', flag to display information about the process        
            
For more details of the parameters check the section 3.4 at:
		'http://nxsa.esac.esa.int/nxsa-web/#aio'

-------------------------------
2. Getting XMM-Newton postcards
-------------------------------

.. code-block:: python

  >>> from astroquery.xmm_newton import XMMNewton
  >>>
  >>> XMMNewton.get_postcard('0505720401')

This will download the EPIC postcard for the observation '0505720401' and it will stored in a PNG called
'P0505720401EPX000OIMAGE8000.PNG'. The parameters available are:

	observation_id : string
    	id of the observation for which download the postcard, mandatory
	image_type : string
		image type, optional, default 'OBS_EPIC'
        It can be: OBS_EPIC, OBS_RGS_FLUXED, OBS_RGS_FLUXED_2, OBS_RGS_FLUXED_3, OBS_EPIC_MT, OBS_RGS_FLUXED_MT, OBS_OM_V, OBS_OM_B, OBS_OM_U, OBS_OM_L, OBS_OM_M, OBS_OM_S, OBS_OM_W
	filename : string
 		file name to be used to store the postcard, optional, default None
	verbose : bool
		optional, default 'False'
		Flag to display information about the process


------------------------------------------
3. Getting XMM-Newton metadata through TAP 
------------------------------------------

This function provides access to the XMM-Newton Science Archive database using the Table Access Protocol (TAP) and via the Astronomical Data
Query Language (ADQL).

.. code-block:: python

  >>> from astroquery.xmm_newton import XMMNewton
  >>> result = XMMNewton.query_xsa_tap("select top 10 * from v_public_observations", output_format='csv', output_file='results10.csv')
  >>> print(result)

This will execute an ADQL query to download the first 10 observations in the XMM-Newton Science Archive. The result of the query will be 
stored in the file 'results10.csv'. The result of this query can be printed by doing print(result).

The parameters available are:
		query : str, mandatory
            query (adql) to be executed
        output_file : str, optional, default None
            file name where the results are saved
        output_format : str, optional, default 'votable'
            results format
        verbose : bool, optional, default 'False'
            flag to display information about the process
            
-----------------------------------
4. Getting table details of XSA TAP 
-----------------------------------

.. code-block:: python

  >>> from astroquery.xmm_newton import XMMNewton
  >>> XMMNewton.get_tables(True)

This will show the available tables in XSA TAP service in the XMM-Newton Science Archive.

The parameters available are:
		only_names : bool, TAP+ only, optional, default 'False'
            True to load table names only
        verbose : bool, optional, default 'False'
            flag to display information about the process
            
-------------------------------------
4. Getting columns details of XSA TAP 
-------------------------------------

.. code-block:: python

  >>> from astroquery.xmm_newton import XMMNewton
  >>> XMMNewton.get_columns('public.v_all_observations')

This will show the column details of the table 'v_all_observations' in XSA TAP service in the XMM-Newton Science Archive.

The parameters available are:
		table_name : string, mandatory, default None
            table name of which, columns will be returned
        only_names : bool, TAP+ only, optional, default 'False'
            True to load table names only
        verbose : bool, optional, default 'False'
            flag to display information about the process
            

Reference/API
=============

.. automodapi:: astroquery.xmm_newton
    :no-inheritance-diagram:
