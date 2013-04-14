.. _astroquery.irsadust:

************************************************************
IRSA Dust Extinction Service Queries (`astroquery.irsadust`)
************************************************************

Getting started
===============

Basic IRSA dust extinction service query:

.. code-block:: python

    >>> from astroquery import irsadust
    >>> dust_result = irsadust.query('m81', reg_size=2.2)
    >>> table = dust_result.table()
    >>> table.pprint()

        http://irsa.ipac.caltech.edu/cgi-bin/DUST/nph-dust?locstr=m81&regSize=2.2
        RA      Dec    coord sys regSize     ext desc     ... temp ref coord sys temp mean temp std temp max temp min
        --------- -------- --------- ------- ---------------- ... ------------------ --------- -------- -------- --------
        148.88822 69.06529 equ J2000     2.2 E(B-V) Reddening ...          equ J2000    17.157   0.0069  17.1796  17.1522


Multi-query example:

.. code-block:: python

    Query multiple objects with a single command:
    >>> dust_result = irsadust.query(['m101', 'm33', 'm15'])
    >>> table = dust_result.table()
    >>> table.pprint()

        http://irsa.ipac.caltech.edu/cgi-bin/DUST/nph-dust?locstr=m101
        http://irsa.ipac.caltech.edu/cgi-bin/DUST/nph-dust?locstr=m33
        http://irsa.ipac.caltech.edu/cgi-bin/DUST/nph-dust?locstr=m15
        RA      Dec    coord sys regSize     ext desc         ... temp ref coord sys temp mean temp std temp max temp min
        --------- -------- --------- ------- ---------------- ... ------------------ --------- -------- -------- --------
        210.80227 54.34895 equ J2000     5.0 E(B-V) Reddening ...          equ J2000   18.0045   0.0068  18.0267  18.0016
        023.46204 30.66022 equ J2000     5.0 E(B-V) Reddening ...          equ J2000     17.72   0.0148  17.7419  17.6914
        322.49304   12.167 equ J2000     5.0 E(B-V) Reddening ...          equ J2000   18.1562   0.0026  18.1619  18.

.. leading spaces in tables lead to indentation errors (so I added 0 in front of 23.46204 above)
    This is problematic, since it will break doctests

Fetch extinction detail table and fits images from links in initial response:
.. code-block:: python

    >>> dust_result = irsadust.query('266.12 -61.89 equ j2000')
    >>> detail_table = dust_result.ext_detail_table()
    >>> emission_image = dust_result.image('emission')
    >>> emission_image.writeto("image1.fits")
    >>> temperature_image = dust_result.image('temp')
    >>> temperature_image.writeto("image2.fits")

Reference/API
=============

.. automodapi:: astroquery.irsadust
    :no-inheritance-diagram:
