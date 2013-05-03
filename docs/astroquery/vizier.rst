.. _astroquery.vizier:

*****************************************
VizieR Queries (`astroquery.vizier`)
*****************************************

Getting started
===============

The following example illustrates a VizieR query of the Veron & Cetty catalogue

.. code-block:: python

    >>> from astroquery import vizier
    >>> query = {}
    >>> query["-source"] = "VII/258/vv10"
    >>> query["-out"] = ["Name", "Sp", "Vmag"]
    >>> query["Vmag"] = "5.0..11.0"
    >>> table1 = vizier.vizquery(query)
    WARNING: W27: None:29:2: W27: COOSYS deprecated in VOTable 1.2 [astropy.io.vo.exceptions]
    >>> print(table1)
    _RAJ2000 _DEJ2000      Name      Sp   Vmag
    -------- -------- ------------- ---- -----
     10.6846  41.2694          M 31   S2 10.57
     60.2779 -16.1108 NPM1G-16.0168      10.16
    103.7917  41.0028 NPM1G+41.0135   S?  9.37
     27.2387   5.9067      NGC  676   S2  10.5
     40.6696  -0.0131      NGC 1068  S1h 10.83
    139.7596  26.2697      NGC 2824   S? 10.88
    147.5921  72.2792      NGC 2985 S1.9 10.61
    169.5687 -32.8142      NGC 3621   S2   9.4
    173.1442  53.0678      NGC 3718  S3b 10.61
    184.9608  29.6139     UGC  7377   S3 10.47
    185.0287  29.2808      NGC 4278  S3b 10.87
    186.4537  33.5467      NGC 4395 S1.8 10.27
    189.9971 -11.6231      NGC 4594   S3  9.25
    192.7196  41.1194      NGC 4736    S 10.85
    208.3612  40.2831      NGC 5353   S? 10.91

The resulting "table1" can be reused as an input for another search, here in 2MASS

.. code-block:: python

    >>> query = {}
    >>> query["-source"] = "II/246/out"
    >>> query["-out"] = ["RAJ2000", "DEJ2000", "2MASS", "Kmag"]
    >>> query["-c.rs"] = "2"
    >>> query["-c"] = table1
    >>> table2 = vizquery(query)
    WARNING: W27: None:32:2: W27: COOSYS deprecated in VOTable 1.2 [astropy.io.vo.exceptions]
    WARNING: W03: None:64:4: W03: Implictly generating an ID from a name '2MASS' -> '_2MASS' [astropy.io.vo.exceptions]
    >>> print(table2)
     _q  _RAJ2000   _DEJ2000   RAJ2000    DEJ2000        2MASS        Kmag 
    --- ---------- ---------- ---------- ---------- ---------------- ------
      1  10.684737  41.269035  10.684737  41.269035 00424433+4116085  8.475
      2   60.27763 -16.110863   60.27763 -16.110863 04010663-1606391 12.176
      3 103.791864  41.002831 103.791864  41.002831 06551004+4100101 11.625
      5  40.669613  -0.013339  40.669613  -0.013339 02424070-0000480  7.271
      6 139.759322  26.270023 139.759322  26.270023 09190223+2616120 11.115
      7 147.592456  72.278999 147.592456  72.278999 09502218+7216443  9.792
      8 169.568732 -32.814068 169.568732 -32.814068 11181649-3248506 12.604
     11 185.028409  29.280706 185.028409  29.280706 12200681+2916505 10.049
     12  186.45358  33.546852  186.45358  33.546852 12254885+3332486 14.138
     13 189.997638 -11.622945 189.997638 -11.622945 12395943-1137226  8.573
     15 208.361284  40.283085 208.361284  40.283085 13532670+4016591 10.047

Note: In the result above, column "_q" of "table2" is a 1-based index referencing "table1".


Reference/API
=============

.. automodapi:: astroquery.vizier
    :no-inheritance-diagram:
