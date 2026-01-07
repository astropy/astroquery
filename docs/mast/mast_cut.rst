
*************
Image Cutouts
*************

The image cutout interfaces in `astroquery.mast` provide a convenient way to retrieve
small, spatially localized subsets of large imaging datasets hosted at MAST. Instead of
downloading full-frame images, users can request cutouts centered on a sky position or target
of interest, reducing data volume and simplifying exploratory analysis.

Cutout services support several major MAST imaging products, including TESS full-frame
images, Hubble Advanced Products (HAP), and selected deep-field surveys. These interfaces are
designed for common science workflows such as quick-look visualization, time-series
extraction, and focused analysis around known sources.

The sections below describe the available cutout classes and typical usage patterns, 
with examples demonstrating how to request cutout products.

TESSCut
=======

`TESSCut <https://mast.stsci.edu/tesscut/>`__ is a MAST service that provides image cutouts from the **full-frame images 
(FFIs) taken by the Transiting Exoplanet Survey Satellite** (`TESS <https://archive.stsci.edu/missions-and-data/tess>`__).
This service enables users to extract small, localized regions of TESS data around targets of interest without downloading
entire FFI files, which are quite large. TESSCut is particularly useful for time-series analysis, quick-look visualization, 
and focused studies of specific objects.

The `~astroquery.mast.TesscutClass` provides programmatic access to the 
`MAST TESScut API <https://mast.stsci.edu/tesscut/docs/getting_started.html#requesting-a-cutout>`__,
enabling TESSCut queries directly from Python scripts and applications. It has three main capabilities:

- Sector Discovery: Identify which TESS sectors, cameras, and CCDs cover a given sky position or object.
- In-memory Cutouts: Retrieve cutouts as `~astropy.io.fits.HDUList` objects for immediate analysis without writing files to disk.
- Downloaded Cutouts: Download cutout target pixel files (TPFs) to local storage.

TESSCut supports cutout requests centered on fixed sky coordinates, resolved object names (including TIC IDs), and 
moving targets such as asteroids and comets. Requests may return multiple cutouts when a target appears in more than 
one sector or overlaps multiple cameras or CCDs. For fixed targets, cutouts may be requested by sky coordinates or object name.
For moving targets, `ephemerides from the JPL Horizons <https://ssd.jpl.nasa.gov/horizons/app.html>`__ system are used to determine 
target positions on a per-sector basis. All cutouts are generated from Science Processing Operations 
Center (`SPOC <https://archive.stsci.edu/missions-and-data/tess>`__) FFI products and are returned in the standard TESS 
`target pixel file format <https://astrocut.readthedocs.io/en/latest/astrocut/file_formats.html#target-pixel-files>`__.

As of August 2025, the option to generate cutouts from TESS Image Calibration
(`TICA <https://ui.adsabs.harvard.edu/abs/2020RNAAS...4..251F/abstract>`__) full frame images
has been discontinued. Individual TICA FFIs remain available from the
`MAST TICA homepage <https://archive.stsci.edu/hlsp/tica>`__. Cutouts generated from SPOC
FFIs continue to be supported through TESSCut.

**Note:** TESSCut limits each user to a maximum of **10 simultaneous requests**. If this limit
is exceeded, the service will respond with a ``503 Service Temporarily Unavailable Error``.

If you use TESSCut for your work, please cite 
`Brasseur et al. 2019 <https://ui.adsabs.harvard.edu/abs/2019ascl.soft05007B/abstract>`__.


Sector Discovery
-----------------

Before requesting cutouts, it is often useful to determine which TESS sectors contain data
for a given target. TESS observes the sky in discrete observing campaigns called sectors,
and cutouts can only be generated for sectors in which the target falls on an active camera
and CCD.

The `~astroquery.mast.TesscutClass.get_sectors` method identifies the TESS sectors whose
footprints intersect a given target or region of the sky. Targets may be specified using sky
coordinates, a resolved object name (including TIC IDs), or a moving target name.

The result is returned as an `~astropy.table.Table` containing the sector number along with
the corresponding camera and CCD information. This table can be used to:

- Verify whether a target was observed by TESS
- Identify all available sectors before requesting cutouts
- Select a specific sector, camera, or CCD for downstream analysis

If no sectors overlap the requested location, a warning is issued and an empty result is
returned.

For moving targets, sector discovery accounts for the target's motion across the sky. When a
sector is not explicitly specified in later cutout requests, this information is used
internally to generate cutouts for each applicable sector.

The following example demonstrates how to use the `~astroquery.mast.TesscutClass.get_sectors` method with sky coordinates.

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
   tess-s0061-1-2     61      1   2
   tess-s0088-1-2     88      1   2

You can also use the ``objectname`` parameter to specify a target by name or TIC ID.

.. doctest-remote-data::

   >>> sector_table = Tesscut.get_sectors(objectname="TIC 32449963")
   >>> print(sector_table)     # doctest: +IGNORE_OUTPUT
     sectorName   sector camera ccd
   -------------- ------ ------ ---
   tess-s0010-1-4     10      1   4

To find sectors for a moving target, set the ``moving_target`` parameter to ``True``.

.. doctest-remote-data::

   >>> sector_table = Tesscut.get_sectors(objectname="Ceres", moving_target=True)
   >>> print(sector_table)
     sectorName   sector camera ccd
   -------------- ------ ------ ---
   tess-s0029-1-4     29      1   4
   tess-s0043-3-3     43      3   3
   tess-s0044-2-4     44      2   4
   tess-s0092-4-3     92      4   3
   tess-s0097-1-4     97      1   4


Cutouts in Memory
-----------------

For interactive analysis or workflows that do not require writing files to disk,
`~astroquery.mast.TesscutClass.get_cutouts` can be used to load TESS cutouts directly
into memory. This method returns cutout data as a list of
`~astropy.io.fits.HDUList` objects, allowing immediate inspection and analysis.

Targets may be specified by sky coordinates, resolved object names (including TIC IDs), or
moving targets. The cutout size may be given in pixels or as an angular quantity; if not
specified, a default size of 5 pixels is used.

The optional ``sector`` parameter controls which TESS observing sector is used when generating
cutouts. When ``sector`` is provided, cutouts are generated only from data in that specific
sector. This is useful when focusing on a particular observing window, comparing results
across sectors, or avoiding unnecessary data retrieval.

If ``sector`` is not specified, `~astroquery.mast.TesscutClass.get_cutouts` will return cutouts for all available
sectors in which the target appears. In this case, a separate target pixel file is returned
for each sector, and potentially for each camera or CCD overlapped by the cutout region. The returned cutout
list may therefore contain multiple cutouts, depending on the number of sectors, cameras, and CCDs involved.
This behavior ensures that all available data covering the target is returned.

The following example demonstrates how to request a TESS cutout using sky coordinates and a specified sector.

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> cutout_coord = SkyCoord(107.18696, -70.50919, unit="deg")
   >>> hdulist = Tesscut.get_cutouts(coordinates=cutout_coord, sector=33)
   >>> hdulist[0].info()
   Filename: <class '_io.BytesIO'>
   No.    Name      Ver    Type      Cards   Dimensions   Format
   0  PRIMARY       1 PrimaryHDU      57   ()
   1  PIXELS        1 BinTableHDU    281   3495R x 12C   [D, E, J, 25J, 25E, 25E, 25E, 25E, J, E, E, 38A]
   2  APERTURE      1 ImageHDU        82   (5, 5)   int32

You may also request cutouts of a moving target by inputting a valid moving target as the ``objectname`` and setting 
the ``moving_target`` parameter to ``True``.

.. doctest-remote-data::

   >>> hdulist = Tesscut.get_cutouts(objectname="Eleonora",
   ...                               moving_target=True,
   ...                               sector=6)
   >>> hdulist[0].info()  # doctest: +IGNORE_OUTPUT
   Filename: <class '_io.BytesIO'>
   No.    Name      Ver    Type      Cards   Dimensions   Format
     0  PRIMARY       1 PrimaryHDU      54   ()
     1  PIXELS        1 BinTableHDU    150   355R x 16C   [D, E, J, 25J, 25E, 25E, 25E, 25E, J, E, E, 38A, D, D, D, D]
     2  APERTURE      1 ImageHDU        97   (2136, 2078)   int32

Download Cutouts
----------------

