# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import warnings
import re
import time
from math import cos, radians
import requests
from bs4 import BeautifulSoup

from astropy.extern.six import BytesIO
import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable

from ..query import QueryWithLogin
from ..exceptions import InvalidQueryError, TimeoutError, NoResultsWarning
from ..utils import commons
from . import conf
from ..exceptions import TableParseError

from ..wfau import BaseWFAUClass, clean_catalog

__all__ = ['Ukidss', 'UkidssClass', 'clean_catalog']


class UkidssClass(BaseWFAUClass):

    """
    The UKIDSSQuery class.  Must instantiate this class in order to make any
    queries.  Allows registered users to login, but defaults to using the
    public UKIDSS data sets.
    """
    BASE_URL = conf.server
    LOGIN_URL = BASE_URL + "DBLogin"
    IMAGE_URL = BASE_URL + "GetImage"
    ARCHIVE_URL = BASE_URL + "ImageList"
    REGION_URL = BASE_URL + "WSASQL"
    TIMEOUT = conf.timeout

    filters = {'all': 'all', 'J': 3, 'H': 4, 'K': 5, 'Y': 2,
               'Z': 1, 'H2': 6, 'Br': 7}

    frame_types = {'stack': 'stack', 'normal': 'normal', 'interleave': 'leav',
                   'deep_stack': 'deep%stack', 'confidence': 'conf',
                   'difference': 'diff', 'leavstack': 'leavstack',
                   'all': 'all'}

    ukidss_programmes_short = {'LAS': 101,
                               'GPS': 102,
                               'GCS': 103,
                               'DXS': 104,
                               'UDS': 105, }

    ukidss_programmes_long = {'Large Area Survey': 101,
                              'Galactic Plane Survey': 102,
                              'Galactic Clusters Survey': 103,
                              'Deep Extragalactic Survey': 104,
                              'Ultra Deep Survey': 105}

    all_databases = ("UKIDSSDR10PLUS", "UKIDSSDR9PLUS",
                     "UKIDSSDR8PLUS", "UKIDSSDR7PLUS",
                     "UKIDSSDR6PLUS", "UKIDSSDR5PLUS", "UKIDSSDR4PLUS",
                     "UKIDSSDR3PLUS", "UKIDSSDR2PLUS", "UKIDSSDR1PLUS",
                     "UKIDSSDR1", "UKIDSSEDRPLUS", "UKIDSSEDR", "UKIDSSSV",
                     "WFCAMCAL08B", "U09B8v20120403", "U09B8v20100414")

    def __init__(self, username=None, password=None, community=None,
                 database='UKIDSSDR10PLUS', programme_id='all'):
        super(UkidssClass, self).__init__()
        self.database = database
        self.programme_id = programme_id  # 102 = GPS
        self.session = None
        if username is None or password is None or community is None:
            pass
        else:
            self.login(username, password, community)
        self.vista = False

Ukidss = UkidssClass()
