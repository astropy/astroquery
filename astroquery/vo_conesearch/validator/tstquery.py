# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Sub-query to obtain test parameters from service providers.

In case USVO service is unstable, it does the following:

    #. Try USVO production server.
    #. If SR > 0.1, force SR to be 0.1.
    #. If fails, use RA=0 DEC=0 SR=0.1.

"""
# STDLIB
import warnings
from collections import OrderedDict

# ASTROPY
from astropy.table import Table
from astropy.utils.data import get_readable_fileobj
from astropy.utils.exceptions import AstropyUserWarning

# LOCAL
from astroquery.utils.commons import ASTROPY_LT_4_1

__all__ = ['parse_cs']


def parse_cs(ivoid, cap_index=1):
    """Return test query pars as dict for given IVO ID and capability index."""
    if isinstance(ivoid, bytes):  # ASTROPY_LT_4_1
        ivoid = ivoid.decode('ascii')

    # Production server.
    url = ("http://vao.stsci.edu/regtap/tapservice.aspx/sync?lang=adql&"
           "query=select%20detail_xpath%2Cdetail_value%20from%20"
           "rr.res_detail%20where%20"
           "ivoid%3D%27{0}%27%20and%20cap_index={1}%20and%20"
           "detail_xpath%20in%20%28%27/capability/testQuery/ra%27%2C"
           "%27/capability/testQuery/dec%27%2C%27/capability/testQuery/sr%27"
           "%29".format(ivoid, cap_index))

    urls_failed = False
    default_sr = 0.1

    try:
        with get_readable_fileobj(url, encoding='binary',
                                  show_progress=False) as fd:
            t_query = Table.read(fd, format='votable')
    except Exception as e:  # pragma: no cover
        urls_failed = True
        urls_errmsg = '{0} raised {1}, using default'.format(
            url, str(e))

    if not urls_failed:
        try:
            xpath = t_query['detail_xpath']
            if ASTROPY_LT_4_1:
                ra = float(
                    t_query[xpath == b'/capability/testQuery/ra']['detail_value'])
                dec = float(
                    t_query[xpath == b'/capability/testQuery/dec']['detail_value'])
                sr = float(
                    t_query[xpath == b'/capability/testQuery/sr']['detail_value'])
            else:
                ra = float(
                    t_query[xpath == '/capability/testQuery/ra']['detail_value'])
                dec = float(
                    t_query[xpath == '/capability/testQuery/dec']['detail_value'])
                sr = float(
                    t_query[xpath == '/capability/testQuery/sr']['detail_value'])

            # Handle big SR returning too big a table for some queries, causing
            # tests to fail due to timeout.
            if sr > default_sr:
                warnings.warn(
                    'SR={0} is too large, using SR={1} for {2},{3}'.format(
                        sr, default_sr, ivoid, cap_index), AstropyUserWarning)
                sr = default_sr

            d = OrderedDict({'RA': ra, 'DEC': dec, 'SR': sr})

        except Exception as e:  # pragma: no cover
            urls_failed = True
            urls_errmsg = ('Failed to retrieve test query parameters for '
                           '{0},{1}, using default: {2}'.format(ivoid, cap_index, str(e)))

    # If no test query found, use default
    if urls_failed:  # pragma: no cover
        d = OrderedDict({'RA': 0, 'DEC': 0, 'SR': default_sr})
        warnings.warn(urls_errmsg, AstropyUserWarning)

    return d
