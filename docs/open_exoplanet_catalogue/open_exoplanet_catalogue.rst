.. _astroquery.open_exoplanet_catalogue:

***************************************************************
Open Exoplanet Catalogue(`astroquery.open_exoplanet_catalogue`)
***************************************************************

Getting started
===============

This module gives easy access to the open exoplanet catalogue in the form of an XML element tree. 

To start import the catalog and generate the catalogue.

.. code-block:: python

        from astroquery import open_exoplanet_catalogue as oec
        from astroquery.open_exoplanet_catalogue import findvalue

        # getting the catalogue from the default remote source
        cata = oec.get_catalogue()

        # getting the catalogue from a local path
        cata = oec.get_catalogue("path/to/file/systems.xml.gz")



Examples
========

First import the module and generate the catalogue. The findvalue function provides a simple method of getting values from Elements.

.. code-block:: python

        from astroquery import open_exoplanet_catalogue as oec
        from astroquery.open_exoplanet_catalogue import findvalue

        cata = oec.get_catalogue()

Prints all planets and their masses.

.. code-block:: python

    for planet in oec.findall(".//planet"):
        print findvalue(planet, 'name'), findvalue(planet, 'mass')

Prints all of the planets with known mass around stars of known mass in a machine readable format.

.. code-block:: python

    for star in oec.findall(".//star[mass]"):
        for planet in star.findall(".//planet[mass]"):
            print findvalue(planet, 'mass').machine_readable(), findvalue(star, 'mass').machine_readable()

Print all the names of stars in binaries.
         
.. code-block:: python

    for star in oec.findall(".//binary/star"):
        print findvalue(star, 'name')

Prints all the planet names and period of planets around binaries

.. code-block:: python

    for planet in oec.findall(".//binary/planet"):
        print findvalue( planet, 'name'), findvalue( planet, 'period')

Prints the name, radius and mass of the planet Kepler-68 b. 

.. code-block:: python

    planet = oec.find(".//planet[name='Kepler-68 b']")
    print findvalue( planet, 'name'), findvalue(planet, 'radius'), findvalue(planet, 'mass')

Prints the name and radius of planets with a radius greater than 1 jupiter radius.

.. code-block:: python

    for planet in oec.findall(".//planet[radius]"):
        if findvalue(planet, 'radius') > 1:
            print findvalue( planet, 'name'), findvalue( planet, 'radius')

Prints the names of the planets around a single star in a binary.

.. code-block:: python

    for binary in oec.findall(".//binary/star/planet"):
        print findvalue( binary, 'name')

Prints a ratio of star and planet mass.

.. code-block:: python

    for star in oec.findall(".//star[mass]/planet[mass].."):
        if findvalue(star, 'mass') != None:
            for planet in star.findall(".//planet"):
                if findvalue(planet, 'mass') != None:
                    print findvalue( star, 'name'), findvalue( planet, 'name'), "Ratio:", findvalue( star, 'mass')/findvalue( planet, 'mass')

Prints planets whose mass has an upper limit

.. code-block:: python

    for planet in oec.findall(".//planet/mass[@upperlimit].."):
        print findvalue( planet, 'name'), findvalue(planet, 'mass')
   
Prints all stars with the number of planets orbiting them

.. code-block:: python


    for star in oec.findall(".//star[planet]"):
        print findvalue( star, 'name'), len(star.findall(".//planet"))

Prints all the properties of Kepler-20 b.

.. code-block:: python

    for properties in oec.findall(".//planet[name='Kepler-20 b']/*"):
        print "\t" + properties.tag + ":", properties.text

Prints the right ascension and declination of systems with planets of known mass.

.. code-block:: python

    for systems in oec.findall(".//system[declination][rightascension]"):
        for planet in systems.findall(".//planet[mass]"):
            print findvalue( systems, 'name'), findvalue( systems, 'rightascension'), findvalue( systems, 'declination'), findvalue( planet, 'mass')

Prints the names of rogue planets.

.. code-block:: python

    for planets in oec.findall(".//system/planet"):
        print findvalue( planets, 'name')

Reference
=========
To contribute to the open exoplanet catalogue, fork the project on github!
https://github.com/OpenExoplanetCatalogue/open_exoplanet_catalogue
