"""
RingNode
--------

:author: Ned Molter (emolter@berkeley.edu)
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.solarsystem.pds`.
    """

    # server settings
    pds_server = _config.ConfigItem(
        ["https://pds-rings.seti.org/cgi-bin/tools/viewer3_xxx.pl?",], "Ring Node"
    )

    # implement later: other pds tools

    timeout = _config.ConfigItem(30, "Time limit for connecting to PDS servers.")

    # PDS settings - put hardcoded dictionaries of any kind here

    planet_defaults = {
        "mars": {
            "ephem": "000 MAR097 + DE440",
            "moons": "402 Phobos, Deimos",
            "center_ansa": "Phobos Ring",
            "rings": "Phobos, Deimos",
        },
        "jupiter": {
            "ephem": "000 JUP365 + DE440",
            "moons": "516 All inner moons (J1-J5,J14-J16)",
            "center_ansa": "Main Ring",
            "rings": "Main & Gossamer",
        },
        "saturn": {
            "ephem": "000 SAT389 + SAT393 + SAT427 + DE440",
            "moons": "653 All inner moons (S1-S18,S32-S35,S49,S53)",
            "center_ansa": "A",
            "rings": "A,B,C,F,G,E",
        },
        "uranus": {
            "ephem": "000 URA111 + URA115 + DE440",
            "moons": "727 All inner moons (U1-U15,U25-U27)",
            "center_ansa": "Epsilon",
            "rings": "All rings",
        },
        "neptune": {
            "ephem": "000 NEP081 + NEP095 + DE440",
            "moons": "814 All inner moons (N1-N8,N14)",
            "center_ansa": "Adams Ring",
            "rings": "Galle, LeVerrier, Arago, Adams",
        },
        "pluto": {
            "ephem": "000 PLU058 + DE440",
            "moons": "905 All moons (P1-P5)",
            "center_ansa": "Hydra",
            "rings": "Styx, Nix, Kerberos, Hydra",
        },
    }

    neptune_arcmodels = {
        1: "#1 (820.1194 deg/day)",
        2: "#2 (820.1118 deg/day)",
        3: "#3 (820.1121 deg/day)",
    }


conf = Conf()

from .core import RingNode, RingNodeClass

__all__ = [
    "RingNode",
    "RingNodeClass",
    "Conf",
    "conf",
]
