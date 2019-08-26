.. doctest-skip-all

.. _astroquery.esa.hubble:

************************************
esa.hubble (`astroquery.esa.hubble`)
************************************

The Hubble Space Telescope (HST) is a joint ESA/NASA orbiting astronomical
observatory operating from the near-infrared into the ultraviolet.  Launched
in 1990 and scheduled to operate at least through 2020, HST carries and has
carried a wide variety of instruments producing imaging, spectrographic,
astrometric, and photometric data through both pointed and parallel
observing programs. During its lifetime HST has become one of the most
important science projects ever, with over 500 000 observations of more than
30000 targets available for retrieval from the Archive.

This package allows the access to the `European Space Agency Hubble Archive
<http://archives.esac.esa.int/ehst/>`__. All the HST observations available
in the EHST are synchronised with the MAST services for HST reprocessed
public data and corresponding metadata.  Therefore, excluding proprietary
data, all HST data in the EHST are identical to those in MAST.

========
Examples
========

---------------------------
1. Getting Hubble products
---------------------------

.. code-block:: python

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = EsaHubble()
  >>> esahubble.download_product("J6FL25S4Q", "RAW", "raw_data_for_J6FL25S4Q.tar")

This will download all files for the raw calibration level of the
observation 'J6FL25S4Q' and it will store them in a tar called
'raw_data_for_J6FL25S4Q.tar'.

---------------------------
2. Getting Hubble postcards
---------------------------

.. code-block:: python

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = EsaHubble()
  >>> esahubble.get_postcard("J6FL25S4Q", "RAW", 256, "raw_postcard_for_J6FL25S4Q.jpg")

This will download the postcard for the observation 'J8VP03010' with low
resolution (256) and it will stored in a jpg called
'raw_postcard_for_J6FL25S4Q.jpg'. Resolution of 1024 is also available.

Calibration levels can be RAW, CALIBRATED, PRODUCT or AUXILIARY.

---------------------------
3. Getting Hubble artifacts
---------------------------

Note: Artifact is a single Hubble product file.

.. code-block:: python

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = EsaHubble()
  >>> esahubble.get_artifact("w0ji0v01t_c2f.fits.gz")

This will download the compressed artifact
'w0ji0v01t_c2f.fits.gz'. 'w0ji0v01t_c2f.fits' is the name of the Hubble
artifact to be download.

----------------------------------------------
4. Querying target names in the Hubble archive
----------------------------------------------

The query_target function queries the name of the target as given by the proposer of the observations.

.. code-block:: python

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = EsaHubble()
  >>> table = esahubble.query_target("m31", "m31_query.xml")
  >>> str(table)

This will retrieve a table with the output of the query.
It will also download a file storing all metadata for all observations
associated with target name 'm31'. The result of the query will be stored in
file 'm31_query.xml'.

--------------------------------------
5. Cone searches in the Hubble archive
--------------------------------------

.. code-block:: python

  >>> from astropy import coordinates
  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> c = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s", frame='icrs')
  >>> table = esahubble.cone_search(c, 7, "cone_search_m31_5.vot")
  >>> str(table)

This will perform a cone search with radius 7 arcmins. The result of the
query will be returned and stored in the votable file
'cone_search_m31_5.vot'.

-------------------------------
6. Getting access to catalogues
-------------------------------

This function provides access to the HST archive database using the Table
Access Protocol (TAP) and via the Astronomical Data Query Language (ADQL).

.. code-block:: python

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> result = esahubble.query_hst_tap("select top 10 * from hsc_v2.hubble_sc2", "test.vot.gz")
  >>> print(result)
  >>> result.get_results()

This will execute an ADQL query to download the first 10 sources in the
Hubble Source Catalog (HSC) version 2.1 (format default: compressed
votable). The result of the query will be stored in the file
'test.vot.gz'. The result of this query can be viewed by doing
result.get_results() or printing it by doing print(result).

Reference/API
=============

.. automodapi:: astroquery.esa.hubble
    :no-inheritance-diagram:
