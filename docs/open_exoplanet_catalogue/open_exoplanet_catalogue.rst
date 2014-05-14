.. _astroquery.simbad:

***************************************************************
Open Exoplanet Catalogue(`astorquery.open_exoplanet_catalogue`)
***************************************************************

Getting started
===============

This module gives easy access to the open exoplanet catalogue in the form of an XML element tree. 

To start import the catalog and generate the catalogue.

.. code-block:: python

        from astroquery import open_exoplanet_catalogue as oec

        cata = oec.get_catalogue()

The source of the catalogue can be changed from remote to local, and vice versa.

.. code-block:: python

        oec.change_to_local("path/to/catalogue/systems.xml.gz")

        oec.change_to_remote()


Examples
========

First import the module and generate the catalogue.

.. code-block:: python

        from astroquery import open_exoplanet_catalogue as oec

        cata = oec.get_catalogue()

Prints all planets and their masses.

.. code-block:: python

    for planet in cata.findall(".//planet"):
        print planet.findtext('name'), planet.findvalue('mass')

Prints all of the planets with known mass around stars of known mass in a machine readable format.

.. code-block:: python

    for star in cata.findall(".//star[mass]"):
        for planet in star.findall("./planet[mass]"):
            print planet.findvalue('mass').machine_readable(),star.findvalue('mass').machine_readable()

Print all the names of stars in binaries.
         
.. code-block:: python

    for star in cata.findall(".//binary/star"):
        print star.findtext('name')

Prints all the planet names and period of planets around binaries

.. code-block:: python

    for planet in cata.findall(".//binary/planet"):
        print planet.findtext('name'), planet.findvalue('period')

Prints the name, radius and mass of the planet Kepler-68 b. 

.. code-block:: python

    for planet in cata.findall(".//planet[name='Kepler-68 b']"):
        print planet.findtext('name'), planet.findvalue('radius'), planet.findvalue('mass')

Prints the name and radius of planets with a radius greater than 1 jupiter radius.

.. code-block:: python

    for planet in cata.findall(".//planet[radius]"):
        if planet.findvalue('radius') > 1:
            print planet.findtext('name'), planet.findvalue('radius')

Prints the names of the planets around a single star in a binary.

.. code-block:: python

    for binary in cata.findall(".//binary/star/planet"):
        print binary.findtext('name')

Prints a ratio of star and planet mass.

.. code-block:: python

    for star in cata.findall(".//star[mass]/planet[mass].."):
        if star.findvalue('mass') != None:
            for planet in star.findall(".//planet"):
                if planet.findvalue('mass') != None:
                    print star.findtext('name'),planet.findtext('name'), "Ratio:", star.findvalue('mass')/planet.findvalue('mass')

Prints planets whose mass has an upper limit

.. code-block:: python

    for planet in cata.findall(".//planet/mass[@upperlimit].."):
        print planet.findtext('name'), planet.findvalue('mass')

   
Prints all stars with the number of planets orbiting them

.. code-block:: python

    for star in cata.findall(".//star[planet]"):
        print star.findtext('name'), len(star.findall(".//planet"))

Prints all the properties of Kepler-20 b.

.. code-block:: python

    for properties in cata.findall(".//planet[name='Kepler-20 b']/*"):
        print "\t" + properties.tag + ":", properties.text
   
Prints the right ascension and declination of systems with planets of known mass.

.. code-block:: python

    for system in cata.findall(".//system[declination][rightascension]"):
        for planet in system.findall(".//planet[mass]"):
            print system.findtext('name'), system.findtext('rightascension'),system.findtext('declination'), planet.findvalue('mass')


Prints the names of rogue planets.

.. code-block:: python

    for planets in cata.findall(".//system/planet"):
        print planets.findtext('name')


Reference
=========
To contribute to the open exoplanet catalogue, fork the project on github!
https://github.com/OpenExoplanetCatalogue/open_exoplanet_catalogue




