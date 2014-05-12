.. _astroquery.open_exoplanet_catalogue:

*****************************************
Open Exoplanet Catalogue Queries (`astroquery.open_exoplanet_catalogue`)
*****************************************

Getting started
===============

The following example illustrates a simple query to find the Kepler-67 system and print the raw XML data.

.. code-block:: python

    >>> from astroquery import open_exoplanet_catalogue as oec
    >>> xml = oec.query_system_xml('Kepler-67') 
    >>> print xml
 
    <system>
            <name>Kepler-67</name>
            <rightascension>19 36 37</rightascension>
            <declination>46 09 59</declination>
            <distance errorminus="90" errorplus="90">1107</distance>
            <star>
                    <name>Kepler-67</name>
                    <mass errorminus="0.034" errorplus="0.034">0.865</mass>
                    <radius errorminus="0.031" errorplus="0.031">0.778</radius>
                    <temperature errorminus="63" errorplus="63">5331</temperature>
                    <magV>16.4</magV>
                    <metallicity errorminus="0.003" errorplus="0.003">0.012</metallicity>
                    <spectraltype>G9V</spectraltype>
                    <age errorminus="0.17" errorplus="0.17">1</age>
                    <planet>
                            <name>Kepler-67 b</name>
                            <list>Confirmed planets</list>
                            <radius errorminus="0.014581" errorplus="0.014581">0.267923</radius>
                            <period errorminus="0.00011" errorplus="0.00011">15.72590</period>
                            <transittime errorminus="0.0048" errorplus="0.0048">2454966.9855</transittime>
                            <semimajoraxis errorminus="0.0015" errorplus="0.0015">0.1171</semimajoraxis>
                            <discoverymethod>transit</discoverymethod>
                            <lastupdate>13/06/26</lastupdate>
                            <description>Kepler-67 b is orbiting a Sun-like star in the billion-year-old open cluster NGC6811. It demonstrates that small planets can form and survive in a dense cluster environment. The frequency of planets around stars in open cluster and field stars in the Milky Way are approximately the same.</description>
                            <discoveryyear>2013</discoveryyear>
                            <new>1</new>
                    </planet>
            </star>
    </system>


The following example finds the planet 'Kepler-67 b' and prints its radius and period.

.. code-block:: python

    >>> from astroquery import open_exoplanet_catalogue as oec
    >>> kepler67b = oec.query_planet('Kepler-67 b') 

    >>> print "Period of Kepler-67 b:\t %s \t [days]"% kepler67b['period']
    Period of Kepler-67 b:   15.72590        [days]
    
    >>> print "Radius of Kepler-67 b:\t %s \t [R_Jupiter]"% kepler67b['radius']
    Radius of Kepler-67 b:   0.267923        [R_Jupiter]




Reference/API
=============

.. automodapi:: astroquery.open_exoplanet_catalogue
    :no-inheritance-diagram:
