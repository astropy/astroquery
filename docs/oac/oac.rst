.. doctest-skip-all

.. _astroquery.oac:

**********************************
OAC API Queries (`astroquery.oac`)
**********************************

Getting started
===============

This module is designed to enable the full-functionality of the Open Astronomy
Catalog REST API for easy access to data of supernovae, Tidal Disruption Events (TDEs)
and kilonovae. Examples of API usage and available data products can be found
at the `OAC API Github Repository <https://github.com/astrocatalogs/OACAPI>`_

Primary Methods
===============
There are two primary methods for submitting API queries. The first is query_object
which can be used to search the OAC based on an event name. Multiple events can
be retrieved by submitting a list of event names.

The default behavior returns a top-level list of all available metadata for the
queried event(s).

.. code-block:: python

    >>> from astroquery.oac import OAC
    >>> metadata = OAC.query_object("GW170817")

The query can be further refined by using the available QUANTITY and ATTRIBUTE
options. For example, to retrieve the light curve for an object:

.. code-block:: python

    >>> photometry = OAC.query_object("GW170817", quantity="photometry",
                                      attribute=["time", "magnitude",
                                                 "e_magnitude", "band",
                                                 "instrument"])

The results of a query can be further refined by using the ARGUMENT option

.. code-block:: python

    >>> photometry = OAC.query_object("GW170817", quantity="photometry",
                                      attribute=["time", "magnitude",
                                                 "e_magnitude", "band",
                                                 "instrument"],
                                      argument=["band=i"])

The second method available is query_region which performs a cone or box
search for a given set of coordinates. Coordinates can be submitted as an Astropy
SkyCoord object or a list with [ra, dec] structure. Coordinates can be
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

An example box search:

.. code-block:: python

    >>> photometry = OAC.query_region(coordinates=test_coords,
                                      width=test_width, height=test_height,
                                      quantity="photometry",
                                      attribute=["time", "magnitude",
                                                 "e_magnitude", "band",
                                                 "instrument"])

As with the query_object method, searches using query_region can be refined
using the QUANTITY, ATTRIBUTE, and ARGUMENT options. The complete list of
available options can be found at the `OAC API Github Repository <https://github.com/astrocatalogs/OACAPI>`_

The default behavior for both methods is to return an Astropy table object.
Queries can also be returned as a JSON compliant dictionary using the
data_format option.

Tailored Methods
================
There are three tailed search methods available to users to facilitate quick
retrieval of common data products.

The method get_photometry is designed to quickly return the photometry for a
given event or list of events.

.. code-block:: python

    >>> from astroquery.oac import OAC
    >>> photometry = OAC.get_photometry("SN2014J")

The search can be refined using only the argument features of
query_object. More complex queries should use the base query_object method.

For example, to retrieve only R-band photometry:

.. code-block:: python

    >>> photometry = OAC.get_photometry("SN2014J", argument="band=R")

The output is an Astropy table.

The method get_single_spectrum is designed to retrieve a single spectrum for a
single object at a specified time. The time should be given in MJD, but does
not have to be exact. The query will return the spectrum that is closest in time.

.. code-block:: python

    >>> from astroquery.oac import OAC
    >>> test_time = 57740
    >>> spectrum = OAC.get_single_spectrum("GW170817", time=test_time)

The output is an Astropy table.

The method get_spectra is designed to return all available spectra for an event
or list of events.

.. code-block:: python

    >>> from astroquery.oac import OAC
    >>> spectra = OAC.get_spectra("SN2014J")

Note that the query must return a JSON-compliant dictionary which will
have nested lists of MJD and [wavelength, flux] pairs. Multiple spectra
can not be unwrapped into an Astropy table.

The basic dictionary structure is:

{"event_name" : {"spectra" : [mjd_0, [[wavelength_0, flux_0], ... ,
[wavelength_n, flux_n]]], ... , [mjd_m, [[wavelength_0, flux_0], ... ,
[wavelength_n, flux_n]]]}}

Reference/API
=============

.. automodapi:: astroquery.oac
    :no-inheritance-diagram:
