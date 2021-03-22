.. doctest-skip-all

.. _astroquery.neodys:

************************************
NEODyS Queries (`astroquery.neodys`)
************************************

Getting started
===============

This module supports retrieving the orbital information of an object from the
NEODyS website (https://newton.spacedys.com/neodys/). The state vector,
covariance matrix, epoch, absolute magnitude, slope parameter, and correlation
matrix are given in dictionary form. The results can be given in either
Keplerian or Equinoctial. The only required argument is the identifier of the
object to be retrieved. Here is a basic example:

.. code-block:: python

    >>> from astroquery.neodys import NEODyS
    >>> res = neodys.core.NEODyS.query_object("1982YA")
    >>> print(res)
    {'Equinoctial State Vector': [3.643505823124891, 0.555753608185406,
    0.413673328231395, -0.316412712941692, -0.005264652421941, 48.553922087068],
    'Mean Julian Date': ['55417.557065659', 'TDT'], 'Magnitude': [17.798, 0.15],
    'Covariance Matrix': [6.737866678261391e-15, 3.835925316932412e-14,
    -6.640239789108145e-14, -1.439007899529439e-15, -4.938922190348063e-15,
    4.994817272482335e-12, 2.656750560890953e-13, -4.11492595235993e-13,
    5.390531237956025e-14, -8.210458555809306e-14, 3.034284768527233e-11,
    6.987414264633028e-13, -3.461847188742589e-14, 8.072873747426578e-14,
    -5.283334219581364e-11, 3.441265766874457e-13, -1.712409537284e-13,
    6.293229007026724e-13, 1.418015029378066e-13, -3.898114012957574e-12,
    4.0664813765478e-09], 'Keplerian Correlation Matrix': [], 'URL':
    'https://newton.spacedys.com/~neodys2/epoch//1982YA.eq0'}

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

.. code-block:: python

    >>> from astroquery.neodys import NEODyS
    >>> res = neodys.core.NEODyS.query_object(
        "1982YA", orbital_element_type="ke", epoch_near_present=1)
    >>> print(results)
    {'Keplerian State Vector': [3.648336, 0.691188, 35.123, 268.963, 144.376,
    170.251], 'Mean Julian Date': ['59200.0000', 'TDT'], 'Magnitude': [17.798,
    0.15], 'Covariance Matrix': [7.39777353e-15, -9.00996211e-15, -3.12399412e-13,
    -1.41885172e-12, 8.13796963e-12, -2.98795622e-12, 2.61069828e-14,
    -2.30621969e-12, -3.23293856e-12, -4.26709227e-12, 2.1454954e-12,
    3.66367782e-09, 3.29118054e-09, -3.80504189e-09, 4.73514563e-10,
    4.83809216e-09, -6.57723081e-09, 1.26901103e-09, 1.47852822e-08,
    -4.09276587e-09, 1.39372059e-09], 'Keplerian Correlation Matrix': [1.0,
    -0.648327, -0.06000688, -0.23716436, 0.77812746, -0.93054173, 1.0,
    -0.2358108, -0.2876617, -0.21718953, 0.35568159, 1.0, 0.7817286, -0.51699459,
    0.2095496, 1.0, -0.77766258, 0.4886979, 1.0, -0.90160069, 1.0], 'URL':
    'https://newton.spacedys.com/~neodys2/epoch//1982YA.ke1'}


Reference/API
=============

.. automodapi:: astroquery.neodys
    :no-inheritance-diagram:
