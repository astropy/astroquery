"""
Utilities for generating ADQL for NRAO TAP service
"""
from astropy import units as u
import astropy.coordinates as coord
from ..alma.tapsql import (_gen_str_sql, _val_parse)

ALMA_DATE_FORMAT = '%d-%m-%Y'

NRAO_BANDS = {
    '4m': (0.054*u.GHz, 0.084*u.GHz),
    'P': (0.195*u.GHz, 0.6*u.GHz),
    'L': (0.95*u.GHz,   2*u.GHz),
    'S': (1.95*u.GHz,   4*u.GHz),
    'C': (3.95*u.GHz,   8*u.GHz),
    'X': (7.95*u.GHz,  12*u.GHz),
    'U': (1.95*u.GHz, 18*u.GHz),
    'K': (17.95*u.GHz, 26.5*u.GHz),
    'A': (26.45*u.GHz, 39*u.GHz),
    'Q': (38.95*u.GHz, 50*u.GHz),
    'W': (66.95*u.GHz, 115*u.GHz),
    '1': (30*u.GHz, 50*u.GHz),
    '2': (67*u.GHz, 116*u.GHz),
    '3': (84*u.GHz, 116*u.GHz),
    '4': (125*u.GHz, 163*u.GHz),
    '5': (163*u.GHz, 211*u.GHz),
    '6': (211*u.GHz, 275*u.GHz),
    '7': (275*u.GHz, 373*u.GHz),
    '8': (385*u.GHz, 500*u.GHz),
    '9': (602*u.GHz, 720*u.GHz),
    '10': (787*u.GHz, 950*u.GHz)
}


def _gen_pos_sql(field, value):
    result = ''
    if field == 'SkyCoord.from_name':
        # resolve the source first
        if value:
            obj_coord = coord.SkyCoord.from_name(value)
            frame = 'icrs'
            ras = [str(obj_coord.icrs.ra.to(u.deg).value)]
            decs = [str(obj_coord.icrs.dec.to(u.deg).value)]
            radius = 10 * u.arcmin
        else:
            raise ValueError('Object name missing')
    else:
        if field == 's_ra, s_dec':
            frame = 'icrs'
        else:
            frame = 'galactic'
        radius = 10*u.arcmin
        if ',' in value:
            center_coord, rad = value.split(',')
            try:
                radius = float(rad.strip())*u.degree
            except ValueError:
                raise ValueError('Cannot parse radius in ' + value)
        else:
            center_coord = value.strip()
        try:
            ra, dec = center_coord.split(' ')
        except ValueError:
            raise ValueError('Cannot find ra/dec in ' + value)
        ras = _val_parse(ra, val_type=str)
        decs = _val_parse(dec, val_type=str)

    for ra in ras:
        for dec in decs:
            if result:
                result += ' OR '
            if isinstance(ra, str) and isinstance(dec, str):
                # circle
                center = coord.SkyCoord(ra, dec,
                                        unit=(u.deg, u.deg),
                                        frame=frame)

                result += \
                    "CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',{},{},{}))=1".\
                    format(center.icrs.ra.to(u.deg).value,
                           center.icrs.dec.to(u.deg).value,
                           radius.to(u.deg).value)
            else:
                raise ValueError('Cannot interpret ra({}), dec({}'.
                                 format(ra, dec))
    if ' OR ' in result:
        # use brackets for multiple ORs
        return '(' + result + ')'
    else:
        return result

def _gen_pub_sql(field, value):
    if value is True:
        return "{}='PUBLIC'".format(field)
    elif value is False:
        return "{}='LOCKED'".format(field)
    else:
        return None


def _gen_band_list_nrao_sql(field, value):
    # converts a specified band to a frequency range; alias to search
    # via freq_min and freq_max
    if isinstance(value, list):
        val = value
    else:
        val = value.split(' ')
    query = ''
    for value in val:
        band_min = NRAO_BANDS[value][0]
        band_max = NRAO_BANDS[value][1]
        band_query = '(freq_min >= {} AND freq_max <= {})'.format(
                      band_min.to(u.Hz).to_value(), band_max.to(u.Hz).to_value())
        if query != '':
           query += ' OR '+band_query
        else:
           query = band_query
        query='('+query+')'

    return query


def _gen_pol_sql(field, value):
    val = ''
    states_map = {'Stokes I': '*I*',
                  'Single-circular': 'RR',
                  'Dual-circular': 'RR, LL',
                  'Full-circular': 'RR, RL, LR, LL',
                  'Single-linear': 'XX',
                  'Dual-linear': 'XX, YY',
                  'Full-linear': 'XX, XY, YX, YY'}
    for state in states_map:
        if state in value:
            if val:
                val += '|'
            val += states_map[state]
    return _gen_str_sql(field, val)