For workflows that require persistent files on disk, such as batch processing or repeated
analysis, `~astroquery.mast.TesscutClass.download_cutouts` can be used to download TESS cutout
target pixel files to local storage.

This method accepts the same target specifications and cutout sizing options as
`~astroquery.mast.TesscutClass.get_cutouts`, but instead of returning in-memory FITS objects, it writes the resulting
cutout files to disk and returns an `~astropy.table.Table` listing the local file paths.

By default, cutouts are downloaded as a compressed archive and automatically extracted into
the specified directory. The temporary archive is removed after extraction. To retain the
compressed archive without extracting its contents, set ``inflate=False``.

As with in-memory cutouts, multiple files may be produced when a target appears in more than
one TESS sector or overlaps multiple cameras or CCDs. For moving targets, if no sector is
specified, cutouts are downloaded separately for each applicable sector to reduce load on the
service.

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

The returned table contains the paths to the downloaded target pixel files, which follow the
standard TESS pipeline format and can be opened using Astropy or other FITS-compatible tools.

Downloaded cutouts are recommended when working with large numbers of targets, performing
offline analysis, or integrating TESS cutouts into automated pipelines.


Zcut
====

ZCut is a MAST service that provides image cutouts from **large, deep-field imaging surveys**
hosted at MAST. Unlike mission-specific cutout services, ZCut enables positional cutouts from
a variety of wide-area and deep-field datasets through a single interface, making it useful
for exploratory imaging analysis and multi-survey comparisons.

The `~astroquery.mast.ZcutClass` provides programmatic access to the `MAST ZCut API <https://mast.stsci.edu/zcut/>`_, 
allowing users to generate cutouts centered on a sky position without downloading full-frame images.
Cutouts may be returned either as in-memory FITS objects for interactive analysis or as files
written to disk in FITS or common image formats.

ZCut supports workflows for discovering which deep-field surveys cover a given sky position,
as well as requesting cutouts from one or more of those surveys. Optional image-scaling and
stretching parameters are available when requesting image-format cutouts, enabling
quick-look visualization directly from the service.

The sections below describe how to identify available surveys at a given position and how to
retrieve cutouts using both in-memory and downloaded workflows.

Survey Discovery
-----------------

Before requesting cutouts, users may wish to determine which deep-field surveys cover a
given position on the sky. ZCut provides a survey discovery step that identifies all available
imaging surveys whose footprints intersect a specified target location.

The `~astroquery.mast.ZcutClass.get_surveys` method returns a list of deep-field surveys
available at a given sky position. The target location may be specified using sky coordinates
or a resolvable target name. An optional search radius may be provided to expand the region
used for survey matching.

The result is returned as a list of survey identifiers, which can be used to:

- Verify whether a position is covered by one or more deep-field surveys
- Select a specific survey for subsequent cutout requests
- Inspect and compare coverage across multiple surveys

If no surveys overlap the requested location, a warning is issued and an empty result is
returned.

.. doctest-remote-data::

   >>> from astroquery.mast import Zcut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> coord = SkyCoord(189.49206, 62.20615, unit="deg")
   >>> survey_list = Zcut.get_surveys(coordinates=coord)
   >>> print(survey_list)    # doctest: +IGNORE_OUTPUT
   ['candels_gn_60mas', 'candels_gn_30mas', 'goods_north', '3dhst_goods-n']


Cutouts in Memory
-----------------

For interactive analysis or exploratory workflows, ZCut supports retrieving cutouts directly
into memory without writing files to disk. The
`~astroquery.mast.ZcutClass.get_cutouts` method returns cutout data as a list of
`~astropy.io.fits.HDUList` objects, which can be inspected and analyzed immediately.

Cutouts are requested by sky position and may optionally be restricted to a specific survey with the ``survey`` parameter.
The cutout size may be specified in pixels or as an angular quantity; if not provided, a
default size of 5 pixels is used.

When no survey is specified, cutouts are returned for all surveys that cover the requested
position. If a survey is provided, only cutouts from that survey are returned. This allows
users to compare coverage across multiple datasets or to focus on a single deep-field survey
of interest. The returned list may contain multiple cutouts, depending on the number of surveys that
overlap the requested location.

The following example demonstrates how to request a ZCut cutout using sky coordinates and a specified survey.

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


Download Cutouts
-----------------

For workflows that require cutout files to be saved locally, such as batch processing or
offline analysis, `~astroquery.mast.ZcutClass.download_cutouts` can be used to download ZCut
image cutouts to disk.

This method accepts the same target, size, and survey parameters as `~astroquery.mast.ZcutClass.get_cutouts`, but
writes the resulting cutout files to the specified directory instead of returning in-memory
objects. The method returns an `~astropy.table.Table` containing the local file paths of the
downloaded cutouts.

By default, cutouts are returned from the service as a compressed archive and are
automatically extracted into the output directory. The temporary archive is removed after
extraction. To retain the archive without extracting its contents, set ``inflate=False``.

Cutouts may be saved in FITS format or in common image formats (jpg or png). When
requesting image-format cutouts, optional image-scaling parameters may be supplied to control
stretching, scaling, and inversion for quick-look visualization.

If no survey is specified, cutouts are downloaded for all surveys that cover the requested
position. Restricting the request to a single survey can help reduce the number of returned
files.

The following example demonstrates how to download ZCut cutouts using sky coordinates and a specified survey.

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

You can also request cutouts in image formats such as jpg by setting the ``cutout_format`` parameter.

.. doctest-remote-data::

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


HAPCut
======

HAPCut is a MAST service that provides image cutouts from **Hubble Advanced Products (HAP)**,
which are high-level, science-ready data products derived from Hubble Space Telescope
observations. These products combine and reprocess individual exposures to produce
well-aligned, calibrated images suitable for direct scientific analysis.

The `~astroquery.mast.HapcutClass` provides programmatic access to the `MAST HAPCut API <https://mast.stsci.edu/hapcut/>`_,
allowing users to generate image cutouts centered on a sky position without downloading full
HAP mosaics or images. This interface is designed for simple, position-based cutout requests
and supports both in-memory and file-based workflows.

HAPCut cutouts are returned as FITS images and are well suited for quick-look visualization,
photometric measurements, and targeted analysis of small regions within larger Hubble
datasets. Unlike other cutout services, HAPCut does not require survey or sector selection;
all available HAP imaging that overlaps the requested position is returned.

The sections below describe how to retrieve HAP cutouts directly into memory or download them
to disk for further analysis.

Cutouts in Memory
-----------------

For interactive analysis or exploratory workflows, HAPCut supports retrieving image cutouts
directly into memory without writing files to disk. The
`~astroquery.mast.HapcutClass.get_cutouts` method returns cutout data as a list of
`~astropy.io.fits.HDUList` objects, allowing immediate inspection and analysis.

Cutouts are requested by sky position and cutout size. The target may be specified using sky
coordinates or a resolvable object name, and the cutout size may be given in pixels or as an
angular quantity. If not specified, a default size of 5 pixels is used.

When multiple HAP images overlap the requested position, a separate cutout is returned for
each matching image. This ensures that all available Hubble Advanced Products covering the
target are included in the result.

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

Each element in the returned list is a FITS image provided as an in-memory object. In-memory cutouts are best 
suited for visualization, exploratory analysis, and notebook-based workflows where temporary files are unnecessary.

Download Cutouts
----------------

For workflows that require cutout files to be saved locally, such as batch processing or
offline analysis, `~astroquery.mast.HapcutClass.download_cutouts` can be used to download HAP
image cutouts to disk.

This method accepts the same target and size parameters as `~astroquery.mast.HapcutClass.get_cutouts`, 
but writes the resulting cutout files to the specified directory instead of returning in-memory FITS
objects. The method returns an `~astropy.table.Table` listing the local paths of the
downloaded cutouts.

By default, cutouts are returned from the service as a compressed archive and are
automatically extracted into the output directory. The temporary archive is removed after
extraction. To retain the archive without extracting its contents, set ``inflate=False``.

If multiple HAP images overlap the requested position, a separate cutout file is produced for
each image. This behavior ensures that all available Hubble Advanced Products covering the
target location are included in the downloaded results.

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

The returned table contains the paths to the downloaded FITS cutout files, which can be
opened using standard FITS-compatible tools for further analysis.
