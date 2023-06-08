.. _astroquery.splatalogue:

**********************************************
Splatalogue Queries (`astroquery.splatalogue`)
**********************************************

Getting Started
===============


This module provides an interface to the `Splatalogue web service`_
It returns tables of spectral lines with features that you can specify by the
same means generally available on the Splatalogue website.


Searching for Lines
-------------------

In the Splatalogue web interface, you select "species" of interest using the left side menu
seen in the `query interface`_.  You can access the line list:

.. code-block:: python

   >>> from astroquery.splatalogue import Splatalogue
   >>> line_ids = Splatalogue.get_species_ids()

This will return the complete Splatalogue chemical species list, including all isotopologues, etc.
To search within this list for a particular species, you can use regular expressions:

.. code-block:: python

   >>> CO_containing_species = Splatalogue.get_species_ids(species_regex='CO')
   >>> len(CO_containing_species)
   105
   >>> just_CO = Splatalogue.get_species_ids(species_regex=' CO ') # note the spaces
   >>> len(just_CO)
   4
   >>> just_CO
   {'02812 CO v = 0 - Carbon Monoxide': '204',
    '02813 CO v = 1 - Carbon Monoxide': '990',
    '02814 CO v = 2 - Carbon Monoxide': '991',
    '02815 CO v = 3 - Carbon Monoxide': '1343'}
   >>> carbon_monoxide = Splatalogue.get_species_ids('Carbon Monoxide')
   >>> len(carbon_monoxide) # includes isotopologues
   17
   >>> carbon_monoxide
   {'02931 13CO+ - Carbon Monoxide Ion': '21107',
    '03027 C18O+ - Carbon Monoxide Ion': '21108',
    '03119 13C18O+ - Carbon Monoxide Ion': '21109',
    '02812 CO v = 0 - Carbon Monoxide': '204',
    '02813 CO v = 1 - Carbon Monoxide': '990',
    '02816 CO+ v = 0 - Carbon Monoxide Ion': '709',
    '02910 13CO v = 0 - Carbon Monoxide': '4',
    '02913 C17O - Carbon Monoxide': '226',
    '03005 C18O - Carbon Monoxide': '245',
    '03006 13C17O - Carbon Monoxide': '264',
    '03101 13C18O - Carbon Monoxide': '14',
    '02814 CO v = 2 - Carbon Monoxide': '991',
    '02815 CO v = 3 - Carbon Monoxide': '1343',
    '02817 CO+ v = 1 - Carbon Monoxide Ion': '21273',
    '02911 13CO v = 1 - Carbon Monoxide': '992',
    '02912 13CO v = 2 - Carbon Monoxide': '993',
    '03004 14CO - Carbon Monoxide': '778'}
   >>> atomic_weight_88 = Splatalogue.get_species_ids('^088')
   >>> atomic_weight_88
   {'08801 SiC5 - Silicon Tetracarbide': '265',
    '08803 C6O - Hexacarbon monoxide': '585',
    '08802 CH3C6H - Methyltriacetylene': '388'}

The returned items are dictionaries, but they are also searchable.

.. code-block:: python

   >>> # note leading space
   >>> carbon_monoxide.find(' 13')
   {'02931 13CO+ - Carbon Monoxide Ion': '21107',
    '03119 13C18O+ - Carbon Monoxide Ion': '21109',
    '02910 13CO v = 0 - Carbon Monoxide': '4',
    '03006 13C17O - Carbon Monoxide': '264',
    '03101 13C18O - Carbon Monoxide': '14',
    '02911 13CO v = 1 - Carbon Monoxide': '992',
    '02912 13CO v = 2 - Carbon Monoxide': '993'}

Querying Splatalogue: Getting Line Information
----------------------------------------------

Unlike most astroquery tools, the Splatalogue_ tool closely resembles the
online interface.  In principle, we can make a higher level wrapper, but it is
not obvious what other parameters one might want to query on (whereas with
catalogs, you almost always need a sky-position based query tool).

Any feature you can change on the `Splatalogue web form <query interface_>`_
can be modified in the
:meth:`~astroquery.splatalogue.SplatalogueClass.query_lines` tool.

For any Splatalogue query, you *must* specify a minimum/maximum frequency.
However, you can do it with astropy units, so wavelengths are OK too.

(note that in the following examples, ``max_width=100`` is set to minimize the
size of the printout and assist with doctests; it is not needed as the default
``pprint`` behavior is to fill the terminal width)

.. doctest-remote-data::

   >>> from astropy import units as u
   >>> CO1to0 = Splatalogue.query_lines(115.271*u.GHz, 115.273*u.GHz)
   >>> CO1to0.pprint(max_width=100)
          Species                  Chemical Name             ...  E_U (K)   Linelist
    ------------------- ------------------------------------ ... ---------- --------
            GA-n-C4H9CN                      n-Butyl cyanide ...  332.23706     CDMS
       NH2CH2CH2OHv26=1                         Aminoethanol ...  390.35352      JPL
                  COv=0                      Carbon Monoxide ...    5.53211     CDMS
                  COv=0                      Carbon Monoxide ...    5.53211      JPL
                  COv=0                      Carbon Monoxide ...        0.0    Lovas
                  COv=0                      Carbon Monoxide ...    5.53211    SLAIM
                   FeCO                    Iron Monocarbonyl ...  103.95656     CDMS
         CH3CHNH2COOH-I                      &alpha;-Alanine ...  129.92964     CDMS
     s-trans-H2C=CHCOOH                       Propenoic acid ...   18.49667     CDMS
          CH3CHOv=0,1&2                         Acetaldehyde ...  223.65667    SLAIM
          CH3CHOv=0,1&2                         Acetaldehyde ...   223.6558      JPL
                c-C5H5N                             Pyridine ...  230.47644     CDMS
                c-C5H5N                             Pyridine ...  230.47644     CDMS
             c-CH2CHCHO                             Propenal ... 1266.35462      JPL
             c-CH2CHCHO                             Propenal ... 1266.35462      JPL
       NH2CH2CH2OHv26=1                         Aminoethanol ...  766.11681      JPL
       NH2CH2CH2OHv26=1                         Aminoethanol ...  766.11681      JPL
       NH2CH2CH2OHv26=1                         Aminoethanol ...  766.11681      JPL
       NH2CH2CH2OHv26=1                         Aminoethanol ...  766.11681      JPL
    CH3O13CHO(TopModel)                       Methyl Formate ...  272.75041 TopModel
       CH3O13CHO,vt=0,1 Methyl formate, v<sub>t</sub> = 0, 1 ...  272.75358     CDMS
       H2NCH2COOH-IIv=1                              Glycine ...  2355.1427      JPL
        cis-CH2OHCHOv=3                       Glycolaldehyde ...  887.56625      JPL

Querying just by frequency isn't particularly effective; a nicer approach is to
use both frequency and chemical name.  If you can remember that CO 2-1 is approximately
in the 1 mm band, but you don't know its exact frequency (after all, why else would you be using splatalogue?),
this query works:

.. doctest-remote-data::

   >>> CO2to1 = Splatalogue.query_lines(1*u.mm, 2*u.mm, chemical_name=" CO ")
   >>> CO2to1.pprint(max_width=100)
   Species  Chemical Name  Freq-GHz(rest frame,redshifted) ... E_U (cm^-1)  E_U (K)   Linelist
   ------- --------------- ------------------------------- ... ----------- ---------- --------
     COv=3 Carbon Monoxide                     224.2417699 ...    6361.659  9152.9556     CDMS
     COv=2 Carbon Monoxide                              -- ...   4271.3871  6145.5379     CDMS
     COv=2 Carbon Monoxide                      226.340357 ...   4271.3869 6145.53761    SLAIM
     COv=1 Carbon Monoxide                              -- ...  2154.70101 3100.11628     CDMS
     COv=1 Carbon Monoxide                       228.43911 ...  2154.70191 3100.11758    SLAIM
     COv=0 Carbon Monoxide                              -- ...    11.53492   16.59608     CDMS
     COv=0 Carbon Monoxide                              -- ...    11.53492   16.59608      JPL
     COv=0 Carbon Monoxide                         230.538 ...         0.0        0.0    Lovas
     COv=0 Carbon Monoxide                         230.538 ...    11.53492   16.59608    SLAIM

