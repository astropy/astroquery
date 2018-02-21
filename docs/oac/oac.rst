.. doctest-skip-all

.. _astroquery.oac:

********************************
OAC API Queries (`astroquery.oac`)
********************************

Getting started
===============

This module is designed to enable the full-functionality of the Open Astronomy
Catalog REST API into `astroquery` for easy access to data of supernovae,
Tidal Disruption Events (TDEs) and kilonovae. Examples of API usage and
available data products can be found at the `OAC API Github Repository <https://github.com/astrocatalogs/OACAPI>`_

Primary Methods
================
There are two primary methods for submitting API queries. The first is `query_object`
which can be used to search the OAC based on an event name. Multiple events can
be retrieved by submitting a list of event names.

The default behavior returns a top-level list of all available metadata for the
queries event(s).

.. code-block:: python
    >>> from astroquery.oac import OAC
    >>> metadata = OAC.query_object("GW170817")
    >>> print(metadata.keys())
    >>> ['event', 'hostoffsetdist', 'masses', 'ra', 'instruments',
         'lumdist', 'hostdec', 'host', 'velocity', 'ebv', 'hostra',
         'claimedtype', 'redshift', 'maxabsmag', 'alias', 'hostoffsetang',
         'download', 'maxdate', 'discoverdate', 'xraylink', 'dec',
         'maxappmag', 'radiolink', 'spectralink', 'references', 'name',
         'photolink']

The query can be further refined by using the available `QUANTIY` and `ATTRIBUTE`
options. For example, to retrieve the light curve for an object:

.. code-block:: python
    >>> photometry = OAC.query_object("GW170817", quantity="photometry",
                                      attribute=["time", "magnitude",
                                                 "e_magnitude", "band",
                                                 "instrument"])
    >>> print(photometry[:5])
    >>> event      time    magnitude e_magnitude band instrument
        -------- --------- --------- ----------- ---- ----------
        GW170817 57743.334     20.44                r
        GW170817 57790.358     21.39                r
        GW170817 57791.323     21.34                r
        GW170817 57792.326     21.26                r
        GW170817 57793.335     21.10                r

The results of a query can be further refined by using the `ARGUMENT` option

.. code-block:: python
    >>> photometry = OAC.query_object("GW170817", quantity="photometry",
                                      attribute=["time", "magnitude",
                                                 "e_magnitude", "band",
                                                 "instrument"],
                                      argument=["band=i"])
    >>> print(photometry[:5])
    >>>  event          time magnitude e_magnitude band instrument
        -------- ----------- --------- ----------- ---- ----------
        GW170817    57982.98      17.3                i
        GW170817  57982.9814     17.48        0.02    i      Swope
        GW170817 57983.00305     17.48        0.03    i      DECam
        GW170817    57983.05    16.984       0.050    i       ROS2
        GW170817 57983.23125     17.24        0.06    i        PS1

The second method available is `query_region` which performs a `cone` or `box`
search for a given set of coordinates. Coordinates can be submitted as an `Astropy`
`SkyCoord` object or a `list` with `[ra, dec]` structure. Coordinates can be
given in decimal degrees or sexigesimal units. The API can currently only query
a single set of coordinates.

For this example, we first establish coordinates and search parameters:

.. code-block:: python
    >>> import astropy.coordinates as coord
    >>> import astropy.units as u
    >>> from astroquery.oac import OAC

    >>> #Sample coordinates. We are using GW170817.
    >>> ra = 197.45037
    >>> dec = -23.38148
    >>> test_coords = coord.SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg))

    >>> test_radius = 10*u.arcsec
    >>> test_height = 10*u.arcsec
    >>> test_width = 10*u.arcsec

An example cone search:

.. code-block:: python
    >>> photometry = OAC.query_region(coordinates=test_coords,
                                      radius=test_radius,
                                      quantity="photometry",
                                      attribute=["time", "magnitude",
                                                 "e_magnitude", "band",
                                                 "instrument"])
    >>> print(photometry[:5])
    >>>  event      time   magnitude e_magnitude band instrument
        -------- --------- --------- ----------- ---- ----------
        GW170817 57743.334     20.44                r
        GW170817 57790.358     21.39                r
        GW170817 57791.323     21.34                r
        GW170817 57792.326     21.26                r
        GW170817 57793.335     21.10                r

An example box search:

.. code-block:: python
    >>> photometry = OAC.query_region(coordinates=test_coords,
                                      width=test_width, height=test_height,
                                      quantity="photometry",
                                      attribute=["time", "magnitude",
                                                 "e_magnitude", "band",
                                                 "instrument"])
    >>> print(photometry[:5])
    >>>  event      time   magnitude e_magnitude band instrument
        -------- --------- --------- ----------- ---- ----------
        GW170817 57743.334     20.44                r
        GW170817 57790.358     21.39                r
        GW170817 57791.323     21.34                r
        GW170817 57792.326     21.26                r
        GW170817 57793.335     21.10                r

As with the `query_object` method, searches using `query_region` can be refined
using the `QUANTIY`, `ATTRIBUTE`, and `ARGUMENT` options. The complete list of
available options can be found at the `OAC API Github Repository <https://github.com/astrocatalogs/OACAPI>`_

The default behavior for both methods is to return an `Astropy` table object.
Queries can also be returned as a `JSON` compliant dictionary using the
`data_format` option.

Tailored Methods
=================
There are three tailed search methods available to users to facilitate quick
retrieval of common data products.

The method `get_photometry` is designed to quickly return the photometry for a
given event or list of events.

.. code-block:: python
    >>> from astroquery.oac import OAC
    >>> photometry = OAC.get_photometry("SN2014J")
    >>> print(photometry[0:5])

    >>> event       time         magnitude     e_magnitude band instrument
        ------- -------------- ---------------- ----------- ---- ----------
        SN2014J 56677.68443724 11.3932586807338                R
        SN2014J 56678.31205141   11.00561836355                R
        SN2014J 56678.81414463 11.2078655297216               i'
        SN2014J 56678.84552409 12.5056184232995               g'
        SN2014J 56678.84552409 11.4662920294307               r'

The search can be refined using only the argument features of
`query_object`. More complex queries should use the base `query_object` method.

For example, to retrieve only R-band photometry:

.. code-block:: python
    >>> photometry = OAC.get_photometry("SN2014J", argument="band=R")
    >>> print(photometry[0:5])

    >>>  event       time         magnitude     e_magnitude band instrument
        ------- -------------- ---------------- ----------- ---- ----------
        SN2014J 56677.68443724 11.3932586807338                R
        SN2014J 56678.31205141   11.00561836355                R
        SN2014J       56678.87           11.105       0.021    R
        SN2014J 56678.90828613 11.1235949161792                R
        SN2014J 56679.06518967 11.0561795725355                R

The output is an `Astropy` table.

The method `get_single_spectrum` is designed to retrieve a single spectrum for a
single object at a specified time. The time should be given in `MJD,` but does
not have to be exact. The query will return the spectrum that is closest in time.

.. code-block:: python
    >>> from astroquery.oac import OAC
    >>> test_time = 57740
    >>> spectrum = OAC.get_single_spectrum("GW170817", time=test_time)
    >>> print(spectrum[0:5])
    >>> wavelength    flux
        ---------- ----------
        3501.53298 3.6411e-17
        3501.73298 4.0294e-17
        3502.33298 4.0944e-17
        3502.53298 4.1159e-17
        3502.73298 4.3485e-17

The output is an `Astropy` table.

The method `get_spectra`is designed to return all available spectra for an event
or list of events.

.. code-block:: python
    >>> from astroquery.oac import OAC
    >>> spectra = OAC.get_spectra("SN2014J")
    >>> print (spectra.keys())
    >>> dict_keys(['SN2014J'])
    >>> print (spectra["SN2014J"].keys())
    >>> dict_keys(['spectra'])
    >>> print (spectra["SN2014J"]["spectra"][0][0])
    >>> 56680.0
    >>> print (spectra["SN2014J"]["spectra"][0][1][0])
    >>> ['5976.1440', '1.17293e-14']

Note that the query must return a JSON-compliant dictionary which will
have nested lists of MJD and [wavelength, flux] pairs. Multiple spectra
can not be unwrapped into an `Astropy` table.

The basic dictionary structure is:
```{"event_name" : {"spectra" : [mjd_0, [[wavelength_0, flux_0], ... ,
[wavelength_n, flux_n]]], ... , [mjd_m, [[wavelength_0, flux_0], ... ,
[wavelength_n, flux_n]]]}}```

Reference/API
=============

.. automodapi:: astroquery.oac
    :no-inheritance-diagram:
