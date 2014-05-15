#!/usr/bin/python
import xml.etree.ElementTree as ET
import urllib
import gzip
import io
import os
"""
To access the catalogue
from oec2py import oec

this gives an xml element tree which can be parse as shown in the examples.

Finding values use the findvalue function
example:
from oec2py import oec

for planet in oec.findall(".//planet"):
    print planet.findvalue('mass')
"""

oec_server_url = "https://github.com/OpenExoplanetCatalogue/oec_gzip/raw/master/systems.xml.gz"

__all__ = ['xml_element_to_dict','findvalue', 'get_catalogue']

def get_catalogue(filepath=None):
    """ (str) -> ElementTree
    Return an element tree of the open exoplanet catalogue. If no filepath is given, remote source is used.
    """

    if filepath is None:
        oec = ET.parse(gzip.GzipFile(fileobj=io.BytesIO(urllib.urlopen(oec_server_url).read())))
    else:
        oec = ET.parse(gzip.GzipFile(filepath)) 
    return oec

def xml_element_to_dict(e):
    """ (str) -> dict
    Converts xml tree to dictionary
    """

    d = {}
    for c in e.getchildren():
        d[c.tag] = c.text
    return d
    
class Number(object):
    """ Number class for values containing errors. Math operations use 
    the value given. Checking for no 'value' must use "==". Numbers with
    upper or lower limits as assumed to have no value.

    >>>num = Number(10, errorminus=0.5, errorplus=0.8)
    >>>str(num)
    10 +0.5 -0.8

    >>>num * 2
    20

    >>>num + 2
    12

    >>>num.errorminus
    0.5

    >>>num = Number(None, upperlimit=10)
    >>>str(num) 
    "upperlimit=10"
    
    >>>num + 2
    TypeError:....

    >>>num == None
    True

    >>>num is None
    False
    """

    def __init__(self, value, **kwargs):
        """ "(float, float, float) -> (Number)
        Number object acts as a typical float object, but can hold\
        errorminus, errorplus, lowerlimit, upperlimit
        mathematical operations use value. Number == Number does compare
        the error values as well
        """
        try:
            self.value = float(value)
        except:
            self.value = value
        for key,val in kwargs.iteritems():
            setattr(self, key, value)
   

    def __str__(self):
        """ (Number) -> str
        Returns a string representation of the Number

        2.0
        2.0 +1.0 -1.5
        2.0 +/-1.0
        >2.0
        <2.0
        """
        tempstr = ""
        if self.value is not None:
            tempstr += str(self.value)
        if hasattr(self, "errorplus") and self.errorplus is not None and\
                hasattr(self,"errorminus") and self.errorminus is not None:

            if self.errorplus == self.errorminus:
                tempstr += " +/-" + str(self.errorplus)
            else:
                tempstr += " +"+str(self.errorplus) +" -"+str(self.errorminus)
        if hasattr(self,"upperlimit") and self.upperlimit is not None:
            tempstr += "<"+ str(self.upperlimit)
        elif hasattr(self,"lowerlimit") and self.lowerlimit is not None:
            tempstr += ">"+ str(self.lowerlimit)
        return tempstr

    def machine_readable(self, seperator="\t",missingval="None"):
        """ (str, str) -> str
        creates a string intedned for a machine to read (ex, gnuplot)
        prints as follows
        value(seperator)errorplus(seperator)errorminus(seperator)upperlimit(seperator)lowerlimit
        
        if the value does not exist, the missingval is added instead
        """

        temp = ""
        if hasattr(self,"value") and self.value is not None:
            temp += str(self.value) + seperator 
        else:
            temp += missingval + seperator
        if hasattr(self,"errorplus") and self.errorplus is not None:
            temp += str(self.errorplus) + seperator 
        else:
            temp += missingval + seperator
        if hasattr(self,"errorminus") and self.errorminus is not None:
            temp += str(self.errorminus) + seperator 
        else:
            temp += missingval + seperator
        if hasattr(self,"upperlimit") and self.upperlimit is not None:
            temp += str(self.upperlimit) + seperator 
        else:
            temp += missingval + seperator
        if hasattr(self,"lowerlimit") and self.lowerlimit is not None:
            temp += str(self.lowerlimit) + seperator 
        else:
            temp += missingval + seperator
        return temp

    def __setattr__(self, key, val):

        try:
            self.__dict__[key] = float(val)
        except:
            self.__dict__[key] = val

    def __eq__(self, num):
        """ (any)-> any
        returns true if value of self is the same as value of num
        x == y
        if num is of type Number, this will check the errors as well
        """
        if num.__class__.__name__ == "Number":
            return self.value == num.value and\
                    self.errorminus == num.errorminus and\
                    self.errorplus == num.errorplus and\
                    self.lowerlimit == num.lowerlimit and\
                    self.upperlimit == num.upperlimit
        else:
            return self.value == num


    def __add__(self, num):
        return self.value + num

    def __sub__(self, num):
        return self.value - num

    def __lt__(self, num):
        return self.value < num

    def __le__(self, num):
        return self.value <= num

    def __ne__(self, num):
        """ (any) -> any
        returns true if self value is not equal to num value
        x != y
        if num is of type Number, it will check errors as well
        """

        if num.__class__.__name__ == "Number":
            return self.value != num.value and\
                    self.errorminus != num.errorminus and\
                    self.errorplus != num.errorplus
        else:
            return self.value != num

    def __gt__(self, num):
        return self.value > num
    
    def __ge__(self, num):
        return self.value >= num

    def __mul__(self, num):
        return self.value * num

    def __div__(self, num):
        return self.value / num

    def __floordiv__(self, num):
        return self.value // num

    def __mod__(self, num):
        return self.value % num

    def __divmod__(self, num):
        return divmod(self.value, num)

    def __pow__(self, num,*z):
        return pow(self.value, num,*z)

    def __float__(self):
        return float(self.value)

    def __cmp__(self, num):
        return cmp(self.value, num)

    def __and__(self, num):
        return self.value & num

    def __abs__(self):
        return abs(self.value)

    def __coerce__(self, num):
        return coerce(self.value, num)

    def __hash__(self):
        return hash(self.value)

    def __hex__(self):
        return hex(self.value)

    def __int__(self):
        return int(self.value)

    def __invert__(self):
        return ~self.value

    def __long__(self):
        return long(self.value)

    def __lshift__(self, num):
        return self.value << num

    def __neg__(self):
        return -self.value

    def __nonzero__(self):
        return self.value != 0
    
    def __oct__(self):
        return oct(self.value)

    def __or__(self, num):
        return self.value | num

    def __pos__(self):
        return +self.value

    def __radd__(self, num):
        return num + self.value

    def __rdiv__(self, num):
        return num / self.value

    def __rdivmod(self, num):
        return divmod(num, self.value)

    def __repr__(self):
        return str(self)

    def __rfloordiv__(self, num):
        return num // self.value

    def __rlshift__(self, num):
        return num << self.value

    def __rmod__(self, num):
        return num % self.value

    def __rmul__(self, num):
        return num * self.value

    def __ror__(self,num):
        return num | self.value

    def __rpow__(self, num,*z):
        return pow(num, self.value,*z)

    def __rrshift__(self, num):
        return num >> self.value 

    def __rshift__(self, num):
        return self.value >> num

    def __rsub__(self, num):
        return num - self.value

    def __rtruediv__(self, num):
        return num / self.value

    def __rxor__(self, num):
        return num^self.value

    def __truediv__(self, num):
        return self.value / num

    def __xor__(self, num):
        return self.value^num

    def bit_length(self):
        return self.value.bit_length()

    def asymmetric(self):
        """ (Number) -> bool
        returns true if the error values are asymmetric
        """

        return self.errorminus != self.errorplus

