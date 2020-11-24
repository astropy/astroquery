.. doctest-skip-all
.. # To render rst files to HTML: python setup.py build_docs
.. # When above stops working (astroquery removes helpers) do next:
.. # cd docs; make html

.. _astroquery.noirlab:

**************************************
NOIRLab Queries (`astroquery.noirlab`)
**************************************

Getting started
===============

This module supports fetching the table of observation summaries from
the `NOIRLab data archive <https://astroarchive.noao.edu/>`_. The `Rest API
documentation <https://astroarchive.noao.edu/api/docs/>`_ is the most
up-to-date info on the web-services used by this module.
The archive is hosted at
`NOIR-CSDC <https://nationalastro.org/programs/csdc/>`_.

The results are returned in a `~astropy.table.Table`. The service
can be queried using the :meth:`~astroquery.noirlab.NoirlabClass.query_region`. The
only required argument to this is the target coordinates around which
to query.  Specify the coordinates using the appropriate coordinate system from
`astropy.coordinates`. Here is a basic example:

.. code-block:: python

    >>> from astroquery.noirlab import Noirlab
    >>> import astropy.coordinates as coord
    >>> from astropy import units as u
    >>> from astropy.coordinates import SkyCoord
    >>> coord = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')

    >>> noirlab_file = Noirlab(which='file')
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

    >>> noirlab_hdu = Noirlab(which='hdu')
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



Reference/API
=============


.. automodapi:: astroquery.noirlab
    :no-inheritance-diagram:
