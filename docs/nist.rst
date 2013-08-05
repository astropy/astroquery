.. _astroquery.nist:

********************************
NIST Queries (`astroquery.nist`)
********************************

Tool to query the NIST Atomic Lines database (http://physics.nist.gov/cgi-bin/ASD/lines1.pl).

Getting started
===============

This is a relatively simple module that you may use to query spectra from
NIST. All the results are returned as an `astropy.table.Table`. To do this you
just need to specify the lower and the upper wavelength for the spectrum you
want to fetch. These wavelengths must be specified as an appropriate
`astropy.units.Quantity` object, for instance having units of
nanometer, or angstrom or the like. Of course there are several optional
parameters you can also specify. For instance use the `linename` parameter to
specify the spectrum you wish to fetch. By default this is set to "H I", but
you can set it to several other values like "Na;Mg", etc. Lets now see a simple example.

.. code-block:: python
                
    >>> from astroquery.nist import Nist
    >>> import astropy.units as u
    >>> table = Nist.query(4000 * u.nm, 7000 * u.nm, linename="H I")
    >>> print table

        Observed     Ritz     Rel.    Aki    ... Type    TP       Line   
    -------- ----------- ----- --------- ... ---- -------- ----------
          --    4020.871 (200)    5526.5 ... over "showBal oon('[',ev
          --  4052.18664    -- 1238100.0 ...   --   <a cla s='bib' ON
          --  4052.19376    --  737160.0 ...   --   <a cla s='bib' ON
          --  4052.22121    --  215030.0 ... over "showBal oon('[',ev
          --  4052.23222    --  737210.0 ...   --   <a cla s='bib' ON
          -- 4052.248747    -- 2412100.0 ... over "showBal oon('T',ev
          --  4052.24892    -- 1485800.0 ... over "showBal oon('[',ev
          --  4052.26147    --   18846.0 ...   --   <a cla s='bib' ON
         ...         ...   ...       ... ...  ...      ...        ...
          --     5525.19 (150)    2470.9 ... over "showBal oon('[',ev
          --    5711.464 (180)    3515.8 ... over "showBal oon('[',ev
          --     5908.22 (540)   70652.0 ...   --   <a cla s='bib' ON
          --    5956.845 (210)    5156.2 ... over "showBal oon('[',ev
          --    6291.918 (250)    7845.7 ... over "showBal oon('[',ev
          --    6771.993 (300)   12503.0 ...   --   <a cla s='bib' ON
          --    6946.756    --    688.58 ... over "showBal oon('[',ev

Reference/API
=============

.. automodapi:: astroquery.nist
    :no-inheritance-diagram:
