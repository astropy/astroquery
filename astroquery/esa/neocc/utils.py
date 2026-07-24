# Useful general purpose functions for NEOCC
import numpy as np

from astropy.time import Time, TimeDelta


def convert_time(date_col, time_col=None, conversion_string=None):
    """
    Converte date/time column(s) and turn them into an astropy Time object.

    Parameters
    ----------
    date_col : `astropy.table.Column`
        The column with dates (or datetime) strings in it.
    time_col : `astropy.table.Column`
        Optional. Column with only time strings.
    conversion_string : str
        Optional. If the date(time) string are in a non-standard format
        the conversion string will be used with `astropy.time.Time.strptime`
        to create the Time object.

    Returns
    -------
    response : `astropy.time.Time`
        The converted time column as an astropy Time object.
    """

    if time_col is None:
        day, tme = np.array([x.split(".") for x in date_col]).swapaxes(0, 1)
        time_delta = TimeDelta([float("." + x) for x in tme], format='jd')

    else:
        day = np.array(date_col)
        time_delta = TimeDelta(time_col, format="jd")

    if conversion_string:
        time_obj = Time.strptime(day, conversion_string)
    else:
        time_obj = Time(day)

    return time_obj + time_delta
