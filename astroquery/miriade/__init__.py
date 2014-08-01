# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Miriade Query Tool
------------------
A tool to query Miriade, The Virtual Observatory Solar System Object
Ephemeris Generator, a web service of the IMCCE
http://vo.imcce.fr/webservices/miriade/

:Author: Julien Woillez (jwoillez@gmail.com) et al.
"""

from .core import Miriade, MiriadeClass

__all__ = ['Miriade','MiriadeClass']