Of course, there's some noise in there: both the vibrationally excited line and a whole lot of different line lists.
Start by thinning out the line lists used:

.. doctest-remote-data::

   >>> CO2to1 = Splatalogue.query_lines(1*u.mm, 2*u.mm, chemical_name=" CO ",only_NRAO_recommended=True)
   >>> CO2to1.pprint(max_width=100)
   Species  Chemical Name  Freq-GHz(rest frame,redshifted) ... E_U (cm^-1)  E_U (K)   Linelist
    ------- --------------- ------------------------------- ... ----------- ---------- --------
      COv=1 Carbon Monoxide                              -- ...  2154.70101 3100.11628     CDMS
      COv=0 Carbon Monoxide                              -- ...    11.53492   16.59608     CDMS

Then get rid of the vibrationally excited line by setting an energy upper limit in Kelvin:

.. doctest-remote-data::

   >>> CO2to1 = Splatalogue.query_lines(1*u.mm, 2*u.mm, chemical_name=" CO ",
   ...                                  only_NRAO_recommended=True,
   ...                                  energy_max=50, energy_type='eu_k')
   >>> CO2to1.pprint(max_width=100)
   Species  Chemical Name  Freq-GHz(rest frame,redshifted) ... E_U (cm^-1) E_U (K)  Linelist
   ------- --------------- ------------------------------- ... ----------- -------- --------
     COv=0 Carbon Monoxide                              -- ...    11.53492 16.59608     CDMS

A note on recombination lines
-----------------------------

Radio recombination lines are included in the splatalogue catalog under the
names "Hydrogen Recombination Line", "Helium Recombination Line", and "Carbon
Recombination Line".  If you want to search specifically for the alpha, beta,
delta, gamma, epsilon, or zeta lines, you need to use the unicode character for
these symbols (Hα, Hβ, Hγ, Hδ, Hε, Hζ), even though they will show up as
``&alpha;`` in the ASCII table.  For example:

.. doctest-remote-data::

   >>> ha_result = Splatalogue.query_lines(84*u.GHz, 115*u.GHz, chemical_name='Hα')
   >>> ha_result.pprint(max_width=100)
   Species         Chemical Name        Freq-GHz(rest frame,redshifted) ... E_U (K) Linelist
   -------- --------------------------- ------------------------------- ... ------- --------
   H&alpha; Hydrogen Recombination Line                        85.68839 ...     0.0   Recomb
   H&alpha; Hydrogen Recombination Line                       92.034434 ...     0.0   Recomb
   H&alpha; Hydrogen Recombination Line                       99.022952 ...     0.0   Recomb
   H&alpha; Hydrogen Recombination Line                      106.737357 ...     0.0   Recomb

You could also search by specifying the line list

.. doctest-remote-data::

    >>> recomb_result = Splatalogue.query_lines(84*u.GHz, 85*u.GHz, line_lists=['Recomb'])
    >>> recomb_result.pprint(max_width=100)
     Species         Chemical Name        Freq-GHz(rest frame,redshifted) ... E_U (K) Linelist
    --------- --------------------------- ------------------------------- ... ------- --------
     H&gamma; Hydrogen Recombination Line                       84.914394 ...     0.0   Recomb
    He&gamma;   Helium Recombination Line                       84.948997 ...     0.0   Recomb
     C&gamma;   Carbon Recombination Line                       84.956762 ...     0.0   Recomb

Cleaning Up the Returned Data
-----------------------------

Depending on what sub-field you work in, you may be interested in fine-tuning
splatalogue queries to return only a subset of the columns and lines on a
regular basis.  For example, if you want data returned preferentially in units
of K rather than inverse cm, you're interested in low-energy lines, and you want your
data sorted by energy, you can use an approach like this:

(note that as of March 2023, there is an upstream error in which the ``noHFS`` keyword
is not respected; we include it here as a demonstration in the hope that that error will
be fixed)

.. doctest-remote-data::

    >>> S = Splatalogue(energy_max=500,
    ...    energy_type='eu_k',energy_levels=['el4'],
    ...    line_strengths=['ls4'],
    ...    only_NRAO_recommended=True,
    ...    noHFS=True,
    ...    displayHFS=False)
    >>> def trimmed_query(*args,**kwargs):
    ...     columns = ('Species','Chemical Name','Resolved QNs',
    ...                'Freq-GHz(rest frame,redshifted)',
    ...                'Meas Freq-GHz(rest frame,redshifted)',
    ...                'Log<sub>10</sub> (A<sub>ij</sub>)',
    ...                'E_U (K)')
    ...     table = S.query_lines(*args, **kwargs)[columns]
    ...     table.rename_column('Log<sub>10</sub> (A<sub>ij</sub>)','log10(Aij)')
    ...     table.rename_column('E_U (K)','EU_K')
    ...     table.rename_column('Resolved QNs','QNs')
    ...     table.rename_column('Freq-GHz(rest frame,redshifted)', 'Freq-GHz'),
    ...     table.rename_column('Meas Freq-GHz(rest frame,redshifted)', 'Meas Freq-GHz'),
    ...     table.sort('EU_K')
    ...     return table
    >>> trimmed_query(1*u.GHz,30*u.GHz,
    ...     chemical_name='(H2.*Formaldehyde)|( HDCO )',
    ...     energy_max=50)[:10].pprint(max_width=100)
    Species Chemical Name         QNs          Freq-GHz Meas Freq-GHz log10(Aij)   EU_K
    ------- ------------- ------------------- --------- ------------- ---------- --------
       HDCO  Formaldehyde       1(1,0)-1(1,1)        --     5.3461416   -8.31616 11.18301
     H2C18O  Formaldehyde 1(1,0)-1(1,1),F=1-0 4.3887783            --    -9.0498 15.30206
     H2C18O  Formaldehyde 1(1,0)-1(1,1),F=0-1 4.3887957            --   -8.57268 15.30206
     H2C18O  Formaldehyde 1(1,0)-1(1,1),F=2-2 4.3887965            --   -8.69765 15.30206
     H2C18O  Formaldehyde       1(1,0)-1(1,1)  4.388797            --   -8.57272 15.30206
     H2C18O  Formaldehyde 1(1,0)-1(1,1),F=2-1 4.3888012            --   -9.17475 15.30206
     H2C18O  Formaldehyde 1(1,0)-1(1,1),F=1-2 4.3888036            --    -8.9529 15.30206
     H2C18O  Formaldehyde 1(1,0)-1(1,1),F=1-1 4.3888083            --    -9.1748 15.30206
     H213CO  Formaldehyde       1(1,0)-1(1,1)        --     4.5930885   -8.51332 15.34693
       H2CO  Formaldehyde 1(1,0)-1(1,1),F=1-2 4.8296665            --   -8.82819 15.39497


Reference/API
=============

.. automodapi:: astroquery.splatalogue
    :no-inheritance-diagram:

.. _Splatalogue: https://www.splatalogue.online
.. _Splatalogue web service: https://splatalogue.online/
.. _query interface: https://splatalogue.online//b.php
