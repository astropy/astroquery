.. _astroquery.noirlab:

**************************************
NOIRLab Queries (`astroquery.noirlab`)
**************************************

Introduction
============

The methods in this module are wrappers around a set of web services
described in the
`REST API documentation <https://astroarchive.noirlab.edu/api/docs/>`_.
This data archive is hosted at the
`Community Science and Data Center (CDSC) <https://noirlab.edu/public/programs/csdc/>`_.


About the NSF NOIRLab Astro Data Archive
========================================

The NOIRLab Astro Data Archive (formerly NOAO Science Archive) provides
access to data taken with more than 40 telescope and instrument combinations,
including those operated in partnership with the WIYN, SOAR and SMARTS
consortia, from semester 2004B to the present. In addition to raw data,
pipeline-reduced data products from the DECam, Mosaic and NEWFIRM imagers
are also available, as well as advanced data products delivered by teams
carrying out surveys and other large observing programs with NSF NOIRLab
facilities.

For more info about our holdings see the
`NSF NOIRLab Astro Data Archive <https://astroarchive.noirlab.edu/about/>`_.

Acknowledgment
--------------

Please use the following acknowledgement in your publications when you use NOIRLab data:

This research uses services or data provided by the Astro Data Archive at
NSF's NOIRLab. NOIRLab is operated by the Association of Universities for
Research in Astronomy (AURA), Inc. under a cooperative agreement with the
National Science Foundation.


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

.. doctest-remote-data::

    >>> from astroquery.noirlab import NOIRLab
    >>> from astropy import units as u
    >>> from astropy.coordinates import SkyCoord
    >>> coord = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')
    >>> results_file = NOIRLab.query_region(coord, radius='0.1')
    >>> mosaic_filter = results_file['instrument'] == 'mosaic3'
    >>> print(results_file[mosaic_filter][['archive_filename', 'ra_center', 'dec_center']])
                                archive_filename                                ra_center          dec_center
    ----------------------------------------------------------------------- ------------------ -----------------
    /net/archive/mtn/20151120/kp4m/2015B-2001/k4m_151121_041031_ori.fits.fz 10.579374999999999 41.19416666666666
    /net/archive/mtn/20151120/kp4m/2015B-2001/k4m_151121_031258_ori.fits.fz 10.579374999999999 41.19416666666666
    /net/archive/mtn/20151027/kp4m/2015B-2001/k4m_151028_085849_ori.fits.fz 10.672041666666665 41.24944166666667
    /net/archive/mtn/20151027/kp4m/2015B-2001/k4m_151028_084112_ori.fits.fz 10.672041666666665 41.24944166666667
    /net/archive/mtn/20151120/kp4m/2015B-2001/k4m_151121_033641_ori.fits.fz 10.579374999999999 41.19416666666666
    /net/archive/mtn/20151027/kp4m/2015B-2001/k4m_151028_091327_ori.fits.fz 10.672041666666665 41.24944166666667

This is an example of searching by HDU.

.. note::

   Only some instruments have pipeline processing that populates the RA, DEC fields used for this search.

.. doctest-remote-data::

    >>> results_hdu = NOIRLab.query_region(coord, radius='0.1', hdu=True)
    >>> mosaic_hdu_filter = results_hdu['instrument'] == 'mosaic3'
    >>> print(results_hdu[mosaic_hdu_filter][['archive_filename', 'hdu_idx']])
                                    archive_filename                                hdu_idx
    ------------------------------------------------------------------------------- -------
     /net/archive/pipe/20180211/kp4m/2016A-0453/k4m_180212_030259_ooi_zd_v2.fits.fz       0
     /net/archive/pipe/20180211/kp4m/2016A-0453/k4m_180212_030259_ooi_zd_v2.fits.fz       1
    /net/archive/pipe/20180211/kp4m/2016A-0453/k4m_180212_021444_ooi_zd_ls9.fits.fz       2
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_031124_ooi_zd_v1.fits.fz       3
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_031819_ooi_zd_v1.fits.fz       0
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_031426_ooi_zd_v1.fits.fz       0
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_031426_ooi_zd_v1.fits.fz       1
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_031038_ooi_zd_v1.fits.fz       2
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_031038_ooi_zd_v1.fits.fz       3
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_031646_ooi_zd_v1.fits.fz       0
    /net/archive/pipe/20180211/kp4m/2016A-0453/k4m_180212_030259_ooi_zd_ls9.fits.fz       0
    /net/archive/pipe/20180211/kp4m/2016A-0453/k4m_180212_030259_ooi_zd_ls9.fits.fz       1
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_030855_ooi_zd_v1.fits.fz       2
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_031731_ooi_zd_v1.fits.fz       0
     /net/archive/pipe/20180211/kp4m/2016A-0453/k4m_180212_023526_ooi_zd_v2.fits.fz       1
    /net/archive/pipe/20180211/kp4m/2016A-0453/k4m_180212_030041_ooi_zd_ls9.fits.fz       2
    /net/archive/pipe/20180211/kp4m/2016A-0453/k4m_180212_030041_ooi_zd_ls9.fits.fz       3
     /net/archive/pipe/20180206/kp4m/2016A-0453/k4m_180207_024709_ooi_zd_v2.fits.fz       2
     /net/archive/pipe/20180211/kp4m/2016A-0453/k4m_180212_021444_ooi_zd_v2.fits.fz       2
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_031342_ooi_zd_v1.fits.fz       0
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_031342_ooi_zd_v1.fits.fz       1
     /net/archive/pipe/20180211/kp4m/2016A-0453/k4m_180212_030041_ooi_zd_v2.fits.fz       2
     /net/archive/pipe/20180211/kp4m/2016A-0453/k4m_180212_030041_ooi_zd_v2.fits.fz       3
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_030945_ooi_zd_v1.fits.fz       2
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_030809_ooi_zd_v1.fits.fz       2
    /net/archive/pipe/20180211/kp4m/2016A-0453/k4m_180212_023526_ooi_zd_ls9.fits.fz       1
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_031511_ooi_zd_v1.fits.fz       1
    /net/archive/pipe/20180206/kp4m/2016A-0453/k4m_180207_024709_ooi_zd_ls9.fits.fz       2
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_031904_ooi_zd_v1.fits.fz       0
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_030717_ooi_zd_v1.fits.fz       2
     /net/archive/pipe/20151120/kp4m/2015B-2001/k4m_151121_031558_ooi_zd_v1.fits.fz       1