def findvalue(self, searchstring):
    """ (str) -> Number
    Find the tag given by searchstring and return its data as a Number object.
    """

    res = self.find(searchstring)
    if res is None:
        return None
    if len(res.attrib) == 0:
       return Number(res.text) 
    tempnum = Number(res.text)
    if res.attrib.has_key("errorminus"):
        tempnum.errorminus = res.attrib["errorminus"]
    if res.attrib.has_key("errorplus"):
        tempnum.errorplus = res.attrib["errorplus"]
    if res.attrib.has_key("upperlimit"):
        tempnum.upperlimit = res.attrib["upperlimit"]
    if res.attrib.has_key("lowerlimit"):
        tempnum.lowerlimit = res.attrib["lowerlimit"]
    return tempnum 


ET.Element.findvalue = findvalue 


if __name__ == "__main__":

    oec = get_catalogue()

    # examples
    print("---------- Example 1 ----------")
    # example 1
    # find all planets
    for planet in oec.findall(".//planet"):
        print planet.findtext('name'), planet.findvalue('mass')

    print("---------- Example 2 ----------")
    # example 2
    # find stars with a mass, and find planets with a mass around those stars
    for star in oec.findall(".//star[mass]"):
        for planet in star.findall("./planet[mass]"):
            print planet.findvalue('mass').machine_readable(),star.findvalue('mass').machine_readable()
    print("---------- Example 3 ----------")
    # example 3
    # find stars in binaries 
    for star in oec.findall(".//binary/star"):
        print star.findtext('name')

    print("---------- Example 4 ----------")
    # example 4
    # find all planets orbiting a binary
    for planet in oec.findall(".//binary/planet"):
        print planet.findtext('name'), planet.findvalue('period')

    print("---------- Example 5 ----------")
    # example 5
    # find a specific planet
    planet = oec.find(".//planet[name='Kepler-68 b']")
    print planet.findtext('name'), planet.findvalue('radius'), planet.findvalue('mass')

    print("---------- Example 6 ----------")
    # example 6
    # find planets with a radius greater than 1
    for planet in oec.findall(".//planet[radius]"):
        if planet.findvalue('radius') > 1:
            print planet.findtext('name'), planet.findvalue('radius')

    print("---------- Example 7 ----------")
    # example 7
    # planets that belong to a star in a binary
    for binary in oec.findall(".//binary/star/planet"):
        print binary.findtext('name')

    print("---------- Example 8 ----------")

    # example 8
    # ratio of star mass to planet mass
    for star in oec.findall(".//star[mass]/planet[mass].."):
        if star.findvalue('mass') != None:
            for planet in star.findall(".//planet"):
                if planet.findvalue('mass') != None:
                    print star.findtext('name'),planet.findtext('name'), "Ratio:", star.findvalue('mass')/planet.findvalue('mass')

    print("---------- Example 9 ----------")
    # example 9
    # find planets that have an upperlimit on mass
    for planet in oec.findall(".//planet/mass[@upperlimit].."):
        print planet.findtext('name'), planet.findvalue('mass')

    
    print("---------- Example 10 ----------")
    # example 10
    # print the number of planets in systems
    for star in oec.findall(".//star[planet]"):
        print star.findtext('name'), len(star.findall(".//planet"))

    print("---------- Example 11 ----------")
    # example 11
    # print all the properties of a planet
    for properties in oec.findall(".//planet[name='Kepler-20 b']/*"):
        print "\t" + properties.tag + ":", properties.text

    
    print("---------- Example 12 ----------")
    # example 12
    # print all of the declination and right ascension of systems with planets with mass
    for systems in oec.findall(".//system[declination][rightascension]"):
        for planet in systems.findall(".//planet[mass]"):
            print systems.findtext('name'), systems.findtext('rightascension'),systems.findtext('declination'), planet.findvalue('mass')


    print("---------- Example 13 ----------")
    # example 13
    # print the rogue planets
    for planets in oec.findall(".//system/planet"):
        print planets.findtext('name')
  
    
