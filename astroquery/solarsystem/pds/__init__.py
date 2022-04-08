'''
RingNode
--------

:author: Ned Molter (emolter@berkeley.edu)
'''

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.solarsystem.pds`.
    """

    # server settings
    pds_server = _config.ConfigItem(
        ['https://pds-rings.seti.org/cgi-bin/tools/viewer3_xxx.pl?', ],
        'Ring Node')

    # implement later: other pds tools

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to PDS servers.')

    # PDS settings - put hardcoded dictionaries of any kind here
    
    planet_defaults = {'jupiter':{
                                'ephem':'000 URA111 %2B+URA115+%2B+DE440',
                                'moons':'727+All+inner+moons+%28U1-U15%2CU25-U27%29&'
                                },
                       'saturn':{
                                'ephem':'000+URA111+%2B+URA115+%2B+DE440',
                                'moons':'727+All+inner+moons+%28U1-U15%2CU25-U27%29&'
                                },
                       'uranus':{
                                'ephem':'000 URA111 + URA115 + DE440',
                                'moons':'727 All inner moons (U1-U15,U25-U27)'
                                },
                       'neptune':{
                                'ephem':'000+URA111+%2B+URA115+%2B+DE440',
                                'moons':'727+All+inner+moons+%28U1-U15%2CU25-U27%29&'
                                }
                       }
    


conf = Conf()

#from .core import RingNode, RingNodeClass

#__all__ = ['RingNode', 'RingNodeClass',
#           'Conf', 'conf',
#           ]