Advanced Search
===============

The :meth:`~astroquery.noirlab.NOIRLabClass.query_metadata`
method supports *arbitrary searches of any fields*
stored in the FITS headers of the Archive.
There are a lot of these, so in addition to the documentation below,
there is helper method, :meth:`~astroquery.noirlab.NOIRLabClass.list_fields`,
to fetch information about archive fields in a programmatic way.

The input to :meth:`~astroquery.noirlab.NOIRLabClass.query_metadata` is a
JSON_ structure containing a list of fields to query and a list of search
parameters, sometimes called the *JSON search spec*.

.. doctest-remote-data::

    >>> qspec = {"outfields": ["md5sum", "archive_filename", "original_filename", "instrument", "proc_type"],
    ...          "search": [['original_filename', 'c4d_', 'contains']]}
    >>> results = NOIRLab.query_metadata(qspec, limit=3)
    >>> 'md5sum' in results.colnames
    True

Understanding Core versus Aux, File versus HDU, and Categoricals
----------------------------------------------------------------

Fields that are associated with all entries in the Archive are called "Core" fields.
These fields are optimized for fast searches. However, note that Core HDU files are different from Core File fields.

Aux File fields and Aux HDU fields depend on the "instrument" and "proctype". These
may slow down queries. Users should especially consider applying query limits in
this case.

"Instrument" and "proctype" are examples of categorical fields.
Categorical fields can only take on a special set of values. For example "instrument"
can have the values "decam" or "mosaic"; "proctype" can have the values "raw" or "stacked".

========================== =============================================================================== ========
If you need the list of... Run this query                                                                  See also
========================== =============================================================================== ========
Core File fields           ``NOIRLab.list_fields()``                                                       `File search <https://astroarchive.noirlab.edu/api/adv_search/fadoc/>`_
Core HDU fields            ``NOIRLab.list_fields(hdu=True)``                                               `HDU search <https://astroarchive.noirlab.edu/api/adv_search/hadoc/>`_
Aux File fields            ``NOIRLab.list_fields(aux=True, instrument="decam", proctype="raw")``
Aux HDU fields             ``NOIRLab.list_fields(aux=True, instrument="decam", proctype="raw", hdu=True)``
Categorical fields         ``NOIRLab.list_fields(categorical=True)``
========================== =============================================================================== ========

Once you have identified fields of interest, it is necessary to prepend HDU-specific
fields with ``hdu:`` *and* set ``hdu=True`` in the query.
Here is an example query that illustrates this.

.. doctest-remote-data::

    >>> qspec = {"outfields": ["md5sum", "archive_filename", "hdu:CD1_1", "hdu:CD1_2"],
    ...          "search": [["caldat", "2017-08-14", "2017-08-16"], ["instrument", "decam"], ["proc_type", "raw"]]}
    >>> results = NOIRLab.query_metadata(qspec, sort='md5sum', limit=3, hdu=True)
    >>> 'CD1_1' in results.colnames
    True


.. _JSON: https://www.json.org/json-en.html

Reference/API
=============

.. automodapi:: astroquery.noirlab
    :no-inheritance-diagram:
