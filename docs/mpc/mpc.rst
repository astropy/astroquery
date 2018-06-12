.. doctest-skip-all

.. _astroquery.mpc:

**********************************************
Minor Planet Center Queries (`astroquery.mpc`)
**********************************************

Getting started
===============

This is an Astroquery wrapper for querying the
`Minor Planet Center <https://minorplanetcenter.net/web_service//>`__
web service, which returns the pure JSON response from the service.

The MPC web service allows for querying by any of the parameters listed in the function headers,
and also allows for querying for a range of values.

Querying with varying forms of selection parameters
---------------------------------------------------

Parameters can be queried in three manners:
    - Exact match
    - with a _min suffix, which sets the minimum value for the parameter
    - with a _max suffix, which sets the maximum value for the parameter

An example of an exact match:

.. code-block:: python

    >>> from astroquery.mpc import MPC
    >>> mpc = MPC()
    >>> result = mpc.query_object_async(name='ceres')
    >>> print(result.json())

    [{'absolute_magnitude': '3.34', 'aphelion_distance': '2.976', 'arc_length': 79247, 'argument_of_perihelion': '73.11528', 'ascending_node': '80.3099167', 'critical_list_numbered_object': False, 'delta_v': 10.5, 'designation': None, 'earth_moid': 1.59353, 'eccentricity': '0.0755347', 'epoch': '2018-03-23.0', 'epoch_jd': '2458200.5', 'first_observation_date_used': '1801-01-31.0', 'first_opposition_used': '1801', 'inclination': '10.59351', 'jupiter_moid': 2.09509, 'km_neo': False, 'last_observation_date_used': '2018-01-20.0', 'last_opposition_used': '2018', 'mars_moid': 0.939285, 'mean_anomaly': '352.23052', 'mean_daily_motion': '0.2141308', 'mercury_moid': 2.18454, 'name': 'Ceres', 'neo': False, 'number': 1, 'observations': 6689, 'oppositions': 114, 'orbit_type': 0, 'orbit_uncertainty': '0', 'p_vector_x': '-0.87827466', 'p_vector_y': '0.33795664', 'p_vector_z': '0.33825868', 'perihelion_date': '2018-04-28.28378', 'perihelion_date_jd': '2458236.78378', 'perihelion_distance': '2.5580384', 'period': '4.6', 'pha': False, 'phase_slope': '0.12', 'q_vector_x': '-0.44248615', 'q_vector_y': '-0.84255514', 'q_vector_z': '-0.30709419', 'residual_rms': '0.6', 'saturn_moid': 6.38856, 'semimajor_axis': '2.7670463', 'tisserand_jupiter': 3.3, 'updated_at': '2018-02-26T17:29:46Z', 'uranus_moid': 15.6642, 'venus_moid': 1.84632}]

A minimum value:

.. code-block:: python

    >>> result = mpc.query_objects_async(inclination_min=170)

Which will get all objects with an inclination of greater than or equal to 170.

A maximum value:

.. code-block:: python

    >>> result = mpc.query_objects_async(inclination_max=1.0)
    
Which will get all objects with an inclination of less than or equal to 1.

Sorting results, setting limits, and ```is_not_null```
------------------------------------------------------

The MPC web service allows a consumer to sort results in order to find a number of objects
fitting into the top or bottom of a range of values (or all, if truly desired).

The service also allows a consumer to limit their results to a number of objects, which,
when paired with sorting, creates very flexible options.

.. code-block:: python

    >>> result = mpc.query_object_async(order_by_desc="semimajor_axis", limit=10)

This will return the 10 furthest asteroids.

There is another parameter that can be used, ```is_not_null```. This can be used in the following
fashion:

.. code-block:: python

    >>> result = mpc.query_object_async(name="is_not_null")

This will, predictably, find all named objects in the MPC database--but that would take a while!

Customizing return fields
-------------------------

If a consumer isn't interested in some return fields, they can use the MPC to limit the fields
they're interested in.

.. code-block:: python

    >>> result = mpc.query_object_async(name="ceres", return_fields="name,number")
    >>> print(result.content)

    [{"name":"Ceres","number":1}]


Reference/API
=============

.. automodapi:: astroquery.mpc
    :no-inheritance-diagram: