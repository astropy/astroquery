# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""NSF's OIR Lab Astro Data Archive(Beta)
-------------------------------------- 

The NSF's OIR Lab Astro Data Archive (formerly NOAO Science Archive)
provides access to data taken with more than 40 telescope and
instrument combinations, including those operated in partnership with
the WIYN, SOAR and SMARTS consortia, from semester 2004B to the
present. In addition to raw data, pipeline-reduced data products from
the DECam, Mosaic and NEWFIRM imagers are also available, as well as
advanced data products delivered by teams carrying out surveys and
other large observing programs with NSF OIR Lab facilities.

Total holdings 9,228,925

| Telescope/Instrument | Total images | Volume |
|----------------------+--------------+--------|
| bok23m - 90prime     |       290070 |     3% |
| ct09m - ccd_imager   |        99651 |     1% |
| ct13m - andicam      |       528124 |     5% |
| ct15m - chiron       |       205521 |     2% |
| ct4m - arcoiris      |        49024 |     0% |
| ct4m - cosmos        |        18763 |     0% |
| ct4m - decam         |      4626073 |    50% |
| ct4m - mosaic_2      |       254004 |     2% |
| ct4m - newfirm       |       339731 |     3% |
| kp09m - hdi          |       110270 |     1% |
| kp09m - mosaic       |         1006 |     0% |
| kp09m - mosaic_1_1   |         3533 |     0% |
| kp4m - kosmos        |         8068 |     0% |
| kp4m - mosaic        |         2420 |     0% |
| kp4m - mosaic3       |       563386 |     6% |
| kp4m - mosaic_1      |        52475 |     0% |
| kp4m - mosaic_1_1    |       142351 |     1% |
| kp4m - newfirm       |       962054 |    10% |
| soar - goodman       |       683389 |     7% |
| soar - sami          |        15639 |     0% |
| soar - soi           |         8981 |     0% |
| soar - spartan       |       166821 |     1% |
| soar - triplespec    |         1167 |     0% |
| wiyn - bench         |        32023 |     0% |
| wiyn - whirc         |        64381 |     0% |
|----------------------+--------------+--------|

ACKNOWLEDGMENT

This research uses services or data provided by the Astro Data Archive
at NSF's National Optical-Infrared Astronomy Research
Laboratory. NSF's OIR Lab is operated by the Association of
Universities for Research in Astronomy (AURA), Inc. under a
cooperative agreement with the National Science Foundation.


See also: gemini, nrao

"""

from astropy import config as _config

class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.noao`.
    """
    server = _config.ConfigItem(
        ['https://astroarchive.noao.edu',
         ],
        'Name of the NOAO server to use.'
        )
    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to NOAO server.'
        )

conf = Conf()

from .core import Noao, NoaoClass

__all__ = ['Noao', 'NoaoClass',
           'conf', 'Conf']
