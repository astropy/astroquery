.. doctest-skip-all

.. _astroquery.esa.integral:

************************************
esa.integral (`astroquery.esa.integral`)
************************************

INTEGRAL is the INTernational Gamma-Ray Astrophysics Laboratory of the 
European Space Agency. It observes the Universe in the X-ray and soft 
gamma-ray band. Since its launch, on October 17, 2002, the ISDC receives 
the spacecraft telemetry within seconds and provides alerts, processed 
data and analysis software to the worldwide scientific community.

========
Examples
========

--------------
1. Logging in
--------------

.. code-block:: python

  >>> from astroquery.esa.integral import Integral
  >>> Integral.login()

This will enable users to access integral archive data.

--------------
2. Logging out
--------------

.. code-block:: python

  >>> from astroquery.esa.integral import Integral
  >>> Integral.logout()

This will enable users to access integral archive data.

------------------------------------
3. Searching metadata by target name
------------------------------------

.. code-block:: python

  >>> from astroquery.esa.integral import Integral
  >>> crab = Integral.search_target('crab', verbose=False)
  >>> crab

This will download a votable containing all metadata about 'crab'.

-------------------------------------------
4. Searching metadata by different criteria
-------------------------------------------

.. code-block:: python

  >>> from astroquery.esa.integral import Integral
  >>> rev0127 = Integral.search_metadata(revno='0127', verbose=False)
  >>> rev0127

This will retrieve a table with the output of the query.
See https://ila.esac.esa.int/ila/#/pages/search for more information
about the different criteria to be used.

-----------------------------------------
5. Downloading data by different criteria
-----------------------------------------

.. code-block:: python

  >>> from astroquery.esa.integral import Integral
  >>> Integral.data_download(scwid='008100430010,033400230030',filename='scwid_1.tar',verbose=False)
  
This will download the data corresponding to scwid='008100430010,033400230030' and
it will store it in a file named 'scwid_1.tar' in the current directory.

See https://ila.esac.esa.int/ila/#/pages/search for more information
about the different criteria to be used.

---------------------------------------
6. Raw ADQL queries to Integral Archive
---------------------------------------

.. code-block:: python

  >>> result = Integral.query_tap('select top 5 * from ila.scw',verbose=False)
  >>> result

This will perform an ADQL search to the Integral database and will return the output.

Reference/API
=============

.. automodapi:: astroquery.esa.integral
    :no-inheritance-diagram:
