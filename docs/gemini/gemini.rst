.. doctest-skip-all

.. _astroquery.gemini:

************************************
Gemini Queries (`astroquery.gemini`)
************************************

Getting Started
===============

This module can be used to query the Gemini Archive. Below are examples of querying the data with various
parameters.

Positional Queries
------------------

Positional queries can be based on a sky position.  Radius is an optional parameter and the default is 0.3 degrees.

.. code-block:: python

                >>> from astroquery.gemini import Observations
                >>> from astropy import coordinates, units

                >>> coord = coordinates.SkyCoord(210.80242917, 54.34875, unit="deg")
                >>> data = Observations.query_region(coordinates=coord, radius=0.3*units.deg)
                >>> print(data[0:5])
                
                exposure_time detector_roi_setting detector_welldepth_setting  telescope   ...
                ------------- -------------------- -------------------------- ------------ ...
                     119.9986           Full Frame                         -- Gemini-North ...
                     119.9983           Full Frame                         -- Gemini-North ...
                     119.9986           Full Frame                         -- Gemini-North ...
                     119.9983           Full Frame                         -- Gemini-North ...
                      99.9983           Full Frame                         -- Gemini-North ...


Observation Criteria Queries
----------------------------

Additional search terms are available as optional arguments to the `~astroquery.gemini.ObservationsClass.query_region`
call.  These all have default values of None, in which case they will not be considered during the search.

The full API is provided below, but some examples are the instrument used via instrument, the
observation_type, such as BIAS, and the program ID via program_id.

.. code-block:: python
                
                >>> from astroquery.gemini import Observations
                >>> from astropy import coordinates, units

                >>> data = Observations.query_region(instrument='GMOS-N',
                ...                                  program_id='GN-CAL20191122',
                ...                                  observation_type='BIAS')
                >>> print(data[0:5])

                exposure_time detector_roi_setting detector_welldepth_setting  telescope   mdready ...
                ------------- -------------------- -------------------------- ------------ ------- ...
                          0.0        Central Stamp                         -- Gemini-North    True ...
                          0.0           Full Frame                         -- Gemini-North    True ...
                          0.0           Full Frame                         -- Gemini-North    True ...
                          0.0           Full Frame                         -- Gemini-North    True ...
                          0.0           Full Frame                         -- Gemini-North    True ...


Reference/API
=============

.. automodapi:: astroquery.gemini
    :no-inheritance-diagram:

