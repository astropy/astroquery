# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
SkyBoT
------

:author: Michael Mommert (mommermiscience@gmail.com)
"""

from astropy import config as _config
import astropy.units as u


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.skybot`.
    """

    server = _config.ConfigItem(
        ['http://vo.imcce.fr/webservices/skybot/skybotconesearch_query.php'],
        'SkyBoT')

    timeout = _config.ConfigItem(
        300,
        'Time limit for connecting to IMCCE/SkyBoT server.')

    # dictionary for field name and unit conversions using 'output=all`
    field_names = {'Num': 'Number',
                   'Name': 'Name',
                   'RA(h)': 'RA',
                   'DE(deg)': 'DEC',
                   'Class': 'Type',
                   'Mv': 'V',
                   'Err(arcsec)': 'posunc',
                   'd(arcsec)': 'centerdist',
                   'dRA(arcsec/h)': 'RA_rate',
                   'dDEC(arcsec/h)': 'DEC_rate',
                   'Dg(ua)': 'geodist',
                   'Dh(ua)': 'heliodist',
                   'Phase(deg)': 'alpha',
                   'SunElong(deg)': 'elong',
                   'x(au)': 'x',
                   'y(au)': 'y',
                   'z(au)': 'z',
                   'vx(au/d)': 'vx',
                   'vy(au/d)': 'vy',
                   'vz(au/d)': 'vz',
                   'Ref. Epoch(JD) ': 'epoch'}
    field_units = {'RA': u.deg,  # after conversion to deg
                   'DEC': u.deg,  # after conversion to deg
                   'V': u.mag,
                   'posunc': u.arcsec,
                   'centerdist': u.arcsec,
                   'RA_rate': u.arcsec/u.hour,
                   'DEC_rate': u.arcsec/u.hour,
                   'geodist': u.au,
                   'heliodist': u.au,
                   'alpha': u.degree,
                   'elong': u.degree,
                   'x': u.au,
                   'y': u.au,
                   'z': u.au,
                   'vx': u.au/u.day,
                   'vy': u.au/u.day,
                   'vz': u.au/u.day,
                   'epoch': u.day}


conf = Conf()

from .core import Skybot, SkybotClass

__all__ = ['Skybot', 'SkybotClass',
           'Conf', 'conf']
