*************************************
Catalogues - Query for Catalogue Data
*************************************

In addition to raw and reduced observations, the ESO archive provides access to
science catalogues. This section shows how to
list the available catalogues and query one of them.

Available Catalogues
====================

You can list the available catalogues with :meth:`~astroquery.eso.EsoClass.list_catalogues`. By default,
the ``all_versions=False`` option returns only the latest version of each
catalogue.

.. doctest-skip::

    >>> from astroquery.eso import Eso
    >>> eso = Eso()

    >>> eso.list_catalogues(all_versions=False)
    ['AMBRE_V1',
     'ATLASGAL_V1',
     'COSMOS2015_Laigle_v1_1b_latestV7_fits_V1',
     'EREBOS_cat_fits_V1',
     'EREBOS_RV_cat_fits_V1',
     ...
     'KiDS_DR3_0_ugri_src_fits_V2',
     'KiDS_DR3_1_ugri_shear_fits_V1',
     'KiDS_DR4_1_ugriZYJHKs_cat_fits',
     ...
     'vmc_dr7_yjks_back_V1',
     'vmc_dr7_yjks_varCat_V3']

    >>> print(len(eso.list_catalogues(all_versions=False)))
    86

To include every available version of every catalogue, set
``all_versions=True``:

.. doctest-skip::

    >>> eso.list_catalogues(all_versions=True)
    ['AMBRE_V1',
     'atlas_er3_ugriz_catMetaData_fits_V2',
     'ATLASGAL_V1',
     'COSMOS2015_Laigle_v1_1b_latestV7_fits_V1',
     'EREBOS_cat_fits_V1',
     'EREBOS_RV_cat_fits_V1',
     ...
     'KiDS_DR3_0_ugri_src_fits_V2',
     'KiDS_DR3_1_ugri_shear_fits_V1',
     'KiDS_DR4_1_ugriZYJHKs_cat_fits',
     ...
     'vmc_dr7_yjks_back_V1',
     'vmc_dr7_yjks_varCat_V3']

    >>> print(len(eso.list_catalogues(all_versions=True)))
    129

Available Query Constraints
===========================

Before querying a specific catalogue, inspect its schema with
``eso.query_catalogue(..., help=True)``. This prints the available columns and
the total number of records in that table -- in this case the ``'KiDS_DR4_1_ugriZYJHKs_cat_fits'`` 
table. To see more infomation on this specific version of the Kilo-Degree Survey (KiDS) catalogue, see the 
`release documentation <https://www.eso.org/rm/api/v1/public/releaseDescriptions/229>`_.*

.. doctest-skip::

    >>> eso.query_catalogue(catalogue='KiDS_DR4_1_ugriZYJHKs_cat_fits', help=True)
    INFO:
    Columns present in the table safcat.KiDS_DR4_1_ugriZYJHKs_cat_fits:
        column_name     datatype       unit                        ucd
    ------------------- -------- ---------------- -------------------------------------
                     ID     CHAR                                      meta.id;meta.main
              KIDS_TILE     CHAR                                                meta.id
             THELI_NAME     CHAR                                                meta.id
                  SeqNr  INTEGER                                                meta.id
                   SLID  INTEGER                                                meta.id
                    SID  INTEGER                                                meta.id
              FLUX_AUTO     REAL            count                    phot.flux;em.opt.R
           FLUXERR_AUTO     REAL            count         stat.error;phot.flux;em.opt.R
               MAG_AUTO     REAL              mag                     phot.mag;em.opt.R
                   ...
                   MASK  INTEGER                                              meta.code
        COLOUR_GAAP_u_g     REAL              mag phot.color.reddFree;em.opt.U;em.opt.B
        COLOUR_GAAP_g_r     REAL              mag phot.color.reddFree;em.opt.B;em.opt.R
        COLOUR_GAAP_r_i     REAL              mag phot.color.reddFree;em.opt.R;em.opt.I
        COLOUR_GAAP_i_Z     REAL              mag          phot.color.reddFree;em.opt.I
        COLOUR_GAAP_Z_Y     REAL              mag  phot.color.reddFree;em.opt.I;em.IR.J
        COLOUR_GAAP_Y_J     REAL              mag           phot.color.reddFree;em.IR.J
        COLOUR_GAAP_J_H     REAL              mag   phot.color.reddFree;em.IR.J;em.IR.H
       COLOUR_GAAP_H_Ks     REAL              mag   phot.color.reddFree;em.IR.H;em.IR.K
    Number of records present in the table safcat.KiDS_DR4_1_ugriZYJHKs_cat_fits:
    100350804
    [astroquery.eso.core]

.. tip:: 
    
    As an exmple, making use of the TAP free query command, :meth:`~astroquery.eso.EsoClass.query_tap`, 
    you can also retrieve the documentation URL for every available catalogue with a query like:

    .. doctest-skip::

        >>> query = """
        ... SELECT table_name, cat_id, rel_descr_url
        ... FROM TAP_SCHEMA.tables
        ... WHERE schema_name = 'safcat' AND cat_id IS NOT NULL
        ... ORDER BY cat_id
        ... """
        >>> tbl = eso.query_tap(query, which_tap="tap_cat")
        >>> print(tbl[:5])
        table_name       cat_id                  release_documentation_url                 
        ---------------- ------ -----------------------------------------------------------
        AMBRE_V1             13 https://www.eso.org/rm/api/v1/public/releaseDescriptions/7
        GOODS_FORS2_V1       31 https://www.eso.org/rm/api/v1/public/releaseDescriptions/37
        HUGS_GOODSS_K_V1     32 https://www.eso.org/rm/api/v1/public/releaseDescriptions/48
        HUGS_UDS_K_V1        33 https://www.eso.org/rm/api/v1/public/releaseDescriptions/49
        HUGS_UDS_Y_V1        34 https://www.eso.org/rm/api/v1/public/releaseDescriptions/50

Query with Constraints
======================

The table can be queried using the :meth:`~astroquery.eso.EsoClass.query_catalogue` method.
Note, however, that catalogue tables can be very large, so it is often useful to start with a
small row limit, which can be set with e.g ``eso.ROW_LIMIT = 5`` or by passing
e.g. ``ROW_LIMIT=5`` to the query method: 

.. doctest-skip::

    >>> table = eso.query_catalogue(catalogue='KiDS_DR4_1_ugriZYJHKs_cat_fits', ROW_LIMIT=5)
    >>> table
    WARNING: MaxResultsWarning: Results truncated to 5. To retrieve all the records set to None the ROW_LIMIT attribute [astroquery.eso.core]
    <Table length=5>
      Level    ALPHA_J2000      A_IMAGE         A_WORLD    ... Z_B_MAX      Z_B_MIN              Z_ML
      count        deg           pixel            deg      ...
     float32     float64        float64         float32    ... float64      float64            float64
    ---------- ----------- ------------------ ------------ ... ------- ------------------ ------------------
    0.03316526    5.079035           1.023542 6.084906e-05 ...    0.97 0.6699999999999999 0.7799999999999999
    0.03316413    5.127818           2.087884 0.0001240919 ...    0.92 0.7899999999999999 0.8300000000000001
    0.03320557    5.171088 2.6607149999999997   0.00015816 ...    0.89 0.7899999999999999 0.8600000000000001
    0.02512704    5.912251         201.661499    0.0119862 ...    0.04               0.01               0.01
    0.04201349    6.206854           3.289606 0.0001955687 ...    0.35               0.23               0.27

A larger number of rows can be returned by setting a higher row limit, or by disabling truncation
with ``eso.ROW_LIMIT = -1`` (``=0`` or ``=None``). Be aware that the TAP service has a maximum limit of 15,000,000 rows
per query, so setting ``eso.ROW_LIMIT = -1`` (``=0`` or ``=None``) will return all matching results up to that TAP limit.

You can also combine selected columns with ADQL filters in ``column_filters``.
For example, to retrieve bright sources with r-band magnitude of ``MAG_AUTO < 10``, and only return a subset of
the available columns, you can do:

.. doctest-skip::

    >>> table = eso.query_catalogue(
    ...     catalogue='KiDS_DR4_1_ugriZYJHKs_cat_fits',
    ...     columns=["ID", "RAJ2000", "DECJ2000", "KIDS_TILE", "MAG_AUTO", "MAGERR_AUTO"],
    ...     column_filters={"MAG_AUTO": "<10"}
    ... )
    >>> table
    <Table length=38>
                  ID                   RAJ2000             DECJ2000      ... MAG_AUTO MAGERR_AUTO
                                         deg                 deg         ...   mag        mag
                object                 float64             float64       ... float32    float32
    ----------------------------- ------------------ ------------------- ... -------- ------------
    KiDSDR4 J092035.791+001110.92          140.14913            0.186369 ... 9.263525 3.264208e-05
    KiDSDR4 J110654.466+015628.34         166.726944            1.941208 ... 9.844576 4.391666e-05
    KiDSDR4 J225722.767-293856.66 344.34486300000003          -29.649074 ... 9.725844 0.0001094358
    ...
    KiDSDR4 J223130.214-322011.16         337.875892          -32.336436 ... 9.379268 2.736172e-05
    KiDSDR4 J223131.492-322022.97         337.881217          -32.339715 ... 9.846291  3.40929e-05
    KiDSDR4 J032045.699-263559.19          50.190415          -26.599775 ... 9.857556 3.780224e-05