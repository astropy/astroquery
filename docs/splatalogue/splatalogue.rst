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
   >>> CO1to0.pprint(max_width=200)
    species_id                                          name                                                     chemical_name             ... searchErrorMessage sqlquery requestnumber
    ---------- -------------------------------------------------------------------------------------- ------------------------------------ ... ------------------ -------- -------------
         21228                                        <i>GA</i>-<i>n</i>-C<sub>4</sub>H<sub>9</sub>CN                      n-Butyl cyanide ...                        None             0
          1288 NH<sub>2</sub>CH<sub>2</sub>CH<sub>2</sub>OH <font color="red">v<sub>26</sub>=1</font>                         Aminoethanol ...                        None             0
           204                                                      CO <font color="red">v = 0</font>                      Carbon Monoxide ...                        None             0
           204                                                      CO <font color="red">v = 0</font>                      Carbon Monoxide ...                        None             0
           204                                                      CO <font color="red">v = 0</font>                      Carbon Monoxide ...                        None             0
           204                                                      CO <font color="red">v = 0</font>                      Carbon Monoxide ...                        None             0
             8                                                                                   FeCO                    Iron Monocarbonyl ...                        None             0
          1321                                                 CH<sub>3</sub>CHNH<sub>2</sub>COOH - I                      &alpha;-Alanine ...                        None             0
         21092                                                                     s-trans-H2C=CHCOOH                       Propenoic acid ...                        None             0
           529                               CH<sub>3</sub>CHO <font color="red">v = 0, 1 & 2 </font>                         Acetaldehyde ...                        None             0
           529                               CH<sub>3</sub>CHO <font color="red">v = 0, 1 & 2 </font>                         Acetaldehyde ...                        None             0
         21067                                                   <i>c</i>-C<sub>5</sub>H<sub>5</sub>N                             Pyridine ...                        None             0
         21067                                                   <i>c</i>-C<sub>5</sub>H<sub>5</sub>N                             Pyridine ...                        None             0
          1275                                                           <i>c</i>-CH<sub>2</sub>CHCHO                             Propenal ...                        None             0
          1275                                                           <i>c</i>-CH<sub>2</sub>CHCHO                             Propenal ...                        None             0
          1288 NH<sub>2</sub>CH<sub>2</sub>CH<sub>2</sub>OH <font color="red">v<sub>26</sub>=1</font>                         Aminoethanol ...                        None             0
          1288 NH<sub>2</sub>CH<sub>2</sub>CH<sub>2</sub>OH <font color="red">v<sub>26</sub>=1</font>                         Aminoethanol ...                        None             0
          1288 NH<sub>2</sub>CH<sub>2</sub>CH<sub>2</sub>OH <font color="red">v<sub>26</sub>=1</font>                         Aminoethanol ...                        None             0
          1288 NH<sub>2</sub>CH<sub>2</sub>CH<sub>2</sub>OH <font color="red">v<sub>26</sub>=1</font>                         Aminoethanol ...                        None             0
          1370                                             CH<sub>3</sub>O<sup>13</sup>CHO (TopModel)                       Methyl Formate ...                        None             0
         21026                                                                   CH3O13CHO, vt = 0, 1 Methyl formate, v<sub>t</sub> = 0, 1 ...                        None             0
          1314                     H<sub>2</sub>NCH<sub>2</sub>COOH - II <font color="red">v=1</font>                              Glycine ...                        None             0
          1284                                   cis-CH<sub>2</sub>OHCHO <font color="red">v=3</font>                       Glycolaldehyde ...                        None             0

Querying just by frequency isn't particularly effective; a nicer approach is to
use both frequency and chemical name.  If you can remember that CO 2-1 is approximately
in the 1 mm band, but you don't know its exact frequency (after all, why else would you be using splatalogue?),
this query works:

.. doctest-remote-data::

   >>> CO2to1 = Splatalogue.query_lines(1*u.mm, 2*u.mm, chemical_name=" CO ")
   >>> CO2to1.pprint(max_width=200)
   species_id                name                chemical_name  resolved_QNs linelist LovasASTIntensity ... telescope_Lovas_NIST transitionBandColor  searchErrorMessage sqlquery requestnumber
    ---------- --------------------------------- --------------- ------------ -------- ----------------- ... -------------------- -------------------- ------------------ -------- -------------
          1343        CO <font color="red">v = 3 Carbon Monoxide         2- 1     CDMS                   ...                      datatablelightpurple                        None             0
           991 CO <font color="red">v = 2</font> Carbon Monoxide         2- 1     CDMS                   ...                      datatablelightpurple                        None             0
           991 CO <font color="red">v = 2</font> Carbon Monoxide         2- 1    SLAIM                   ...                      datatablelightpurple                        None             0
           990 CO <font color="red">v = 1</font> Carbon Monoxide         2- 1     CDMS                   ...                      datatablelightpurple                        None             0
           990 CO <font color="red">v = 1</font> Carbon Monoxide         2- 1    SLAIM           0.62 Jy ...                      datatablelightpurple                        None             0
           204 CO <font color="red">v = 0</font> Carbon Monoxide          2-1     CDMS               70. ...         NRAO     11m datatablelightpurple                        None             0
           204 CO <font color="red">v = 0</font> Carbon Monoxide          2-1      JPL                   ...                      datatablelightpurple                        None             0
           204 CO <font color="red">v = 0</font> Carbon Monoxide          2-1    Lovas               70. ...         NRAO     11m datatablelightpurple                        None             0
           204 CO <font color="red">v = 0</font> Carbon Monoxide         2- 1    SLAIM               70. ...                      datatablelightpurple                        None             0

Of course, there's some noise in there: both the vibrationally excited line and a whole lot of different line lists.
Start by thinning out the line lists used:

.. doctest-remote-data::

   >>> CO2to1 = Splatalogue.query_lines(1*u.mm, 2*u.mm, chemical_name=" CO ", only_NRAO_recommended=True)
   >>> CO2to1.pprint(max_width=200)
    species_id                name                chemical_name  resolved_QNs linelist LovasASTIntensity ... telescope_Lovas_NIST transitionBandColor  searchErrorMessage sqlquery requestnumber
    ---------- --------------------------------- --------------- ------------ -------- ----------------- ... -------------------- -------------------- ------------------ -------- -------------
           990 CO <font color="red">v = 1</font> Carbon Monoxide         2- 1     CDMS                   ...                      datatablelightpurple                        None             0
           204 CO <font color="red">v = 0</font> Carbon Monoxide          2-1     CDMS               70. ...         NRAO     11m datatablelightpurple                        None             0

Then get rid of the vibrationally excited line by setting an energy upper limit in Kelvin:

.. doctest-remote-data::

   >>> CO2to1 = Splatalogue.query_lines(1*u.mm, 2*u.mm, chemical_name=" CO ",
   ...                                  only_NRAO_recommended=True,
   ...                                  energy_max=50, energy_type='eu_k')
   >>> CO2to1.pprint(max_width=200)
   species_id                name                chemical_name  resolved_QNs linelist LovasASTIntensity ... telescope_Lovas_NIST transitionBandColor  searchErrorMessage sqlquery requestnumber
    ---------- --------------------------------- --------------- ------------ -------- ----------------- ... -------------------- -------------------- ------------------ -------- -------------
           204 CO <font color="red">v = 0</font> Carbon Monoxide          2-1     CDMS               70. ...         NRAO     11m datatablelightpurple                        None             0

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
   >>> ha_result.pprint(max_width=200)
    species_id   name          chemical_name           resolved_QNs    linelist LovasASTIntensity ... source_Lovas_NIST telescope_Lovas_NIST transitionBandColor searchErrorMessage sqlquery requestnumber
    ---------- -------- --------------------------- ------------------ -------- ----------------- ... ----------------- -------------------- ------------------- ------------------ -------- -------------
          1154 H&alpha; Hydrogen Recombination Line  H ( 42 ) &alpha;    Recomb                   ...                                           datatableskyblue                        None             0
          1154 H&alpha; Hydrogen Recombination Line  H ( 41 ) &alpha;    Recomb                   ...                                           datatableskyblue                        None             0
          1154 H&alpha; Hydrogen Recombination Line  H ( 40 ) &alpha;    Recomb                   ...                                           datatableskyblue                        None             0
          1154 H&alpha; Hydrogen Recombination Line  H ( 39 ) &alpha;    Recomb                   ...                                           datatableskyblue                        None             0

You could also search by specifying the line list

.. doctest-remote-data::

    >>> recomb_result = Splatalogue.query_lines(84*u.GHz, 85*u.GHz, line_lists=['Recombination'])
    >>> recomb_result.pprint(max_width=200)
    species_id    name          chemical_name            resolved_QNs    linelist LovasASTIntensity ... source_Lovas_NIST telescope_Lovas_NIST transitionBandColor searchErrorMessage sqlquery requestnumber
    ---------- --------- --------------------------- ------------------- -------- ----------------- ... ----------------- -------------------- ------------------- ------------------ -------- -------------
          1156  H&gamma; Hydrogen Recombination Line   H ( 60 ) &gamma;    Recomb                   ...                                           datatableskyblue                        None             0
          1162 He&gamma;   Helium Recombination Line  He ( 60 ) &gamma;    Recomb                   ...                                           datatableskyblue                        None             0
          1166  C&gamma;   Carbon Recombination Line   C ( 60 ) &gamma;    Recomb                   ...                                           datatableskyblue                        None             0

Cleaning Up the Returned Data
-----------------------------

Depending on what sub-field you work in, you may be interested in fine-tuning
splatalogue queries to return only a subset of the columns and lines on a
regular basis.  For example, if you want data returned preferentially in units
of K rather than inverse cm, you're interested in low-energy lines, and you want your
data sorted by energy, you can use an approach like this:

.. doctest-remote-data::

    >>> S = Splatalogue(energy_max=500,
    ...    energy_type='eu_k', energy_levels=['Four'],
    ...    line_strengths=['CDMSJPL'])
    >>> def trimmed_query(*args,**kwargs):
    ...     columns = ('species_id', 'chemical_name', 'name', 'resolved_QNs',
    ...                'orderedfreq',
    ...                'aij',
    ...                'upper_state_energy_K')
    ...     table = S.query_lines(*args, **kwargs)[columns]
    ...     table.sort('upper_state_energy_K')
    ...     return table
    >>> trimmed_query(1*u.GHz,30*u.GHz,
    ...     chemical_name='(H2.*Formaldehyde)|( HDCO )',
    ...     energy_max=50)[:10].pprint(max_width=150)
    species_id chemical_name             name                     resolved_QNs         orderedfreq   aij    upper_state_energy_K
    ---------- ------------- ---------------------------- ---------------------------- ----------- -------- --------------------
           109  Formaldehyde                         HDCO       1(  1, 0)-   1(  1, 1)    5346.142 -8.44112             11.18258
           109  Formaldehyde                         HDCO           1( 1, 0)- 1( 1, 1)   5346.1616 -8.31295             11.18287
           109  Formaldehyde                         HDCO              1(1,0) - 1(1,1)   5346.1416 -8.31616             11.18301
           155  Formaldehyde H<sub>2</sub>C<sup>18</sup>O       1(  1, 0)-   1(  1, 1)    4388.797 -8.22052             15.30187
           155  Formaldehyde H<sub>2</sub>C<sup>18</sup>O  1( 1, 0)- 1( 1, 1), F= 1- 0   4388.7783  -9.0498             15.30206
           155  Formaldehyde H<sub>2</sub>C<sup>18</sup>O  1( 1, 0)- 1( 1, 1), F= 0- 1   4388.7957 -8.57268             15.30206
           155  Formaldehyde H<sub>2</sub>C<sup>18</sup>O  1( 1, 0)- 1( 1, 1), F= 2- 2   4388.7965 -8.69765             15.30206
           155  Formaldehyde H<sub>2</sub>C<sup>18</sup>O              1(1,0) - 1(1,1)    4388.797 -8.57272             15.30206
           155  Formaldehyde H<sub>2</sub>C<sup>18</sup>O  1( 1, 0)- 1( 1, 1), F= 2- 1   4388.8012 -9.17475             15.30206
           155  Formaldehyde H<sub>2</sub>C<sup>18</sup>O  1( 1, 0)- 1( 1, 1), F= 1- 2   4388.8036  -8.9529             15.30206

There are utility functions in ``astroquery.splatalogue.utils`` that automate
some of the above cleanup.

Troubleshooting
===============

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

.. code-block:: python

    >>> from astroquery.splatalogue import Splatalogue
    >>> Splatalogue.clear_cache()

If this function is unavailable, upgrade your version of astroquery.
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.


Reference/API
=============

.. automodapi:: astroquery.splatalogue
    :no-inheritance-diagram:

.. _Splatalogue: https://www.splatalogue.online
.. _Splatalogue web service: https://splatalogue.online/
.. _query interface: https://splatalogue.online/#/basic
