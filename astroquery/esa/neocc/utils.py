# Useful general purpose functions for NEOCC
import numpy as np

from astropy.time import Time, TimeDelta


def convert_time(date_col, time_col=None, conversion_string=None):
    """
    Take a column with times as strings and turn it into an astropy Time object.

    TODO: finish documentation
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
