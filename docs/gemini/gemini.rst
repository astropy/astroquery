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


Observation Name Queries
------------------------

You may also do a query by the name of the object you are interested in.

.. code-block:: python

                >>> from astroquery.gemini import Observations

                >>> data = Observations.query_object(objectname='m101')
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

Additional search terms are available as optional arguments to the `~astroquery.gemini.ObservationsClass.query_criteria`
call.  These all have default values of None, in which case they will not be considered during the search.

Some examples of available search fields are the instrument used, such as GMOS-N, the observation_type, such as BIAS,
and the program ID.  For a complete list of available search fields, see
`~astroquery.gemini.ObservationsClass.query_criteria`

.. code-block:: python
                
                >>> from astroquery.gemini import Observations

                >>> data = Observations.query_criteria(instrument='GMOS-N',
                ...                                    program_id='GN-CAL20191122',
                ...                                    observation_type='BIAS')
                >>> print(data[0:5])

                exposure_time detector_roi_setting detector_welldepth_setting  telescope   mdready ...
                ------------- -------------------- -------------------------- ------------ ------- ...
                          0.0        Central Stamp                         -- Gemini-North    True ...
                          0.0           Full Frame                         -- Gemini-North    True ...
                          0.0           Full Frame                         -- Gemini-North    True ...
                          0.0           Full Frame                         -- Gemini-North    True ...
                          0.0           Full Frame                         -- Gemini-North    True ...

In addition, the criteria query can accept additional parameters via the ``*rawqueryargs`` and ``**rawquerykwargs`` 
optional parameters.

The ``orderby`` parameter can be used to pass the desired sort order.

.. code-block:: python

                >>> from astroquery.gemini import Observations

                >>> data = Observations.query_criteria('centralspectrum',
                ...                                    instrument='GMOS-N',
                ...                                    program_id='GN-CAL20191122',
                ...                                    observation_type='BIAS',
                ...                                    filter='r',
                ...                                    orderby='data_label_desc')


Observation Raw Queries
-----------------------

Finally, for ultimate flexibility, a method is provided for driving the "raw" query that is sent to the
webserver.  For this option, no validation is done on the inputs.  That also means this method may allow
for values or even new fields that were not present at the time this module was last updated.

Regular *args* search terms are sent down as part of the URL path.  Any *kwargs* are then sent down with
key=value also in the URL path.  You can infer what to pass the function by inspecting the URL after a search in the
Gemini website.  This call also supports the ``orderby`` kwarg for requesting the sort order.

This example is equivalent to doing a web search with 
`this example search <https://archive.gemini.edu/searchform/RAW/cols=CTOWEQ/notengineering/GMOS-N/PIname=Hirst/NotFail>`_ .
Note that *NotFail*, *notengineering*, *RAW*, and *cols* are all sent automatically.  Only the additional 
terms need be passed into the method.

.. code-block:: python
                
                >>> from astroquery.gemini import Observations

                >>> data = Observations.query_raw('GMOS-N', 'BIAS', progid='GN-CAL20191122')
                >>> print(data[0:5])

                exposure_time detector_roi_setting detector_welldepth_setting  telescope   mdready ...
                ------------- -------------------- -------------------------- ------------ ------- ...
                          0.0        Central Stamp                         -- Gemini-North    True ...
                          0.0           Full Frame                         -- Gemini-North    True ...
                          0.0           Full Frame                         -- Gemini-North    True ...
                          0.0           Full Frame                         -- Gemini-North    True ...
                          0.0           Full Frame                         -- Gemini-North    True ...


Authenticated Sessions
----------------------

The Gemini module allows for authenticated sessions using your GOA account.  This is the same account you login
with on the GOA homepage at `<https://archive.gemini.edu/>`__.  The `astroquery.gemini.ObservationsClass.login` 
method returns `True` if successful.

.. code-block:: python

                >>> from astroquery.gemini import Observations

                >>> Observations.login(username, password)
                >>> # do something with your elevated access


File Downloading
----------------

As a convenience, you can request file downloads directly from the Gemini module.  This constructs the appropriate
URL and fetches the file.  It will use any authenticated session you may have, so it will retrieve any
proprietary data you may be permissioned for.

.. code-block:: python

                >>> from astroquery.gemini import Observations

                >>> Observations.get_file("GS2020AQ319-10.fits", download_dir="/tmp")


Reference/API
=============

.. automodapi:: astroquery.gemini
    :no-inheritance-diagram:

