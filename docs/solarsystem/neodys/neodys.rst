.. _astroquery.neodys:

************************************************
NEODyS Queries (`astroquery.solarsystem.neodys`)
************************************************

Getting started
===============

This module supports retrieving the orbital information of an object from the
NEODyS website (https://newton.spacedys.com/neodys/). The state vector,
covariance matrix, epoch, absolute magnitude, slope parameter, and correlation
matrix are given in dictionary form. The results can be given in either
Keplerian or Equinoctial. The only required argument is the identifier of the
object to be retrieved. Here is a basic example:

.. doctest-remote-data::

    >>> from astroquery.solarsystem.neodys import NEODyS
    >>> result = NEODyS.query_object("1982YA")
    >>> print(result)  # doctest: +IGNORE_OUTPUT
    {'Equinoctial State Vector': [3.6501814973859177, 0.55510840531515, 0.412442615432626, -0.316403600209491, -0.005615261288851, 7.4974723045741],
    'Mean Julian Date': ['57672.370442276', 'TDT'],
    'Magnitude': [17.478, 0.15],
    'Covariance Matrix': [2.983481961445874e-14, 1.319692615237118e-13, -3.466482497808619e-13,
                          -5.179294501167426e-15, 4.40306644125416e-15, 2.841155344781695e-11,
                          7.248099966950092e-13, -1.55363923471562e-12, -4.018099391315557e-14,
                          -1.400231787484278e-14, 1.210874090734312e-10, 4.091233073364273e-12,
                          4.62498475268648e-15, -1.406987981569261e-14, -3.37147537859451e-10,
                          6.527443331995206e-13, -4.021096836415107e-13, -3.876453730470366e-12,
                          3.584924689571663e-13, 8.057672786144392e-12, 2.841126641896583e-08],
    'Keplerian Correlation Matrix': [],
    'URL': 'https://newton.spacedys.com/~neodys2/epoch//1982YA.eq0'}


More detailed parameters
------------------------

There are two other optional parameters that can be specified. These
are ``orbital_element_type`` which specifies whether the results will
be in Keplerian or Equinoctial. Valid values are 'ke' for Keplerian
and 'eq' for Equinoctial. The other is ``epoch_near_present``, a flag
which sets the epoc to near present instead of near middle of the arc.
Valid values are '0' for near middle of the arc, and '1' for near
present. The default values are 'eq' and '0'. Note: Keplerian elements
are given to a lower precision on the NEODyS website.

Here's an example with these optional parameters:

.. doctest-remote-data::

    >>> from astroquery.solarsystem.neodys import NEODyS
    >>> results = NEODyS.query_object("1982YA", orbital_element_type="ke", epoch_near_present=1)
    >>> print(results)  # doctest: +IGNORE_OUTPUT
    {'Keplerian State Vector': [3.64669, 0.691945, 35.165, 268.935, 144.408, 283.498],
    'Mean Julian Date': ['60000.0000', 'TDT'],
    'Magnitude': [17.478, 0.15],
    'Covariance Matrix': [3.92261704e-14, -1.16359258e-13, 3.11585918e-13,
                          5.00974344e-13, 3.35974943e-11, -6.24946297e-12,
                          4.44803944e-13, 3.19086108e-12, -3.60667109e-12,
                          -9.43905769e-11, 6.70717262e-12, 6.92715199e-09,
                          7.66896347e-09, -7.46695141e-09, 1.41600249e-10,
                          1.22064798e-08, -1.21318576e-08, 1.39344281e-09,
                          4.21853471e-08, -7.19870851e-09, 2.62151264e-09],
    'Keplerian Correlation Matrix': [1.0, -0.88090418, 0.01890221,
                                     0.02289456, 0.82592026, -0.61628098,
                                     1.0, 0.0574839, -0.0489471,
                                     -0.68907027, 0.19641705, 1.0,
                                     0.83399624, -0.43680254, 0.0332285,
                                     1.0, -0.53462747, 0.24633037,
                                     1.0, -0.68453837, 1.0],
    'URL': 'https://newton.spacedys.com/~neodys2/epoch//1982YA.ke1'}


Reference/API
=============

.. automodapi:: astroquery.solarsystem.neodys
    :no-inheritance-diagram:
