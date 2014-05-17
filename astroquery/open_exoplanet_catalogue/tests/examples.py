from astropy.tests.helper import remote_data
from ...open_exoplanet_catalogue import get_catalogue
from ...open_exoplanet_catalogue import findvalue 

class Examples:

    def __init__(self):
        self.oec = get_catalogue()

    @remote_data
    def example1(self):
        # example 1
        # find all planets
        for planet in self.oec.findall(".//planet"):
            print findvalue(planet, 'name'), findvalue(planet, 'mass')

    @remote_data
    def example2(self):
        # example 2
        # find stars with a mass, and find planets with a mass around those stars
        for star in self.oec.findall(".//star[mass]"):
            for planet in star.findall(".//planet[mass]"):
                print findvalue(planet, 'mass').machine_readable(), findvalue(star, 'mass').machine_readable()

    @remote_data
    def example3(self):
        # example 3
        # find stars in binaries 
        for star in self.oec.findall(".//binary/star"):
            print findvalue(star, 'name')

    @remote_data
    def example4(self):
        # example 4
        # find all planets orbiting a binary
        for planet in self.oec.findall(".//binary/planet"):
            print findvalue( planet, 'name'), findvalue( planet, 'period')

    @remote_data
    def example5(self):
        # example 5
        # find a specific planet
        planet = self.oec.find(".//planet[name='Kepler-68 b']")
        print findvalue( planet, 'name'), findvalue(planet, 'radius'), findvalue(planet, 'mass')

    @remote_data
    def example6(self):
        # example 6
        # find planets with a radius greater than 1
        for planet in self.oec.findall(".//planet[radius]"):
            if findvalue(planet, 'radius') > 1:
                print findvalue( planet, 'name'), findvalue( planet, 'radius')

    @remote_data
    def example7(self):
        # example 7
        # planets that belong to a star in a binary
        for binary in self.oec.findall(".//binary/star/planet"):
            print findvalue( binary, 'name')

    @remote_data
    def example8(self):
        # example 8
        # ratio of star mass to planet mass
        for star in self.oec.findall(".//star[mass]/planet[mass].."):
            if findvalue(star, 'mass') != None:
                for planet in star.findall(".//planet"):
                    if findvalue(planet, 'mass') != None:
                        print findvalue( star, 'name'), findvalue( planet, 'name'), "Ratio:", findvalue( star, 'mass')/findvalue( planet, 'mass')

    @remote_data
    def example9(self):
        # example 9
        # find planets that have an upperlimit on mass
        for planet in self.oec.findall(".//planet/mass[@upperlimit].."):
            print findvalue( planet, 'name'), findvalue(planet, 'mass')

    @remote_data
    def example10(self):
        # example 10
        # print the number of planets in systems
        for star in self.oec.findall(".//star[planet]"):
            print findvalue( star, 'name'), len(star.findall(".//planet"))

    @remote_data
    def example11(self):
        # example 11
        # print all the properties of a planet
        for properties in self.oec.findall(".//planet[name='Kepler-20 b']/*"):
            print "\t" + properties.tag + ":", properties.text

    @remote_data
    def example12(self):
        # example 12
        # print all of the declination and right ascension of systems with planets with mass
        for systems in self.oec.findall(".//system[declination][rightascension]"):
            for planet in systems.findall(".//planet[mass]"):
                print findvalue( systems, 'name'), findvalue( systems, 'rightascension'), findvalue( systems, 'declination'), findvalue( planet, 'mass')

    @remote_data
    def example13(self):
        # example 13
        # print the rogue planets
        for planets in self.oec.findall(".//system/planet"):
            print findvalue( planets, 'name')
