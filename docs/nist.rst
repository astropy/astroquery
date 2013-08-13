.. _astroquery.nist:

********************************
NIST Queries (`astroquery.nist`)
********************************

Tool to query the NIST Atomic Lines database (http://physics.nist.gov/cgi-bin/ASD/lines1.pl).

Getting started
===============

This is a relatively simple module that you may use to query spectra from
NIST. All the results are returned as an `astropy.table.Table`_. To do this you
just need to specify the lower and the upper wavelength for the spectrum you
want to fetch. These wavelengths must be specified as an appropriate
`astropy.units`_ `Quantity` object, for instance having units of
nanometer, or angstrom or the like. Of course there are several optional
parameters you can also specify. For instance use the `linename` parameter to
specify the spectrum you wish to fetch. By default this is set to "H I", but
you can set it to several other values like "Na;Mg", etc. Lets now see a simple example.

.. code-block:: python
                
    >>> from astroquery.nist import Nist
    >>> import astropy.units as u
    >>> table = Nist.query(4000 * u.nm, 7000 * u.nm, linename="H I")
    >>> print(table)
    
    Observed     Ritz     Rel.    Aki    ...     Upper level     Type   TP  Line
    -------- ----------- ----- --------- ... ------------------- ---- ----- ----
          --    4020.871 (200)    5526.5 ...                  --   --    --   --
          --  4052.18664    -- 1238100.0 ... 5d     | 2D   | 3/2   -- T8637   --
          --  4052.19376    --  737160.0 ... 5p     | 2P*  | 3/2   -- T8637   --
          --  4052.22121    --  215030.0 ...                  --   --    --   --
          --  4052.23222    --  737210.0 ... 5p     | 2P*  | 1/2   -- T8637   --
          -- 4052.248747    -- 2412100.0 ...                  --   --    --   --
          --  4052.24892    -- 1485800.0 ...                  --   --    --   --
          --  4052.26147    --   18846.0 ... 5p     | 2P*  | 3/2   -- T8637   --
         ...         ...   ...       ... ...                 ...  ...   ...  ...
          --     5525.19 (150)    2470.9 ...                  --   --    --   --
          --    5711.464 (180)    3515.8 ...                  --   --    --   --
          --     5908.22 (540)   70652.0 ...     9      |      |   -- T8637   --
          --    5956.845 (210)    5156.2 ...                  --   --    --   --
          --    6291.918 (250)    7845.7 ...                  --   --    --   --
          --    6771.993 (300)   12503.0 ...     12     |      |   -- T8637   --
          --    6946.756    --    688.58 ...                  --   --    --   --


There are several other optional parameters that you may also set. For instance
you may set the `energy_level_unit` to any one of these values. ::

    'R' 'Rydberg' 'rydberg' 'cm' 'cm-1' 'EV' 'eV' 'electronvolt' 'ev' 'invcm'

Similarly you can set the `output_order` to any one of 'wavelength' or
'multiplet'. A final parameter you may also set is the `wavelength_type` to one of 'vacuum'
or 'vac+air'. Here is an example with all these parameters.

.. code-block:: python
 
    >>> from astroquery.nist import Nist
    >>> table = Nist.query(4000 * u.nm, 7000 * u.nm, 'H I',
    ...                    energy_level_unit='eV', output_order='wavelength',
    ...                    wavelength_type='vacuum')
    >>> print(table)

        Observed     Ritz     Rel.    Aki    ...     Upper level     Type   TP  Line
    -------- ----------- ----- --------- ... ------------------- ---- ----- ----
          --    4020.871 (200)    5526.5 ...                  --   --    --   --
          --  4052.18664    -- 1238100.0 ... 5d     | 2D   | 3/2   -- T8637   --
          --  4052.19376    --  737160.0 ... 5p     | 2P*  | 3/2   -- T8637   --
          --  4052.22121    --  215030.0 ...                  --   --    --   --
          --  4052.23222    --  737210.0 ... 5p     | 2P*  | 1/2   -- T8637   --
          -- 4052.248747    -- 2412100.0 ...                  --   --    --   --
          --  4052.24892    -- 1485800.0 ...                  --   --    --   --
          --  4052.26147    --   18846.0 ... 5p     | 2P*  | 3/2   -- T8637   --
         ...         ...   ...       ... ...                 ...  ...   ...  ...
          --     5525.19 (150)    2470.9 ...                  --   --    --   --
          --    5711.464 (180)    3515.8 ...                  --   --    --   --
          --     5908.22 (540)   70652.0 ...     9      |      |   -- T8637   --
          --    5956.845 (210)    5156.2 ...                  --   --    --   --
          --    6291.918 (250)    7845.7 ...                  --   --    --   --
          --    6771.993 (300)   12503.0 ...     12     |      |   -- T8637   --
          --    6946.756    --    688.58 ...                  --   --    --   --


              
    
Reference/API
=============

.. automodapi:: astroquery.nist
    :no-inheritance-diagram:

.. _astropy.table.Table: http://docs.astropy.org/en/latest/table/index.html
.. _astropy.units: http://docs.astropy.org/en/latest/units/index.html 
