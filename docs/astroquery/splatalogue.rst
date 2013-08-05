.. _astroquery.splatalogue:

**********************************************
Splatalogue Queries (`astroquery.splatalogue`)
**********************************************

Getting Started
===============


This module provides an interface to the `Splatalogue web service <Splatalogue>`_
It returns tables of spectral lines with features that you can specify by the
same means generally available on the Splatalogue website.  

Searching for Lines
~~~~~~~~~~~~~~~~~~~

In the Splatalogue web interface, you select "species" of interest using the left side menu
seen in the `query interface <splat_b>`_  You can access the line list:

.. code-block:: python

   >>> from astroquery.splatalogue import Splatalogue
   >>> line_ids = Splatalogue.get_species_ids()

This will return the complete Splatalogue chemical species list, including all isotopologues, etc.
To search within this list for a particular species, you can use regular expressions:

.. code-block:: python

   >>> CO_containing_species = Splatalogue.get_species_ids('CO')
   >>> len(CO_containing_species)
   91
   >>> just_CO = Splatalogue.get_species_ids(' CO ') # note the spaces
   >>> len(just_CO)
   4
   >>> just_CO  # includes different vibrationally excited states
   {u'02812 CO v = 0 - Carbon Monoxide': u'204',
    u'02813 CO v = 1 - Carbon Monoxide': u'990',
    u'02814 CO v = 2 - Carbon Monoxide': u'991',
    u'02815 CO v = 3 - Carbon Monoxide': u'1343'}
   >>> carbon_monoxide = Splatalogue.get_species_ids('Carbon Monoxide')
   >>> len(carbon_monoxide) # includes isotopologues
   13
   >>> carbon_monoxide
   >>>
   {u'02812 CO v = 0 - Carbon Monoxide': u'204',
    u'02813 CO v = 1 - Carbon Monoxide': u'990',
    u'02814 CO v = 2 - Carbon Monoxide': u'991',
    u'02815 CO v = 3 - Carbon Monoxide': u'1343',
    u'02816 CO+ - Carbon Monoxide Ion': u'709',
    u'02910 13CO v = 0 - Carbon Monoxide': u'4',
    u'02911 13CO v = 1 - Carbon Monoxide': u'992',
    u'02912 13CO v = 2 - Carbon Monoxide': u'993',
    u'02913 C17O - Carbon Monoxide': u'226',
    u'03004 14CO - Carbon Monoxide': u'778',
    u'03005 C18O - Carbon Monoxide': u'245',
    u'03006 13C17O - Carbon Monoxide': u'264',
    u'03101 13C18O - Carbon Monoxide': u'14'}
   >>> atomic_weight_88 = Splatalogue.get_species_ids('^088')
   >>> atomic_weight_88
   {u'08801 SiC5 - ': u'265',
    u'08802 CH3C6H - Methyltriacetylene': u'388',
    u'08803 C6O - Hexacarbon monoxide': u'585'}   

The returned items are dictionaries, but they are also searchable.  

.. code-block:: python

   >>> carbon_monoxide.find(' 13')  # note leading space
   {u'02910 13CO v = 0 - Carbon Monoxide': u'4',
    u'02911 13CO v = 1 - Carbon Monoxide': u'992',
    u'02912 13CO v = 2 - Carbon Monoxide': u'993',
    u'03006 13C17O - Carbon Monoxide': u'264',
    u'03101 13C18O - Carbon Monoxide': u'14'}

Querying Splatalogue: Getting Line Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unlike most astroquery tools, the Splatalogue_ tool closely resembles the
online interface.  In principle, we can make a higher level wrapper, but it is
not obvious what other parameters one might want to query on (whereas with
catalogs, you almost always need a sky-position based query tool).

Any feature you can change on the `Splatalogue web form <splat_b>`_ can be
modified in the :func:`~Splatalogue.query_lines` tool.

For any Splatalogue query, you *must* specify a minimum/maximum frequency.
However, you can do it with astropy units, so wavelengths are OK too.

.. code-block:: python

   >>> from astropy import units as u
   >>> CO1to0 = Splatalogue.query_lines(115.271*u.GHz,115.273*u.GHz)
   >>> CO1to0.pprint()
         Species        Chemical Name   Freq-GHz ... E<sub>U</sub> (K) Linelist
   ------------------- --------------- --------- ... ----------------- --------
                 COv=0 Carbon Monoxide        -- ...           5.53211     CDMS
                 COv=0 Carbon Monoxide        -- ...           5.53211      JPL
                 COv=0 Carbon Monoxide  115.2712 ...               0.0    Lovas
                 COv=0 Carbon Monoxide  115.2712 ...           5.53211    SLAIM
            CH3CHOvt=1    Acetaldehyde 115.27182 ...         223.65667    SLAIM
            CH3CHOvt=1    Acetaldehyde        -- ...         223.65581      JPL
   CH3O13CHO(TopModel)  Methyl Formate  115.2728 ...         272.75041 TopModel

Querying just by frequency isn't particularly effective; a nicer approach is to
use both frequency and chemical name.  If you can remember that CO 2-1 is approximately
in the 1 mm band, but you don't know its exact frequency (after all, why else would you be using splatalogue?),
this query works:

.. code-block:: python

   >>> CO2to1 = Splatalogue.query_lines(1*u.mm, 2*u.mm, chemical_name=" CO ")
   >>> CO2to1.pprint()
   Species  Chemical Name   Freq-GHz ... E<sub>U</sub> (K) Linelist
   ------- --------------- --------- ... ----------------- --------
     COv=1 Carbon Monoxide        -- ...        3100.11628     CDMS
     COv=1 Carbon Monoxide 228.43911 ...        3100.11758    SLAIM
     COv=0 Carbon Monoxide        -- ...          16.59608     CDMS
     COv=0 Carbon Monoxide        -- ...          16.59608      JPL
     COv=0 Carbon Monoxide   230.538 ...               0.0    Lovas
     COv=0 Carbon Monoxide   230.538 ...          16.59608    SLAIM
   
Of course, there's some noise in there: both the vibrationally excited line and a whole lot of different line lists.
Start by thinning out the line lists used:

.. code-block:: python

    >>> CO2to1 = Splatalogue.query_lines(1*u.mm, 2*u.mm, chemical_name=" CO ",only_NRAO_recommended=True)
    >>> CO2to1.pprint()Species  Chemical Name   Freq-GHz ... E<sub>U</sub> (K) Linelist
    ------- --------------- --------- ... ----------------- --------
      COv=1 Carbon Monoxide 228.43911 ...        3100.11758    SLAIM
      COv=0 Carbon Monoxide   230.538 ...          16.59608    SLAIM

Then get rid of the vibrationally excited line by setting an energy upper limit in Kelvin:

.. code-block:: python

    >>> CO2to1 = Splatalogue.query_lines(1*u.mm, 2*u.mm, chemical_name=" CO ",
                                         only_NRAO_recommended=True,
                                         energy_max=50, energy_type='eu_k')
    >>> CO2to1.pprint()Species  Chemical Name  Freq-GHz ... E<sub>U</sub> (K) Linelist
    ------- --------------- -------- ... ----------------- --------
      COv=0 Carbon Monoxide  230.538 ...          16.59608    SLAIM
   

.. _Splatalogue: http://www.splatalogue.net
.. _splat_b: www.cv.nrao.edu/php/splat/b.php


