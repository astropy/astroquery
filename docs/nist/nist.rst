.. _astroquery.nist:

********************************
NIST Queries (`astroquery.nist`)
********************************

Tool to query the NIST Atomic Lines database (https://physics.nist.gov/PhysRefData/ASD/lines_form.html).

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

.. doctest-remote-data::

    >>> from astroquery.nist import Nist
    >>> import astropy.units as u
    >>> table = Nist.query(4000 * u.AA, 7000 * u.AA, linename="H I")
    >>> print(table)
       Observed        Ritz       Transition   Rel.  ... Type   TP    Line
    ------------- ------------- ------------- ------ ... ---- ----- --------
               -- 4102.85985517 24373.2429403     -- ...   -- T8637       --
               -- 4102.86191087 24373.2307283     -- ...   -- T8637       --
               --     4102.8632     24373.223     -- ...   --    --      c57
    4102.86503481 4102.86503481 24373.2121704     -- ...   E2    --   L11759
               -- 4102.86579132 24373.2076763     -- ...   -- T8637       --
    4102.86785074 4102.86785074 24373.1954423     -- ...   M1    --   L11759
               --  4102.8680725 24373.1941249     -- ...   -- T8637       --
         4102.892     4102.8991      24373.05  70000 ...   -- T8637 L7436c29
               --     4102.8922     24373.051     -- ...   --    --      c58
               -- 4102.92068748 24372.8815683     -- ...   -- T8637       --
              ...           ...           ...    ... ...  ...   ...      ...
               --   6564.564672  15233.302588     -- ...   -- T8637       --
               --   6564.579878  15233.267302     -- ...   M1    --       --
               --      6564.583      15233.26     -- ...   --    --      c66
      6564.584404   6564.584403  15233.256799     -- ...   -- T8637 L6891c38
           6564.6      6564.632      15233.21 500000 ...   -- T8637 L7400c29
               --      6564.608     15233.202     -- ...   --    --      c69
       6564.66464    6564.66466   15233.07061     -- ...   -- T8637    L2752
               --     6564.6662     15233.067     -- ...   --    --      c71
               --      6564.667     15233.065     -- ...   --    --      c70
               --   6564.680232  15233.034432     -- ...   -- T8637       --
               --   6564.722349    15232.9367     -- ...   -- T8637       --
    Length = 53 rows


Note that using a different unit will result in different output units in the
``Observed`` and ``Ritz`` columns.

There are several other optional parameters that you may also set. For instance
you may set the ``energy_level_unit`` to any one of these values. ::

    'R' 'Rydberg' 'rydberg' 'cm' 'cm-1' 'EV' 'eV' 'electronvolt' 'ev' 'invcm'

Similarly you can set the ``output_order`` to any one of 'wavelength' or
'multiplet'. A final parameter you may also set is the ``wavelength_type`` to one of 'vacuum'
or 'vac+air'. Here is an example with all these parameters.

.. doctest-remote-data::

    >>> from astroquery.nist import Nist
    >>> table = Nist.query(4000 * u.nm, 7000 * u.nm, 'H I',
    ...                    energy_level_unit='eV', output_order='wavelength',
    ...                    wavelength_type='vacuum')
    >>> print(table)
    Observed     Ritz     Transition  Rel. ...     Upper level     Type   TP   Line
    -------- ----------- ----------- ----- ... ------------------- ---- ----- -----
          --    4020.871    2487.024 (200) ...     14     |      |   -- T8637    --
          --  4052.18664 2467.803411    -- ... 5d     | 2D   | 3/2   -- T8637    --
          --  4052.19376  2467.79907    -- ... 5p     | 2P*  | 3/2   -- T8637    --
          --  4052.22121  2467.78236    -- ... 5s     | 2S   | 1/2   -- T8637    --
          --  4052.23222  2467.77565    -- ... 5p     | 2P*  | 1/2   -- T8637    --
          -- 4052.248747 2467.765585    -- ... 5f     | 2F*  | 5/2   -- T8637    --
          --  4052.24892 2467.765479    -- ... 5d     | 2D   | 5/2   -- T8637    --
          --  4052.26147  2467.75784    -- ... 5p     | 2P*  | 3/2   -- T8637    --
          --  4052.26174 2467.757676    -- ... 5d     | 2D   | 3/2   -- T8637    --
          --  4052.26738  2467.75424    -- ... 5g     | 2G   | 7/2   -- T8637    --
         ...         ...         ...   ... ...                 ...  ...   ...   ...
     5128.65    5128.662     1949.83 (450) ...     10     |      |   -- T8637 L7452
          --    5169.282   1934.5047    -- ...     19     |      |   -- T8637    --
          --    5263.685   1899.8096    -- ...     18     |      |   -- T8637    --
          --    5379.776   1858.8134    -- ...     17     |      |   -- T8637    --
          --     5525.19   1809.8925 (150) ...     16     |      |   -- T8637    --
          --    5711.464   1750.8646 (180) ...     15     |      |   -- T8637    --
          --     5908.22   1692.5572 (540) ...     9      |      |   -- T8637    --
          --    5956.845   1678.7409 (210) ...     14     |      |   -- T8637    --
          --    6291.918   1589.3405 (250) ...     13     |      |   -- T8637    --
          --    6771.993   1476.6701 (300) ...     12     |      |   -- T8637    --
          --    6946.756   1439.5208    -- ...     20     |      |   -- T8637    --
    Length = 37 rows

Reference/API
=============

.. automodapi:: astroquery.nist
    :no-inheritance-diagram:
