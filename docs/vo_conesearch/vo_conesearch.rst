.. doctest-skip-all

.. _astroquery.voconesearch:

****************************************************
VO Simple Cone Search (``astroquery.vo_conesearch``)
****************************************************

Astroquery offers Simple Cone Search Version 1.03 as defined in IVOA
Recommendation (February 22, 2008). Cone Search queries an
area encompassed by a given radius centered on a given RA and Dec and returns
all the objects found within the area in the given catalog.

This was ported from ``astropy.vo``:

* ``astropy.vo.client.conesearch`` is now `astroquery.vo_conesearch.conesearch`
* ``astropy.vo.validator`` is now ``astroquery.vo_conesearch.validator``

``astroquery.vo_conesearch.ConeSearch`` is a Cone Search API that adheres to
Astroquery standards but unlike Astropy's version, it only queries one given
service URL, which defaults to HST Guide Star Catalog. This default is
controlled by ``astroquery.vo_conesearch.conf.fallback_url``.


.. _vo-sec-default-scs-services:

Default Cone Search Services
============================

For the "classic" API ported from Astropy, the default Cone Search services
used are a subset of those found in the STScI VAO Registry.
They were hand-picked to represent commonly used catalogs below:

* 2MASS All-Sky
* HST Guide Star Catalog (also default for "new" Astroquery-style API)
* SDSS Data Release 7
* SDSS-III Data Release 8
* USNO A1
* USNO A2
* USNO B1

This subset undergoes daily validations hosted by STScI using
:ref:`vo-sec-validator-validate`. Those that pass without critical
warnings or exceptions are used by :ref:`vo-sec-client-scs` by
default. They are controlled by
``astroquery.vo_conesearch.conf.conesearch_dbname``:

#. ``'conesearch_good'``
   Default. Passed validation without critical warnings and exceptions.
#. ``'conesearch_warn'``
   Has critical warnings but no exceptions. Use at your own risk.
#. ``'conesearch_exception'``
   Has some exceptions. *Never* use this.
#. ``'conesearch_error'``
   Has network connection error. *Never* use this.

If you are a Cone Search service provider and would like to include your
service in the list above, please open a
`GitHub issue on Astroquery <https://github.com/astropy/astroquery/issues>`_.


Caching
=======

Caching of downloaded contents is controlled by `astropy.utils.data`.
To use cached data, some functions in this package have a ``cache``
keyword that can be set to ``True``.


Getting Started
===============

This section only contains minimal examples showing how to perform
basic Cone Search.

Query STScI Guide Star Catalog using "new" Astroquery-style API
around M31 with a 0.1-degree search radius:

>>> from astropy.coordinates import SkyCoord
>>> from astroquery.vo_conesearch import ConeSearch
>>> c = SkyCoord.from_name('M31')
>>> c
<SkyCoord (ICRS): (ra, dec) in deg
    (10.6847083, 41.26875)>
>>> result = ConeSearch.query_region(c, '0.1 deg')
>>> result
<Table length=4028>
    objID           gsc2ID      gsc1ID ... multipleFlag compassGSC2id   Mag
                                       ...                              mag
    int64           object      object ...    int32         int64     float32
-------------- ---------------- ------ ... ------------ ------------- -------
23323175812944 00424433+4116085        ...            0 6453800072293   9.453
23323175812948 00424403+4116069        ...            0 6453800072297   9.321
23323175812933 00424455+4116103        ...            0 6453800072282  10.773
23323175812939 00424464+4116092        ...            0 6453800072288   9.299
23323175812930 00424403+4116108        ...            0 6453800072279  11.507
23323175812931 00424464+4116106        ...            0 6453800072280   9.399
           ...              ...    ... ...          ...           ...     ...
  133001227000     N33001227000        ...            0 6453800007000 20.1382
 1330012244001    N330012244001        ...            0 6453800044001 21.8968
 1330012228861    N330012228861        ...            0 6453800028861 20.3572
 1330012212014    N330012212014        ...            0 6453800012014 16.5079
 1330012231849    N330012231849        ...            0 6453800031849 20.2869
 1330012210212    N330012210212        ...            0 6453800010212 20.2767
>>> result.url
'http://gsss.stsci.edu/webservices/vo/ConeSearch.aspx?CAT=GSC23'

List the available Cone Search catalogs that passed daily validation:

>>> from astroquery.vo_conesearch import conesearch
>>> conesearch.list_catalogs()
Downloading https://astroconda.org/aux/vo_databases/conesearch_good.json
|==========================================|  59k/ 59k (100.00%)         0s
['Guide Star Catalog 2.3 Cone Search 1',
 'SDSS DR7 - Sloan Digital Sky Survey Data Release 7 1',
 'SDSS DR7 - Sloan Digital Sky Survey Data Release 7 2', ...,
 'Two Micron All Sky Survey (2MASS) 2']

Query the HST Guide Star Catalog around M31 with a 0.1-degree search radius.
This is the same query as above but using "classic" Astropy-style API:

>>> from astropy import units as u
>>> my_catname = 'Guide Star Catalog 2.3 Cone Search 1'
>>> result = conesearch.conesearch(c, 0.1 * u.degree, catalog_db=my_catname)
Trying http://gsss.stsci.edu/webservices/vo/ConeSearch.aspx?CAT=GSC23&
WARNING: W50: ...: Invalid unit string 'pixel' [...]
>>> result
<Table length=4028>
    objID           gsc2ID      gsc1ID ... multipleFlag compassGSC2id   Mag
                                       ...                              mag
    int64           object      object ...    int32         int64     float32
-------------- ---------------- ------ ... ------------ ------------- -------
23323175812944 00424433+4116085        ...            0 6453800072293   9.453
23323175812948 00424403+4116069        ...            0 6453800072297   9.321
23323175812933 00424455+4116103        ...            0 6453800072282  10.773
23323175812939 00424464+4116092        ...            0 6453800072288   9.299
23323175812930 00424403+4116108        ...            0 6453800072279  11.507
23323175812931 00424464+4116106        ...            0 6453800072280   9.399
           ...              ...    ... ...          ...           ...     ...
  133001227000     N33001227000        ...            0 6453800007000 20.1382
 1330012244001    N330012244001        ...            0 6453800044001 21.8968
 1330012228861    N330012228861        ...            0 6453800028861 20.3572
 1330012212014    N330012212014        ...            0 6453800012014 16.5079
 1330012231849    N330012231849        ...            0 6453800031849 20.2869
 1330012210212    N330012210212        ...            0 6453800010212 20.2767
>>> result.url
'http://gsss.stsci.edu/webservices/vo/ConeSearch.aspx?CAT=GSC23'

Get the number of matches and returned column names:

>>> len(result)
4028
>>> result.colnames
['objID',
 'gsc2ID',
 'gsc1ID',
 'hstID',
 'ra',
 'dec', ...,
 'Mag']

Extract RA and Dec of the matches:

>>> result_skycoord = SkyCoord(result['ra'], result['dec'])
>>> result_skycoord
<SkyCoord (ICRS): (ra, dec) in deg
    [(10.684737  , 41.269035  ), (10.683469  , 41.268585  ),
     (10.685657  , 41.26955   ), ..., (10.58375359, 41.33386612),
     (10.55860996, 41.30061722), (10.817729  , 41.26915741)]>


Using ``astroquery.vo_conesearch``
==================================

This package has four main components across two categories:

.. toctree::
   :maxdepth: 2

   client
   validator

They are designed to be used in a work flow as illustrated below:

.. image:: images/astroquery_vo_flowchart.png
    :width: 500px
    :alt: VO work flow

The one that a typical user needs is the :ref:`vo-sec-client-scs` component
(see :ref:`Cone Search Examples <vo-sec-scs-examples>`).


See Also
========

- `Simple Cone Search Version 1.03, IVOA Recommendation (22 February 2008) <http://www.ivoa.net/Documents/REC/DAL/ConeSearch-20080222.html>`_

- `STScI VAO Registry <http://vao.stsci.edu/directory/NVORegInt.asmx?op=VOTCapabilityPredOpt>`_

- `STScI VO Databases <https://astroconda.org/aux/vo_databases/>`_


Reference/API
=============

.. automodapi:: astroquery.vo_conesearch.core

.. automodapi:: astroquery.vo_conesearch.vos_catalog
   :no-inheritance-diagram:

.. automodapi:: astroquery.vo_conesearch.conesearch
   :no-inheritance-diagram:

.. automodapi:: astroquery.vo_conesearch.vo_async
   :no-inheritance-diagram:

.. automodapi:: astroquery.vo_conesearch.exceptions

.. automodapi:: astroquery.vo_conesearch.validator.validate
   :no-inheritance-diagram:

.. automodapi:: astroquery.vo_conesearch.validator.inspect
   :no-inheritance-diagram:

.. automodapi:: astroquery.vo_conesearch.validator.exceptions
