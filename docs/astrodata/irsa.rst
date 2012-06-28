.. _astrodata.irsa:

*****************************************
IRSA Queries (`astrodata.irsa`)
*****************************************

Getting started
===============

The following example illustrates an IRSA Gator query::

    >>> from astrodata import irsa
    >>> t = irsa.query_gator_cone('fp_psc', 'm31', 10.)
    >>> print t
       ra     dec       clon         clat     err_maj err_min ...   angle     j_h   h_k    j_k   id
    ------- ------- ------------ ------------ ------- ------- ... ---------- ----- ------ ----- ---
    10.6833 41.2675 00h42m43.98s 41d16m02.84s    0.13    0.12 ... 215.586031   nan    nan   nan   0
    10.6842 41.2669 00h42m44.20s 41d16m00.99s    0.13    0.12 ... 192.209291   nan    nan   nan   1
     10.684 41.2709 00h42m44.17s 41d16m15.24s    0.13    0.12 ... 342.740902   nan    nan   nan   2
    10.6839 41.2667 00h42m44.15s 41d16m00.06s    0.13    0.12 ... 194.971035   nan    nan   nan   3
    10.6868 41.2707 00h42m44.84s 41d16m14.57s    0.13    0.11 ...  43.053601   nan    nan   nan   4
    10.6824 41.2679 00h42m43.77s 41d16m04.53s     0.1    0.09 ... 237.898243 0.693    nan   nan   5


Reference/API
=============

.. automodapi:: astrodata.irsa
    :no-inheritance-diagram:
