.. doctest-skip-all

.. _astroquery.nist:

********************************
NIST Queries (`astroquery.nist`)
********************************

Tool to query the NIST Atomic Lines database (http://physics.nist.gov/cgi-bin/ASD/lines1.pl).

Getting started
===============

This is a relatively simple module that you may use to query spectra from
NIST. All the results are returned as a `~astropy.table.Table`. To do this you
just need to specify the lower and the upper wavelength for the spectrum you
want to fetch. These wavelengths must be specified as an appropriate
`~astropy.units.Quantity` object, for instance having units of
nanometer, or angstrom or the like. For example, to use a lower wavelength
value of 4000 Angstroms, you should use ```4000 * u.AA``` and if you want the
same in nanometers, just use ```400 * u.nm```. Of course there are several optional
parameters you can also specify. For instance use the ``linename`` parameter to
specify the spectrum you wish to fetch. By default this is set to "H I", but
you can set it to several other values like "Na;Mg", etc. Lets now see a simple example.

.. code-block:: python

    >>> from astroquery.nist import Nist
    >>> import astropy.units as u
    >>> table = Nist.query(4000 * u.AA, 7000 * u.AA, linename="H I")
    >>> print(table)

        Observed        Ritz      Rel.     Aki     Acc. ...     Lower level         Upper level     Type   TP    Line
     ------------- ------------- ------ ---------- ---- ... ------------------- ------------------- ---- ----- --------
                -- 4102.85985516     --  4287700.0  AAA ...                  --                  --   --    --       --
                -- 4102.86191086     --   245010.0  AAA ... 2p     | 2P*  | 1/2 6s     | 2S   | 1/2   -- T8637       --
                --     4102.8632     --         --   -- ...            |      |            |      |   --    --      c57
     4102.86503481 4102.86503481     --         --   -- ... 2s     | 2S   | 1/2 6d     | 2D   | 5/2   E2    --   L11759
                -- 4102.86579134     --  2858300.0  AAA ...                  --                  --   --    --       --
     4102.86785074 4102.86785074     --         --   -- ... 2s     | 2S   | 1/2 6s     | 2S   | 1/2   M1    --   L11759
                -- 4102.86807252     --  2858400.0  AAA ...                  --                  --   --    --       --
          4102.892     4102.8991  70000   973200.0  AAA ...     2      |      |     6      |      |   -- T8637 L7436c29
                --     4102.8922     --         --   -- ...            |      |            |      |   --    --      c58
                -- 4102.92068748     --  5145000.0  AAA ... 2p     | 2P*  | 3/2 6d     | 2D   | 5/2   -- T8637       --
                --     4102.9208     --         --   -- ...            |      |            |      |   --    --      c59
                -- 4102.92144772     --   857480.0  AAA ...                  --                  --   --    --       --
                -- 4102.92350348     --   490060.0  AAA ... 2p     | 2P*  | 3/2 6s     | 2S   | 1/2   -- T8637       --
                --   4341.647191     --  7854800.0  AAA ... 2p     | 2P*  | 1/2 5d     | 2D   | 3/2   -- T8637       --
                --     4341.6512     --         --   -- ...            |      |            |      |   --    --      c60
               ...           ...    ...        ...  ... ...                 ...                 ...  ...   ...      ...
       6564.522552   6564.522555     -- 53877000.0  AAA ... 2p     | 2P*  | 1/2 3d     | 2D   | 3/2   -- T8637    L2752
                --      6564.527     --         --   -- ...            |      |            |      |   --    --      c67
                --      6564.535     --         --   -- ...            |      |            |      |   --    --      c68
       6564.537684   6564.537684     -- 22448000.0  AAA ... 2s     | 2S   | 1/2 3p     | 2P*  | 3/2   -- T8637 L6891c38
                --   6564.564672     --  2104600.0  AAA ... 2p     | 2P*  | 1/2 3s     | 2S   | 1/2   -- T8637       --
                --   6564.579878     --         --   -- ... 2s     | 2S   | 1/2 3s     | 2S   | 1/2   M1    --       --
                --      6564.583     --         --   -- ...            |      |            |      |   --    --      c66
       6564.584404   6564.584403     -- 22449000.0  AAA ... 2s     | 2S   | 1/2 3p     | 2P*  | 1/2   -- T8637 L6891c38
            6564.6      6564.632 500000 44101000.0  AAA ...     2      |      |     3      |      |   -- T8637 L7400c29
                --      6564.608     --         --   -- ...            |      |            |      |   --    --      c69
        6564.66464    6564.66466     -- 64651000.0  AAA ... 2p     | 2P*  | 3/2 3d     | 2D   | 5/2   -- T8637    L2752
                --     6564.6662     --         --   -- ...            |      |            |      |   --    --      c71
                --      6564.667     --         --   -- ...            |      |            |      |   --    --      c70
                --   6564.680232     -- 10775000.0  AAA ... 2p     | 2P*  | 3/2 3d     | 2D   | 3/2   -- T8637       --
                --   6564.722349     --  4209700.0  AAA ... 2p     | 2P*  | 3/2 3s     | 2S   | 1/2   -- T8637       --


Note that using a different unit will result in different output units in the
``Observed`` and ``Ritz`` columns.

There are several other optional parameters that you may also set. For instance
you may set the ``energy_level_unit`` to any one of these values. ::

    'R' 'Rydberg' 'rydberg' 'cm' 'cm-1' 'EV' 'eV' 'electronvolt' 'ev' 'invcm'

Similarly you can set the ``output_order`` to any one of 'wavelength' or
'multiplet'. A final parameter you may also set is the ``wavelength_type`` to one of 'vacuum'
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
