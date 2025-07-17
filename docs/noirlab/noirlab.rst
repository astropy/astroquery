.. _astroquery.noirlab:

****************************************
About the NSF NOIRLab Astro Data Archive
****************************************

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
==============

This research uses services or data provided by the Astro Data Archive at
NSF's NOIRLab. NOIRLab is operated by the Association of Universities for
Research in Astronomy (AURA), Inc. under a cooperative agreement with the
National Science Foundation.

**************************************
NOIRLab Queries (`astroquery.noirlab`)
**************************************

The methods in this module are wrappers around a set of web services
described in the
`REST API documentation <https://astroarchive.noirlab.edu/api/docs/>`_.
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

This set of methods supports *arbitrary searches of any fields*
stored in the FITS headers of the Archive.  Common fields ("core"
fields) are optimized for search speed. Less common fields ("aux"
fields) will be slower to search. You can search by File or HDU. The
primary method for doing the search is
:meth:`~astroquery.noirlab.NOIRLabClass.query_metadata`. That query
requires a JSON_ structure to define the query.  We often call this
the *JSON search spec*. Additional methods in this module
provide information needed to construct the JSON_ structure.
Summaries of the mechanisms available in the JSON search spec for
`File search <https://astroarchive.noirlab.edu/api/adv_search/fadoc/>`_
and for `HDU search
<https://astroarchive.noirlab.edu/api/adv_search/hadoc/>`_
are on the NSF NOIRLab Data Archive website.

These methods provide information needed to fill in a JSON_ query structure:

#. :meth:`~astroquery.noirlab.NOIRLabClass.aux_fields`
#. :meth:`~astroquery.noirlab.NOIRLabClass.core_fields`
#. :meth:`~astroquery.noirlab.NOIRLabClass.categoricals`

See the Reference/API below for details. The
:meth:`~astroquery.noirlab.NOIRLabClass.categoricals` method
returns a list of all the "category strings" such as names of
Instruments and Telescopes.  The :meth:`~astroquery.noirlab.NOIRLabClass.aux_fields`
and :meth:`~astroquery.noirlab.NOIRLabClass.core_fields` methods
tell you what fields are available to search. The core fields are
available for all instruments; searching on these fields is optimized
for speed. The aux fields require you to specify instrument and proctype.
The set of aux fields available is highly dependent on those two fields. The
instrument determines aux fields in raw files. Proctype determines
what kind of pipeline processing was done.  Pipeline processing often
adds important additional aux fields.

.. _JSON: https://www.json.org/json-en.html

Reference/API
=============

.. automodapi:: astroquery.noirlab
    :no-inheritance-diagram:
