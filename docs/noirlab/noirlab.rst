.. doctest-skip-all

.. _astroquery.noirlab:

****************************************
About the NSF NOIRLab Astro Data Archive
****************************************

The NSF NOIRLab Astro Data Archive (formerly NOAO Science Archive)
provides access to data taken with more than 40 telescope and
instrument combinations, including those operated in partnership with
the WIYN, SOAR and SMARTS consortia, from semester 2004B to the
present. In addition to raw data, pipeline-reduced data products from
the DECam, Mosaic and NEWFIRM imagers are also available, as well as
advanced data products delivered by teams carrying out surveys and
other large observing programs with NSF OIR Lab facilities.

For more info about our holdings see the
`NSF NOIRLab Astro Data Archive <https://astroarchive.noirlab.edu/about/>`_

Acknowledgment
==============

This research uses services or data provided by the Astro Data Archive
at NSF's National Optical-Infrared Astronomy Research
Laboratory. NSF's OIR Lab is operated by the Association of
Universities for Research in Astronomy (AURA), Inc. under a
cooperative agreement with the National Science Foundation.

**************************************
NOIRLab Queries (`astroquery.noirlab`)
**************************************

The methods in this module are wrappers around a set of web services
described in the
`Rest API documentation <https://astroarchive.noirlab.edu/api/docs/>`_.
This data archive is hosted at the
`Community Science and Data Center (CDSC) <https://noirlab.edu/public/programs/csdc/>`_.


Getting started (SIA)
=====================

This module supports fetching the table of observation summaries from
the `NOIRLab data archive <https://astroarchive.noirlab.edu/>`_ given
your *Region Of Interest* query values.

In general, you can query the
`NOIRLab data archive <https://astroarchive.noirlab.edu/>`_
against full FITS files or against HDUs of those FITS files.  Most
users will likely prefer results against full FITS files (the
default). The search will likely be faster when searching files
compared to searching HDUs. If you are trying to retrieve HDU specific
image data from large files that contain many HDUs (such as DECam),
you can reduce your download time considerably by getting only
matching HDUs.

The results are returned in a `~astropy.table.Table`. The service
can be queried using the :meth:`~astroquery.noirlab.NOIRLabClass.query_region`. The
only required argument to this is the target coordinates around which
to query.  Specify the coordinates using the appropriate coordinate system from
`astropy.coordinates`. Here is a basic example:

.. code-block:: python

    >>> from astroquery.noirlab import NOIRLab
    >>> import astropy.coordinates as coord
    >>> from astropy import units as u
    >>> from astropy.coordinates import SkyCoord
    >>> coord = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')

    >>> noirlab_file = NOIRLab(which='file')
    >>> results_file = noirlab_file.query_region(coord, radius='0.1')
    >>> print(results_file)
                                archive_filename                             date_obs  ...             updated
                                     str71                                    str10    ...              str32
    ----------------------------------------------------------------------- ---------- ... --------------------------------
                                                                     string     string ...                           string
    /net/archive/mtn/20151027/kp4m/2015B-2001/k4m_151028_085849_ori.fits.fz 2015-10-28 ... 2020-02-09T01:17:17.842642+00:00
    /net/archive/mtn/20151027/kp4m/2015B-2001/k4m_151028_091327_ori.fits.fz 2015-10-28 ... 2020-02-09T01:17:17.875407+00:00
    /net/archive/mtn/20151027/kp4m/2015B-2001/k4m_151028_084112_ori.fits.fz 2015-10-28 ... 2020-02-09T01:17:18.303911+00:00
    /net/archive/mtn/20151120/kp4m/2015B-2001/k4m_151121_033641_ori.fits.fz 2015-11-21 ... 2020-02-09T01:24:35.525861+00:00
    /net/archive/mtn/20151120/kp4m/2015B-2001/k4m_151121_031258_ori.fits.fz 2015-11-21 ... 2020-02-09T01:24:37.873559+00:00
    /net/archive/mtn/20151120/kp4m/2015B-2001/k4m_151121_041031_ori.fits.fz 2015-11-21 ... 2020-02-09T01:24:38.951230+00:00

This is an example of searching by HDU.
.. note::

   Only some instruments have pipeline processing that populates the RA, DEC fields used for this search.

.. code-block:: python

    >>> from astroquery.noirlab import NOIRLabClass
    >>> noirlab_hdu = NOIRLabClass(which='hdu')
    >>> results_hdu = noirlab_hdu.query_region(coord, radius='0.1')
    >>> print(results_hdu)
                                    archive_filename                                  caldat    date_obs  ...    ra    telescope
                                         str79                                        str10      str10    ...   str8      str6
    ------------------------------------------------------------------------------- ---------- ---------- ... -------- ---------
                                                                             string     string     string ...    float    string
    /net/archive/pipe/20180211/kp4m/2016A-0453/k4m_180212_021444_ooi_zd_ls9.fits.fz 2018-02-11 2018-02-12 ... 10.60048      kp4m
     /net/archive/pipe/20180211/kp4m/2016A-0453/k4m_180212_030041_ooi_zd_v2.fits.fz 2018-02-11 2018-02-12 ... 10.43286      kp4m
                /net/archive/pipe/20151120/kp4m/k4m_151121_031038_ooi_zd_v1.fits.fz 2015-11-20 2015-11-21 ... 10.58226      kp4m
     /net/archive/pipe/20180211/kp4m/2016A-0453/k4m_180212_023526_ooi_zd_v2.fits.fz 2018-02-11 2018-02-12 ... 10.58187      kp4m
                /net/archive/pipe/20151120/kp4m/k4m_151121_031646_ooi_zd_v1.fits.fz 2015-11-20 2015-11-21 ... 10.56906      kp4m
                /net/archive/pipe/20151120/kp4m/k4m_151121_030945_ooi_zd_v1.fits.fz 2015-11-20 2015-11-21 ... 10.58203      kp4m
                /net/archive/pipe/20151120/kp4m/k4m_151121_031124_ooi_zd_v1.fits.fz 2015-11-20 2015-11-21 ... 10.58549      kp4m


Advanced Search
===============

This set of methods supports **arbitrary searches of any fields**
stored in the FITS headers of the Archive.  Common fields ("core"
fields) are optimized for search speed. Less common fields ("aux"
fields) will be slower to search. You can search by File or HDU. The
primary method for doing the search in ``query_metadata``. That query
requires a ``JSON`` structure to define the query.  We often call this
the *JSON search spec*. Many of the other
methods with this module are here to provide you with the information
you need to construct the ``JSON`` structure.
Summaries of the mechanisms available in the JSON search spec for
`File search <https://astroarchive.noirlab.edu/api/adv_search/fadoc/>`_
and for `HDU search
<https://astroarchive.noirlab.edu/api/adv_search/hadoc/>`_
are on the NSF NOIRLab Data Archive website.

There are three methods whose sole purpose if providing you with
information to help you with the content of your ``JSON`` structure.
They are:

#. aux_fields()
#. core_fields()
#. categoricals()

See the Reference/API below for details. The categoricals() method
returns a list of all the "category strings" such as names of
Instruments and Telescopes.  The aux/core_fields methods
tell you what fields are available to search. The core fields are
available for all instruments are the search for them is fast. The aux
fields require you to specify instrument and proctype.  The set of
fields available is highly dependent on those two fields. The
Instrument determines aux fields in raw files. Proctype determines
what kind of pipeline processing was done.  Pipeline processing often
adds important (aux) fields.


Reference/API
=============


.. automodapi:: astroquery.noirlab
    :no-inheritance-diagram:
