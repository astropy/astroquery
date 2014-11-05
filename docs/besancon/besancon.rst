.. doctest-skip-all
.. _astroquery.besancon:

*****************************************
Besancon Queries (`astroquery.besancon`)
*****************************************

Getting started
===============

The following example illustrates an Besancon catalog/image query.  The API describes the
relevant keyword arguments (of which there are many) 

.. note::
   These examples are improperly formatted because they are not safe to run
   generally!  The Besancon servers are hosted by individuals and not mean to
   handle large or repeated requests, so we disable *all* automated testing.

A successful run should look something like this

.. code-block:: python

    >>> from astroquery.besancon import Besancon
    >>> #besancon_model = Besancon.query(glon=10.5, glat=0.0, email='your@email.net')

    Waiting 30s for model to finish (elapsed wait time 30s, total 32)
    Loading page...
    Waiting 30s for model to finish (elapsed wait time 60s, total 198)
    Loading page...
    Waiting 30s for model to finish (elapsed wait time 90s, total 362)
    Loading page...
    Waiting 30s for model to finish (elapsed wait time 120s, total 456)
    Loading page...
    Awaiting Besancon file...
    Downloading ftp://sasftp.obs-besancon.fr/modele/modele2003/1407398212.212272.resu
    |========================================================================================================================================| 2.5M/2.5M (100.00%)         0s

    >>> # B.pprint()
     Dist  Mv   CL Typ   LTef logg Age Mass  J-K   J-H   V-K    H-K    K    [Fe/H]   l     b     Av   Mbol 
    ----- ---- --- ---- ----- ---- --- ---- ----- ----- ------ ----- ------ ------ ----- ----- ----- ------
     0.87 12.5   5  7.5 3.515 4.99   5 0.24 0.966 0.649  5.408 0.318  17.44  -0.02 10.62 -0.38 0.637 10.844
     0.91 13.0   5  7.5 3.506 5.03   1 0.21 0.976 0.671  5.805 0.305 17.726   0.13 10.62 -0.38 0.669 11.312
     0.97 18.5   5  7.9  3.39 5.32   7 0.08 0.804 0.634  8.634  0.17 20.518  -0.46 10.62 -0.38 0.716    0.0
     1.01 15.2   5  7.9 3.465 5.14   1 0.13 1.045 0.649  7.015 0.396 18.957   0.22 10.62 -0.38 0.748 13.353
     1.01 16.5   5  7.8 3.435 5.27   5 0.09 1.024 0.701  7.545 0.323 19.642  -0.09 10.62 -0.38 0.748    0.0
     1.03 17.0   5 7.85 3.424 5.29   1 0.09 1.133 0.701  8.132 0.432 19.631   0.07 10.62 -0.38 0.764    0.0
     1.09 13.5   5  7.6 3.497 5.05   7 0.18 0.995  0.69  5.829 0.305 18.629  -0.43 10.62 -0.38 0.812  11.78
     1.17 13.7   5 7.65 3.493  5.0   2 0.17 1.025  0.68  6.319 0.345 18.552    0.2 10.62 -0.38 0.876 11.948
     1.17 18.5   5  7.9  3.39 5.32   5 0.08 0.927  0.69  8.876 0.237 20.763  -0.27 10.62 -0.38 0.876    0.0
     1.25 20.0   5  7.9 3.353 5.36   3 0.08 1.533 0.883 10.202  0.65 21.215   0.15 10.62 -0.38 0.941    0.0
     1.29  9.3   5  7.1  3.58 4.74   2 0.56 0.997 0.777  4.592 0.219 16.263   0.21 10.62 -0.38 0.974  7.834
     1.29 13.5   6  9.0 3.853  8.0   7  0.6 0.349 0.283  1.779 0.066 23.266  -0.17 10.62 -0.38 0.974    0.0
     1.33  6.9   5  6.4 3.656 4.62   5 0.77 0.857  0.69  3.604 0.167 14.889   0.25 10.62 -0.38 1.006  5.795
     1.35  7.5   5  6.5 3.633 4.62   5  0.7 0.902 0.729  3.885 0.172  15.22   0.08 10.62 -0.38 1.023  6.225
      ...  ... ...  ...   ...  ... ...  ...   ...   ...    ...   ...    ...    ...   ...   ...   ...    ...
    40.19 17.1   6  9.0 3.515 8.19   9  0.7 2.013 1.481 11.166 0.532 35.816  -1.99 10.62 -0.38  11.8    0.0
    41.01 17.1   6  9.0 3.515 8.19   9  0.7 2.013 1.481 11.166 0.532 35.899  -2.14 10.62 -0.38  11.8    0.0
    41.21 17.3   6  9.0 3.485 8.19   9  0.7 1.933 1.471 10.826 0.462 36.312  -1.36 10.62 -0.38  11.8    0.0
    41.41 16.9   6  9.0 3.542 8.19   9  0.7 1.893 1.301 11.436 0.592 35.358  -0.92 10.62 -0.38  11.8    0.0
    41.87 16.7   6  9.0 3.568 8.19   9  0.7 1.783 1.141 11.686 0.642 34.917  -1.79 10.62 -0.38  11.8    0.0
    42.05 16.7   6  9.0 3.568 8.19   9  0.7 1.783 1.141 11.686 0.642 34.936  -2.06 10.62 -0.38  11.8    0.0
    44.19 16.9   6  9.0 3.542 8.19   9  0.7 1.893 1.301 11.436 0.592 35.494  -3.04 10.62 -0.38  11.8    0.0
    45.39 17.3   6  9.0 3.485 8.19   9  0.7 1.933 1.471 10.826 0.462 36.497  -1.28 10.62 -0.38  11.8    0.0
    46.01 18.5   6  9.0 3.297 8.19   9  0.7 0.813 1.381  8.016 0.568 40.611  -2.01 10.62 -0.38  11.8    0.0
    46.71 16.7   6  9.0 3.568 8.19   9  0.7 1.783 1.141 11.686 0.642 35.087  -2.59 10.62 -0.38  11.8    0.0
    46.97 17.9   6  9.0 3.389 8.19   9  0.7 1.233 1.161  9.536 0.072 38.563  -1.42 10.62 -0.38  11.8    0.0
    47.45 17.3   6  9.0 3.485 8.19   9  0.7 1.933 1.471 10.826 0.462 36.579  -2.25 10.62 -0.38  11.8    0.0
    48.05  5.2   5 4.82 3.786 4.54   9 0.74  2.42 1.563 11.919 0.857 23.548  -1.45 10.62 -0.38  11.8   5.08
    49.39 16.9   6  9.0 3.542 8.19   9  0.7 1.893 1.301 11.436 0.592 35.813  -1.19 10.62 -0.38  11.8    0.0
    
.. note::
    These tests are commented out (and will fail) because I don't want to put
    unnecessary strain on the Besancon servers by running queries every time we
    test.

Reading a previously downloaded file
------------------------------------

If you've downloaded a ``.resu``, you can parse it with the custom parser in astroquery:

.. code-block:: python

   >>> from astroquery.besancon import parse_besancon_model_file
   >>> tbl = parse_besancon_model_file('file.resu')
   >>> tbl.pprint()
     Dist   Mv   CL Typ  LTef logg Age Mass  J-H   H-K   J-K   V-K    V    [Fe/H]   l     b     Av   Mbol
    ------ ---- --- --- ----- ---- --- ---- ----- ----- ----- ----- ------ ------ ----- ----- ----- ------
     0.091 10.2   5 7.2 3.559 4.85   7 0.48 0.601 0.223 0.824 4.175 15.133   0.02 10.62 -0.38 0.056  8.671


Reference/API
=============

.. automodapi:: astroquery.besancon
    :no-inheritance-diagram:
