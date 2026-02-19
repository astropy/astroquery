# Licensed under a 3-clause BSD style license - see LICENSE.rst

import warnings
from six import BytesIO
from astropy.table import Table
from astropy.io import fits
from astropy import coordinates
from astropy import units as u
from ..query import BaseQuery
from ..utils import commons
from ..utils import async_to_sync
from ..exceptions import InvalidQueryError, NoResultsWarning
from . import conf

__all__ = ['ODA', 'ODAClass']


@async_to_sync
class ODAClass(BaseQuery):

    """
    ...
    """

    URL = conf.server
    TIMEOUT = conf.timeout

    def query(self):
        raise NotImplementedError


ODA = ODAClass()
