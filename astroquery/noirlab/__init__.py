# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
NSF NOIRLab Astro Data Archive
==============================

Overview
--------

The NOIRLab Astro Data Archive (formerly NOAO Science Archive) provides
access to data taken with more than 40 telescope and instrument combinations,
including those operated in partnership with the WIYN, SOAR and SMARTS
consortia, from semester 2004B to the present. In addition to raw data,
pipeline-reduced data products from the DECam, Mosaic and NEWFIRM imagers
are also available, as well as advanced data products delivered by teams
carrying out surveys and other large observing programs with NSF NOIRLab
facilities.

A detailed list of holdings in the archive is available at
https://astroarchive.noirlab.edu/about/.

Acknowledgment
--------------

This research uses services or data provided by the Astro Data Archive at
NSF's NOIRLab. NOIRLab is operated by the Association of Universities for
Research in Astronomy (AURA), Inc. under a cooperative agreement with the
National Science Foundation.
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.noirlab`.
    """
    server = _config.ConfigItem(['https://astroarchive.noirlab.edu',],
                                'Name of the NSF NOIRLab server to use.')
    timeout = _config.ConfigItem(30,
                                 'Time limit for connecting to NSF NOIRLab server.')


conf = Conf()

from .core import NOIRLab, NOIRLabClass  # noqa

__all__ = ['NOIRLab', 'NOIRLabClass',
           'conf', 'Conf']
