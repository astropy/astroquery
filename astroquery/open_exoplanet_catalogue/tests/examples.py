#!/usr/bin/python
from ...open_exoplanet_catalogue import get_catalogue
from ...open_exoplanet_catalogue import findvalue 

oec = get_catalogue()

def example1():
    # example 1
    # find all planets
    for planet in oec.findall(".//planet"):
        print findvalue(planet, 'name'), findvalue(planet, 'mass')

def example2():
    # example 2
    # find stars with a mass, and find planets with a mass around those stars
    for star in oec.findall(".//star[mass]"):
        for planet in star.findall(".//planet[mass]"):
            print findvalue(planet, 'mass').machine_readable(), findvalue(star, 'mass').machine_readable()

def example3():
    # example 3
    # find stars in binaries 
    for star in oec.findall(".//binary/star"):
        print findvalue(star, 'name')

def example4():
    # example 4
    # find all planets orbiting a binary
    for planet in oec.findall(".//binary/planet"):
        print findvalue( planet, 'name'), findvalue( planet, 'period')

def example5():
    # example 5
    # find a specific planet
    planet = oec.find(".//planet[name='Kepler-68 b']")
    print findvalue( planet, 'name'), findvalue(planet, 'radius'), findvalue(planet, 'mass')

def example6():
    # example 6
    # find planets with a radius greater than 1
    for planet in oec.findall(".//planet[radius]"):
        if findvalue(planet, 'radius') > 1:
            print findvalue( planet, 'name'), findvalue( planet, 'radius')

def example7():
    # example 7
    # planets that belong to a star in a binary
    for binary in oec.findall(".//binary/star/planet"):
        print findvalue( binary, 'name')

def example8():
    # example 8
    # ratio of star mass to planet mass
    for star in oec.findall(".//star[mass]/planet[mass].."):
        if findvalue(star, 'mass') != None:
            for planet in star.findall(".//planet"):
                if findvalue(planet, 'mass') != None:
                    print findvalue( star, 'name'), findvalue( planet, 'name'), "Ratio:", findvalue( star, 'mass')/findvalue( planet, 'mass')

def example9():
    # example 9
    # find planets that have an upperlimit on mass
    for planet in oec.findall(".//planet/mass[@upperlimit].."):
        print findvalue( planet, 'name'), findvalue(planet, 'mass')

    
def example10():
    # example 10
    # print the number of planets in systems
    for star in oec.findall(".//star[planet]"):
        print findvalue( star, 'name'), len(star.findall(".//planet"))

def example11():
    # example 11
    # print all the properties of a planet
    for properties in oec.findall(".//planet[name='Kepler-20 b']/*"):
        print "\t" + properties.tag + ":", properties.text

    
def example12():
    # example 12
    # print all of the declination and right ascension of systems with planets with mass
    for systems in oec.findall(".//system[declination][rightascension]"):
        for planet in systems.findall(".//planet[mass]"):
            print findvalue( systems, 'name'), findvalue( systems, 'rightascension'), findvalue( systems, 'declination'), findvalue( planet, 'mass')


def example13():
    # example 13
    # print the rogue planets
    for planets in oec.findall(".//system/planet"):
        print findvalue( planets, 'name')
  
    
