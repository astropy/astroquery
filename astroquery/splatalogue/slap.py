# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Construct a SLAP query.

This is not presently used, since I don't know how to construct a complete SLAP
query.
"""


def slap_default_payload(*, request='queryData', version='2.0', wavelength='',
                         chemical_element='', initial_level_energy='',
                         final_level_energy='', temperature='', einstein_a=''):
    """
    Parse the valid parameters specified by the `IVOA SLAP`_ interface
    document.

    .. _IVOA SLAP: http://www.ivoa.net/documents/SLAP/20101209/REC-SLAP-1.0-20101209.pdf


    Parameters
    ----------
    request : 'queryData'
        No other valid entries are known
    version : '2.0'
        A valid data version number
    wavelength : 'x/y' or 'x' or 'x,y/z' or 'x/'
        Wavelength range in meters.
        'x/y' means 'in the range from x to y'
        'x/' means 'wavelength > x'
        'x' means 'wavelength == x'
        'x/y,y/z' means 'wavelength in range [x,y] or [y,z]'
        See Appendix A of the `IVOA SLAP`_ manual

    Other Parameters
    ----------------
    chemical_element : str
        A chemical element name.  Can be specified as a comma-separated list
    initial_level_energy : float
        Unit: Joules
    final_level_energy : float
        Unit: Joules
    temperature : float
        Unit : Kelvin
        Expected temperature of object.  Not needed for splatalogue
    einstein_a : float
        Unit : s^-1
    process_type : str
    process_name : str
        Examples:
        "Photoionization", "Collisional excitation",
        "Gravitational redshift", "Stark broadening", "Resonance broadening",
        "Van de Waals broadening"

    Returns
    -------
    Dictionary of parameters which can then be POSTed to the service
    """
    return locals()
