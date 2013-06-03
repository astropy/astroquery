"""
Astronomical Name Parser
------------------------

Should include SIMBAD and NED name parsers
"""

import simbad
import astropy.coordinates as coords

class NameParserError(Exception):
    pass

def name_parser(name, service='simbad'):
    """
    Determine the coordinates of a named object using SIMBAD or NED

    Parameters
    ----------
    name : str
        Object name
    service : str
        Service name, can be one of: simbad, ned (ned not implemented yet)

    Returns
    -------
    astropy.coordinates

    Examples
    --------
    >>> M42_coords = name_parser('M 42')
    >>> print M42_coords
    <ICRSCoordinates RA=83.82208 deg, Dec=-5.39111 deg>
    """

    if service.lower() == 'simbad':
        q = simbad.QueryId(name)
        result = q.execute()
        if len(result.table) == 1:
            coordinate = coords.ICRSCoordinates(result.table['RA'][0],
                    result.table['DEC'][0], unit=('hour','degree'))
        elif len(result.table) == 0:
            raise NameParserError("No match found for source %s" % name)
    else:
        raise NotImplementedError("No such service %s" % service)

    return coordinate
