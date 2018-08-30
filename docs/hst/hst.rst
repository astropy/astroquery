.. doctest-skip-all

.. _astroquery.hst:

*****************************
HST (`astroquery.hst`)
*****************************

Hubble Space Telescope (HST) is an orbiting astronomical observatory operating from the near-infrared into 
the ultraviolet. Launched in 1990 and scheduled to operate at least through 2020, HST carries and has 
carried a wide variety of instruments producing imaging, spectrographic, astrometric, and photometric 
data through both pointed and parallel observing programs. MAST is the primary archive and distribution 
center for HST data, distributing science, calibration, and engineering data to HST users and the 
astronomical community at large. Over 500 000 observations of more than 30000 targets are available 
for retrieval from the Archive.

This package allows the access to the European Space Agency Hubble Archive
(http://archives.esac.esa.int/ehst/)

========
Examples
========

---------------------------
1. Getting Hubble products
---------------------------

.. code-block:: python

  >>> from astroquery.hst import Hst
  >>>
  >>> Hst.get_product("J6FL25S4Q", "RAW", "raw_data_for_J6FL25S4Q.tar")
  http://archives.esac.esa.int/ehst-sl-server/servlet/data-action?OBSERVATION_ID=J6FL25S4Q&CALIBRATION_LEVEL=RAW

This will download all files for the raw calibration level of the observation 'J6FL25S4Q' and it will store them in a tar called 'raw_data_for_J6FL25S4Q.tar'.

---------------------------
2. Getting Hubble postcards
---------------------------

.. code-block:: python

  >>> from astroquery.hst import Hst
  >>>
  >>> Hst.get_postcard("J6FL25S4Q", "RAW", 256, "raw_postcard_for_J6FL25S4Q.tar")
  http://archives.esac.esa.int/ehst-sl-server/servlet/data-action?RETRIEVAL_TYPE=POSTCARD&OBSERVATION_ID=\
  J6FL25S4Q&CALIBRATION_LEVEL=RAW&RESOLUTION=256

This will download the postcard for the observation 'J8VP03010' with low resolution (256) and it will store it in a tar called 'raw_postcard_for_J6FL25S4Q.tar'. Resolution of 1024 is also available.

---------------------------
3. Getting Hubble artifacts
---------------------------

.. code-block:: python

  >>> from astroquery.hst import Hst
  >>>
  >>> Hst.get_artifact("O5HKAX030_FLT.FITS")
  http://archives.esac.esa.int/ehst-sl-server/servlet/data-action?ARTIFACT_ID=O5HKAX030_FLT.FITS

This will download the artifact 'O5HKAX030_FLT.FITS'.

---------------------------
4. Getting Hubble metadata
---------------------------

.. code-block:: python

  >>> from astroquery.hst import Hst
  >>>
  >>> Hst.get_metadata("RESOURCE_CLASS=ARTIFACT&OBSERVATION.OBSERVATION_ID=i9zg04010&SELECTED_FIELDS=ARTIFACT.\
  ARTIFACT_ID&RETURN_TYPE=VOTABLE", "metadata.xml")
  http://archives.esac.esa.int/ehst-sl-server/servlet/metadata-action?RESOURCE_CLASS=ARTIFACT&OBSERVATION.\
  OBSERVATION_ID=i9zg04010&SELECTED_FIELDS=ARTIFACT.ARTIFACT_ID&RETURN_TYPE=VOTABLE

This will download metadata for all artifact (product file) ids associated to observation 'i9zg04010' in VOTABLE format. The result of the query will be stored in file 'metadata.xml'.

---------------------------
5. Querying target names in Hubble archive
---------------------------

.. code-block:: python

  >>> from astroquery.hst import Hst
  >>>
  >>> Hst.query_target("m31", "m31_query.xml")
  http://archives.esac.esa.int/ehst-sl-server/servlet/metadata-action?RESOURCE_CLASS=OBSERVATION&\
  SELECTED_FIELDS=OBSERVATION&QUERY=(TARGET.TARGET_NAME=='m31')&RETURN_TYPE=VOTABLE

This will download metadata for all observations associated with target name 'm31'. The result of the query will be stored in file 'm31_query.xml'.

---------------------------
6. Cone searches in Hubble archive
---------------------------

.. code-block:: python

  >>> from astroquery.hst import Hst
  >>> from astropy import coordinates
  >>> import astropy.units as u
  >>> c = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s", frame='icrs')
  >>>
  >>> Hst.cone_search(c, 5, "cone_search_m31_5.xml")
  http://archives.esac.esa.int/ehst-sl-server/servlet/metadata-action?RESOURCE_CLASS=OBSERVATION&SELECTED_FIELDS\
  =OBSERVATION&QUERY=(POSITION.RA==10.685469872614046%20AND%20POSITION.DEC==41.26901534788858)&RETURN_TYPE=VOTABLE

This will perform a cone search with radius 5 arcmins. The result of the query will be stored in file 'cone_search_m31_5.xml'.

---------------------------
7. Getting access to catalogues 
---------------------------

.. code-block:: python

  >>> from astroquery.hst import Hst
  >>> result = Hst.query_hst_tap("select top 10 * from hsc_v2.hubble_sc2", "test.vot")
  >>> print(result)
  >>> result.get_results()

The will execute an ADQL query to download top 10 sources in HSC v2 (format default: votable). The result of the query will be stored in file 'test.vot'. The result of this query can be viewed by doing result.get_results() or printing it by doing print(result).

Reference/API
=============

.. automodapi:: astroquery.hst
    :no-inheritance-diagram:
