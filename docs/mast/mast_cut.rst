
*************
Image Cutouts
*************

TESSCut
=======

TESSCut is MAST's tool to provide full-frame image (FFI) cutouts from the Transiting
Exoplanet Survey Satellite (TESS). The cutouts can be made from either the Science
Processing Operation's Center (`SPOC <https://archive.stsci.edu/missions-and-data/tess>`__) FFI products,
or the TESS Image CAlibrator (`TICA <https://archive.stsci.edu/hlsp/tica>`__) high-level science products.
Cutouts from the TICA products are not available for sectors 1-26,
but are available for sector 27 onwards. These products are available up to 3 weeks sooner than
their SPOC counterparts for the latest sector, so it is recommended to request TICA cutouts
for users working with time-sensitive observations. The cutouts from either SPOC or TICA products
are returned in the form of target pixel files that follow the same format as TESS pipeline target
pixel files. This tool can be accessed in Astroquery by using the Tesscut class.

**Note:** TESScut limits each user to no more than 10 simultaneous calls to the service.
After the user has reached this limit TESScut will return a
``503 Service Temporarily Unavailable Error``.

**Note:** The moving targets functionality does not currently support making cutouts from
TICA products, so the product argument will always default to SPOC.

If you use TESSCut for your work, please cite Brasseur et al. 2019
https://ui.adsabs.harvard.edu/abs/2019ascl.soft05007B/abstract


Cutouts
-------

The `~astroquery.mast.TesscutClass.get_cutouts` function takes a product type
("TICA" or "SPOC", but defaults to "SPOC"), coordinate, object name (e.g. "M104" or "TIC 32449963"),
or moving target (e.g. "Eleonora") and cutout size (in pixels or an angular quantity, default is 5 pixels)
and returns the cutout target pixel file(s) as a list of `~astropy.io.fits.HDUList` objects.

If the given coordinate/object location appears in more than one TESS sector a target pixel
file will be produced for each sector.  If the cutout area overlaps more than one camera or
ccd a target pixel file will be produced for each one.

Requesting a cutout by coordinate or objectname accesses the
`MAST TESScut API <https://mast.stsci.edu/tesscut/docs/getting_started.html#requesting-a-cutout>`__
and returns a target pixel file, with format described
`here <https://astrocut.readthedocs.io/en/latest/astrocut/file_formats.html#target-pixel-files>`__.
Note that the product argument will default to request for SPOC cutouts when
not explicitly called for TICA.

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> cutout_coord = SkyCoord(107.18696, -70.50919, unit="deg")
   >>> hdulist = Tesscut.get_cutouts(coordinates=cutout_coord, sector=33)
   >>> hdulist[0].info()  # doctest: +IGNORE_OUTPUT
   Filename: <class '_io.BytesIO'>
   No.    Name      Ver    Type      Cards   Dimensions   Format
   0  PRIMARY       1 PrimaryHDU      57   ()
   1  PIXELS        1 BinTableHDU    281   3495R x 12C   [D, E, J, 25J, 25E, 25E, 25E, 25E, J, E, E, 38A]
   2  APERTURE      1 ImageHDU        82   (5, 5)   int32


For users with time-sensitive targets who would like cutouts from the latest observations,
we recommend requesting for the TICA product. Using the same target from the example above,
this example shows a request for TICA cutouts:

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> cutout_coord = SkyCoord(107.18696, -70.50919, unit="deg")
   >>> hdulist = Tesscut.get_cutouts(coordinates=cutout_coord,
   ...                               product='tica',
   ...                               sector=28)
   >>> hdulist[0][0].header['FFI_TYPE']  # doctest: +IGNORE_OUTPUT
   'TICA'

The following example will request SPOC cutouts using the objectname argument, rather
than a set of coordinates.

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   ...
   >>> hdulist = Tesscut.get_cutouts(objectname="TIC 32449963", sector=37)
   >>> hdulist[0].info()  # doctest: +IGNORE_OUTPUT
   Filename: <class '_io.BytesIO'>
   No.    Name      Ver    Type      Cards   Dimensions   Format
     0  PRIMARY       1 PrimaryHDU      56   ()
     1  PIXELS        1 BinTableHDU    280   3477R x 12C   [D, E, J, 25J, 25E, 25E, 25E, 25E, J, E, E, 38A]
     2  APERTURE      1 ImageHDU        81   (5, 5)   int32


Requesting a cutout by moving_target accesses the
`MAST Moving Target TESScut API <https://mast.stsci.edu/tesscut/docs/getting_started.html#moving-target-cutouts>`__
and returns a target pixel file, with format described
`here <https://astrocut.readthedocs.io/en/latest/astrocut/file_formats.html#path-focused-target-pixel-files>`__.
The moving_target is an optional bool argument where `True` signifies that the accompanying ``objectname``
input is the object name or ID understood by the
`JPL Horizon ephemerades interface <https://ssd.jpl.nasa.gov/horizons/app.html>`__.
The default value for moving_target is set to False. Therefore, a non-moving target can be input
simply with either the objectname or coordinates.

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   ...
   >>> hdulist = Tesscut.get_cutouts(objectname="Eleonora",
   ...                               moving_target=True,
   ...                               sector=6)
   >>> hdulist[0].info()  # doctest: +IGNORE_OUTPUT
   Filename: <class '_io.BytesIO'>
   No.    Name      Ver    Type      Cards   Dimensions   Format
     0  PRIMARY       1 PrimaryHDU      54   ()
     1  PIXELS        1 BinTableHDU    150   355R x 16C   [D, E, J, 25J, 25E, 25E, 25E, 25E, J, E, E, 38A, D, D, D, D]
     2  APERTURE      1 ImageHDU        97   (2136, 2078)   int32

Note that the moving targets functionality does not currently support TICA, so the product
parameter will result in an error when set to 'TICA'.

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   ...
   >>> hdulist = Tesscut.get_cutouts(objectname="Eleonora",
   ...                               product='tica',
   ...                               moving_target=True,
   ...                               sector=6)
   Traceback (most recent call last):
   ...
   astroquery.exceptions.InvalidQueryError: Only SPOC is available for moving targets queries.

The `~astroquery.mast.TesscutClass.download_cutouts` function takes a product type ("TICA" or "SPOC", but defaults to "SPOC"),
coordinate, cutout size (in pixels or an angular quantity), or object name (e.g. "M104" or "TIC 32449963") and moving target
(True or False). It uses these parameters to download the cutout target pixel file(s).

If a given coordinate/object/moving target appears in more than one TESS sector, a target pixel file
will be produced for each sector.  If the cutout area overlaps more than one camera or ccd, a target
pixel file will be produced for each one.

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   >>> from astropy.coordinates import SkyCoord
   >>> import astropy.units as u
   ...
   >>> cutout_coord = SkyCoord(107.18696, -70.50919, unit="deg")
   >>> manifest = Tesscut.download_cutouts(coordinates=cutout_coord,
   ...                                     size=[5, 5]*u.arcmin,
   ...                                     sector=9) # doctest: +IGNORE_OUTPUT
   Downloading URL https://mast.stsci.edu/tesscut/api/v0.1/astrocut?ra=107.18696&dec=-70.50919&y=0.08333333333333333&x=0.11666666666666667&units=d&sector=9 to ./tesscut_20210716150026.zip ... [Done]
   >>> print(manifest)  # doctest: +IGNORE_OUTPUT
                        Local Path
   ----------------------------------------------------------
   ./tess-s0009-4-1_107.186960_-70.509190_15x15_astrocut.fits

The query from the example above defaults to downloading cutouts from SPOC. The following example is a query for
the same target from above, but with the product argument passed as TICA to explicitly request for TICA cutouts,
and because the TICA products are not available for sectors 1-26, we request cutouts from sector 27 rather than sector 9.

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   >>> from astropy.coordinates import SkyCoord
   >>> import astropy.units as u
   ...
   >>> cutout_coord = SkyCoord(107.18696, -70.50919, unit="deg")
   >>> manifest = Tesscut.download_cutouts(coordinates=cutout_coord,
   ...                                     product='tica',
   ...                                     size=[5, 7]*u.arcmin,
   ...                                     sector=27) # doctest: +IGNORE_OUTPUT
   Downloading URL https://mast.stsci.edu/tesscut/api/v0.1/astrocut?ra=107.18696&dec=-70.50919&y=0.08333333333333333&x=0.11666666666666667&units=d&product=TICA&sector=27 to ./tesscut_20230214150644.zip ... [Done]
   >>> print(manifest)  # doctest: +IGNORE_OUTPUT
                        Local Path
   ----------------------------------------------------------
   ./tica-s0027-4-2_107.186960_-70.509190_21x14_astrocut.fits

Sector information
------------------

To access sector information for a particular coordinate, object, or moving target there is
`~astroquery.mast.TesscutClass.get_sectors`.

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> coord = SkyCoord(135.1408, -5.1915, unit="deg")
   >>> sector_table = Tesscut.get_sectors(coordinates=coord)
   >>> print(sector_table)   # doctest: +IGNORE_OUTPUT
     sectorName   sector camera ccd
   -------------- ------ ------ ---
   tess-s0008-1-1      8      1   1
   tess-s0034-1-2     34      1   2

Note that because of the delivery cadence of the
TICA high level science products, later sectors will be available sooner with TICA than with
SPOC. Also note that TICA is not available for sectors 1-26. The following example is the same
query as above, but for TICA. Notice that products for sector 8 are no longer available,
but are now available for sector 61.

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> coord = SkyCoord(135.1408, -5.1915, unit="deg")
   >>> sector_table = Tesscut.get_sectors(coordinates=coord, product='tica')
   >>> print(sector_table)   # doctest: +IGNORE_OUTPUT
     sectorName   sector camera ccd
   -------------- ------ ------ ---
   tica-s0034-1-2     34      1   2
   tica-s0061-1-2     61      1   2

The following example will request SPOC cutouts using the objectname argument, rather
than a set of coordinates.

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   ...
   >>> sector_table = Tesscut.get_sectors(objectname="TIC 32449963")
   >>> print(sector_table)     # doctest: +IGNORE_OUTPUT
     sectorName   sector camera ccd
   -------------- ------ ------ ---
   tess-s0010-1-4     10      1   4

The following example requests SPOC cutouts for a moving target.

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   ...
   >>> sector_table = Tesscut.get_sectors(objectname="Ceres", moving_target=True)
   >>> print(sector_table)
     sectorName   sector camera ccd
   -------------- ------ ------ ---
   tess-s0029-1-4     29      1   4
   tess-s0043-3-3     43      3   3
   tess-s0044-2-4     44      2   4

Note that the moving targets functionality is not currently available for TICA,
so the query will always default to SPOC.


Zcut
====


Zcut for MAST allows users to request cutouts from various Hubble deep field surveys. The cutouts can
be returned as either fits or image files (jpg and png are supported). This tool can be accessed in
Astroquery by using the Zcut class. The list of supported deep field surveys can be found here:
https://mast.stsci.edu/zcut/


Cutouts
-------

The `~astroquery.mast.ZcutClass.get_cutouts` function takes a coordinate and cutout size (in pixels or
an angular quantity) and returns the cutout FITS file(s) as a list of ~astropy.io.fits.HDUList objects.

If the given coordinate appears in more than one Zcut survey, a FITS file will be produced for each survey.

.. doctest-remote-data::

   >>> from astroquery.mast import Zcut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> cutout_coord = SkyCoord(189.49206, 62.20615, unit="deg")
   >>> hdulist = Zcut.get_cutouts(coordinates=cutout_coord, survey='3dhst_goods-n')
   >>> hdulist[0].info()    # doctest: +IGNORE_OUTPUT
   Filename: <class '_io.BytesIO'>
   No.    Name      Ver    Type      Cards   Dimensions   Format
   0  PRIMARY       1 PrimaryHDU      11   ()
   1  CUTOUT        1 ImageHDU       177   (5, 5)   float32
   2  CUTOUT        1 ImageHDU       177   (5, 5)   float32
   3  CUTOUT        1 ImageHDU       177   (5, 5)   float32


The `~astroquery.mast.ZcutClass.download_cutouts` function takes a coordinate and cutout size (in pixels or
an angular quantity) and downloads the cutout fits file(s) as either fits files or image (png/jpg)
files.

If a given coordinate appears in more than one Zcut survey, a cutout will be produced for each survey.

.. doctest-remote-data::

   >>> from astroquery.mast import Zcut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> cutout_coord = SkyCoord(189.49206, 62.20615, unit="deg")
   >>> manifest = Zcut.download_cutouts(coordinates=cutout_coord,
   ...                                  size=[5, 10],
   ...                                  units="px",
   ...                                  survey="3dhst_goods-n")  # doctest: +IGNORE_OUTPUT
   Downloading URL https://mast.stsci.edu/zcut/api/v0.1/astrocut?ra=189.49206&dec=62.20615&y=200&x=300&units=px&format=fits to ./zcut_20210125155545.zip ... [Done]
   Inflating...
   ...
   >>> print(manifest)    # doctest: +IGNORE_OUTPUT
                                 Local Path
   -------------------------------------------------------------------------
   ./candels_gn_30mas_189.492060_62.206150_300.0pix-x-200.0pix_astrocut.fits
   >>> manifest = Zcut.download_cutouts(coordinates=cutout_coord,
   ...                                  size=[5, 10],
   ...                                  units="px",
   ...                                  survey="3dhst_goods-n",
   ...                                  cutout_format="jpg")  # doctest: +IGNORE_OUTPUT
   Downloading URL https://mast.stsci.edu/zcut/api/v0.1/astrocut?ra=189.49206&dec=62.20615&y=200&x=300&units=px&format=jpg to ./zcut_20201202132453.zip ... [Done]
   ...
   >>> print(manifest)
                                                  Local Path                                              
   -------------------------------------------------------------------------------------------------------
      ./hlsp_3dhst_spitzer_irac_goods-n_irac1_v4.0_sc_189.492060_62.206150_10.0pix-x-5.0pix_astrocut_0.jpg
   ./hlsp_3dhst_spitzer_irac_goods-n-s2_irac3_v4.0_sc_189.492060_62.206150_10.0pix-x-5.0pix_astrocut_0.jpg
   ./hlsp_3dhst_spitzer_irac_goods-n-s1_irac4_v4.0_sc_189.492060_62.206150_10.0pix-x-5.0pix_astrocut_0.jpg
      ./hlsp_3dhst_spitzer_irac_goods-n_irac2_v4.0_sc_189.492060_62.206150_10.0pix-x-5.0pix_astrocut_0.jpg
         ./hlsp_3dhst_mayall_mosaic_goods-n_u_v4.0_sc_189.492060_62.206150_10.0pix-x-5.0pix_astrocut_0.jpg
    ./hlsp_3dhst_subaru_suprimecam_goods-n_rc_v4.0_sc_189.492060_62.206150_10.0pix-x-5.0pix_astrocut_0.jpg
     ./hlsp_3dhst_subaru_suprimecam_goods-n_v_v4.0_sc_189.492060_62.206150_10.0pix-x-5.0pix_astrocut_0.jpg
    ./hlsp_3dhst_subaru_suprimecam_goods-n_ic_v4.0_sc_189.492060_62.206150_10.0pix-x-5.0pix_astrocut_0.jpg
    ./hlsp_3dhst_subaru_suprimecam_goods-n_zp_v4.0_sc_189.492060_62.206150_10.0pix-x-5.0pix_astrocut_0.jpg
     ./hlsp_3dhst_subaru_suprimecam_goods-n_b_v4.0_sc_189.492060_62.206150_10.0pix-x-5.0pix_astrocut_0.jpg


Survey information
------------------

To list the available deep field surveys at a particular location there is `~astroquery.mast.ZcutClass.get_surveys`.

.. doctest-remote-data::

   >>> from astroquery.mast import Zcut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> coord = SkyCoord(189.49206, 62.20615, unit="deg")
   >>> survey_list = Zcut.get_surveys(coordinates=coord)
   >>> print(survey_list)    # doctest: +IGNORE_OUTPUT
   ['candels_gn_60mas', 'candels_gn_30mas', 'goods_north']


HAPCut
======


HAPCut for MAST allows users to request cutouts from various Hubble Advance Products (HAPs). The cutouts can
be returned as fits files (image files are not currently supported). This tool can be accessed in
Astroquery by using the Hapcut class. Documentation for the supported HAPCut API can be found here:
https://mast.stsci.edu/hapcut/


Cutouts
-------

The `~astroquery.mast.HapcutClass.get_cutouts` function takes a coordinate and cutout size (in pixels or
an angular quantity) and returns the cutout FITS file(s) as a list of `~astropy.io.fits.HDUList` objects.

If the given coordinate appears in more than one product, a FITS file will be produced for each.

.. doctest-remote-data::

   >>> from astroquery.mast import Hapcut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> cutout_coord = SkyCoord(351.347812, 28.497808, unit="deg")
   >>> hdulist = Hapcut.get_cutouts(coordinates=cutout_coord, size=5)
   >>> hdulist[0].info()    # doctest: +IGNORE_OUTPUT
   Filename: <class '_io.BytesIO'>
   No.    Name      Ver    Type      Cards   Dimensions   Format
   0  PRIMARY       1 PrimaryHDU     754   ()
   1  SCI           1 ImageHDU       102   (5, 5)   float32
   2  WHT           1 ImageHDU        56   (5, 5)   float32


The `~astroquery.mast.HapcutClass.download_cutouts` function takes a coordinate and cutout size (in pixels or
an angular quantity) and downloads the cutout fits file(s) as fits files.

If the given coordinate appears in more than one product, a cutout will be produced for each.

.. doctest-remote-data::

   >>> from astroquery.mast import Hapcut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> cutout_coord = SkyCoord(351.347812, 28.497808, unit="deg")
   >>> manifest = Hapcut.download_cutouts(coordinates=cutout_coord, size=[50, 100])    # doctest: +IGNORE_OUTPUT
   Downloading URL https://mast.stsci.edu/hapcut/api/v0.1/astrocut?ra=351.347812&dec=28.497808&x=100&y=50&units=px to ./hapcut_20221130112710.zip ... [Done]
   Inflating...
   ...
   >>> print(manifest)    # doctest: +IGNORE_OUTPUT
                                 Local Path
   ---------------------------------------------------------------------------------
   ./hst_cutout_skycell-p2007x09y05-ra351d3478-decn28d4978_wfc3_ir_f160w_coarse.fits
   ./hst_cutout_skycell-p2007x09y05-ra351d3478-decn28d4978_wfc3_ir_f160w.fits
   ./hst_cutout_skycell-p2007x09y05-ra351d3478-decn28d4978_wfc3_uvis_f606w.fits
   ./hst_cutout_skycell-p2007x09y05-ra351d3478-decn28d4978_wfc3_uvis_f814w.fits
