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
    url = _config.ConfigItem(
        "https://pds-rings.seti.org/cgi-bin/tools/viewer3_xxx.pl?", "Ring Node"
    )

    # implement later: other pds tools

    timeout = _config.ConfigItem(30, "Time limit for connecting to PDS servers (seconds).")


conf = Conf()

from .core import RingNode, RingNodeClass

__all__ = [
    "RingNode",
    "RingNodeClass",
    "Conf",
    "conf",
]
