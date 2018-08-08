.. doctest-skip-all

A Gallery of Queries
====================

A series of queries folks have performed for research or for kicks.

Example 1
+++++++++

This illustrates querying Vizier with specific keyword, and the use of
`astropy.coordinates` to describe a query.
Vizier's keywords can indicate wavelength & object type, although only
object type is shown here.

.. include:: gallery-examples/example1_vizier.py
   :code: python


Example 2
+++++++++

This illustrates adding new output fields to SIMBAD queries.
Run `~astroquery.simbad.SimbadClass.list_votable_fields` to get the full list of valid fields.


.. include:: gallery-examples/example2_simbad.py
   :code: python


Example 3
+++++++++

This illustrates finding the spectral type of some particular star.

.. include:: gallery-examples/example3_simbad.py
   :code: python


Example 4
+++++++++


.. include:: gallery-examples/example4_simbad.py
   :code: python



Example 5
+++++++++

This illustrates a simple usage of the open_exoplanet_catalogue module.

Finding the mass of a specific planet:

.. include:: gallery-examples/example5_oec.py
   :code: python


Example 6
+++++++++

Grab some data from ALMA, then analyze it using the Spectral Cube package after
identifying some spectral lines in the data.

.. include:: gallery-examples/example6_alma.py
   :code: python


.. _gallery-almaskyview:

Example 7
+++++++++
Find ALMA pointings that have been observed toward M83, then overplot the
various fields-of view on a 2MASS image retrieved from SkyView.  See
http://nbviewer.jupyter.org/gist/keflavich/19175791176e8d1fb204 for the
notebook.  There is an even more sophisticated version at
http://nbviewer.jupyter.org/gist/keflavich/bb12b772d6668cf9181a, which shows
Orion KL in all observed bands.

.. include:: gallery-examples/example7_alma.py
   :code: python


Example 8
+++++++++

Retrieve data from a particular co-I or PI from the ESO archive

.. include:: gallery-examples/example8_eso.py
   :code: python


Example 9
+++++++++

Retrieve an image from skyview and overlay a Vizier catalog on it.
This example approximately reproduces Figure 1 of 
`2016ApJ...826...16E <http://adsabs.harvard.edu/abs/2016ApJ...826...16E>`_,
except with a different background.


.. include:: gallery-examples/example9_skyview_vizier.py
   :code: python



Example 10
++++++++++
Retrieve Hubble archival data of M83 and make a figure


.. include:: gallery-examples/example10_mast.py
   :code: python

