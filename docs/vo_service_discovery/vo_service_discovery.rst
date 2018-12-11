.. doctest-skip-all

.. _astroquery.vo_service_discovery:

*************************************************************************
Virtual Observatory Service Discovery (`astroquery.vo_service_discovery`)
*************************************************************************

Getting Started
===============

Archives from around the world have registered their services with the NASA
Astronomy Virtual Observatory (NAVO) directory. A web interface is available
at http://vao.stsci.edu/keyword-search/. This module provides methods
to query this directory by service type, keywords, wavelength band or coverage,
and source or publisher.

Here is an example showing how to find information about conesearch services
provided by the NASA Extragalactic Database (NED).

.. code-block:: python

    >>> from astroquery.vo_service_discovery import Registry
    >>> results = Registry.query(source='ned', service_type='cone')
    >>> print(results)

                                waveband                         ... service_type
        -------------------------------------------------------- ... ------------
                                                        infrared ...   conesearch
        radio#millimeter#infrared#optical#uv#euv#x-ray#gamma-ray ...   conesearch

The result of the query is an `astropy.table.Table` object. The methods of `Table`
can be used to inspect the search result.

.. code-block:: python
    >>> print(results.colnames)

        ['waveband', 'short_name', 'ivoid', 'res_description', 'access_url',
         'reference_url', 'publisher', 'service_type']

The value of `'access_url'` specifies the endpoint for the service.

Documentation of the service may be found in the `'reference_url'` values.
You can use a function from the Python standard library to open the second url
in a web browser.

.. code-block:: python

    >>> import webbrowser
    >>> webbrowser.open(results['reference_url'][1].decode())


Discovering Services
====================

The `astroquery.vo_service_discovery.Registry.query` method provides several
ways to search for specific services of interest. Each of these options
can be combined into a single call to the `query` method.

The ``service_type`` parameter can be set to the VO service types ``'conesearch'``,
``'simpleimageaccess'``, ``'simplespectralaccess'``, or ``'tableaccess'``. These
values may be shortened to ``'cone'``, ``'image'``, ``'spectra'`` or
``'spectrum'``, or ``'tap'`` or ``'table'``.

The value of the ``keyword`` parameter will return results containg that string
in the ``ivoid``, ``short_name``, or ``res_description`` fields.

Wavelength range can be specified by a string containing one or more band names.
The options include gamma-ray (wavelength below 0.1 Angstrom), x-ray
(0.1 to 100 Angstrom), euv (100-1000 Angstrom), uv (1000 to 3000 Angstrom),
optical (3000 to 10000 Angstrom), infrared (1 to 100 micron), millimeter (0.1 to
10 mm), or radio (greater than 10 mm wavelength). Multiple bands can be specified
with a comma-separated list.

The ``source`` parameter is a string that is matched to any substring in ivoid.

The ``publisher`` is the name of any publishing organization.

``order_by`` can be specified to sort the result by any of the column names.

The ADQL query can be printed by specifying ``verbose=True``.

The results of the query can be saved to a file. Set ``dump_to_file=True`` to save
the results table. The format will be ``'votable'`` by default; you can change this
with the ``output_format`` option. The result will be saved to a filename using
the TAP job ID; you can specify the filename with the ``output_file`` option.

By default, the query is made using the  registry TAP URL. The ``url`` option
will override that value. Alternatively, the configuration can be changed
to use a different URL.

.. code-block:: python

    >>> from astroquery.vo_service_discovery import Registry
    >>> result = Registry.query(service_type='tap', source='heasarc', verbose=True)

    Registry:  sending query ADQL =
              select res.waveband,res.short_name,cap.ivoid,res.res_description,
              intf.access_url,res.reference_url,res_role.role_name as publisher,cap.cap_type as service_type
              from rr.capability as cap
                natural join rr.resource as res
                natural join rr.interface as intf
                natural join rr.res_role as res_role
                 where cap.cap_type like '%tableaccess%' and cap.ivoid like '%heasarc%' and res_role.base_role = 'publisher'

    Queried: https://vao.stsci.edu/RegTAP/TapService.aspx/sync

    >>> print(result)

    waveband short_name ...  publisher   service_type
    -------- ---------- ... ------------ ------------
                HEASARC ... NASA/HEASARC  tableaccess


Counting available services
===========================

The `query_counts` method will enumerate how many services are available
for the ``'service_type''', ``'waveband'`` or ``'publisher'`` fields.

.. code-block:: python

    >>> from astroquery.vo_service_discovery import Registry
    >>> result = Registry.query_counts(field='service_type')
    >>> print(result)

           service_type       count_service_type
    ------------------------- ------------------
                   capability              59214
                   conesearch              21453
            simpleimageaccess                334
         simplespectralaccess                115
                  tableaccess                 97
                      edition                 86
                ceacapability                 56
                      harvest                 41
             simpletimeaccess                 31
                  openskynode                 27
                       search                  8
    theoreticalspectralaccess                  5
                     heliotap                  5
          protospectralaccess                  4
             simplelineaccess                  3

The ``minimum`` option defaults to 1 and specifies the minimum counts needed for
a row to be listed in the results table. `query_counts` includes the same
``verbose``, ``url`` and file output options as described for the `query` method
in the preceding section.


You can get a table of all publishers with at least 15 services:

.. code-block:: python

    >>> from astroquery.vo_service_discovery import Registry
    >>> results = Registry.query_counts('publisher', minimum=15, verbose=True)
    >>> print(results)

        Registry:  sending query ADQL = select * from (select role_name as publisher, count(role_name) as count_publisher from rr.res_role where base_role = 'publisher'  group by role_name) as count_table where count_publisher >= 15 order by count_publisher desc

    Queried: https://vao.stsci.edu/RegTAP/TapService.aspx/sync

                                              publisher                                           ...
    --------------------------------------------------------------------------------------------- ...
                                                                                              CDS ...
                                                                                NASA/GSFC HEASARC ...
                                                               NASA/IPAC Infrared Science Archive ...
                                                                                 The GAVO DC team ...
                                                        Space Telescope Science Institute Archive ...
                                           WFAU, Institute for Astronomy, University of Edinburgh ...
                                                                                          SVO CAB ...
                                                                                              IA2 ...
                                                                   Canadian Astronomy Data Centre ...
                                     Sternberg Astronomical Institute Virtual Observatory Project ...
                                                                                            Helio ...
                                                                                             MSSL ...
                                                                                        Astrogrid ...
                                                                            European Space Agency ...
                                                                                              JHU ...
                                                             The NASA/IPAC Extragalactic Database ...
    Stellar Department of Astronomical Institute of the Academy of Sciences of the Czech Republic ...
                                                                                              JVO ...
                                                           Paris Astronomical Data Centre - LESIA ...


Reference/API
=============

.. automodapi:: astroquery.vo_service_discovery
    :no-inheritance-diagram:

.. _Table Acess Protocol standard: http://www.ivoa.net/documents/TAP/

.. _Registry Relational Schema standard: http://www.ivoa.net/documents/RegTAP/

.. _Astronomical Query Data Language (2.0): http://www.ivoa.net/documents/latest/ADQL.html

