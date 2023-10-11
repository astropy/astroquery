.. _astroquery_skyview:

**************************************
Skyview Queries (`astroquery.skyview`)
**************************************

Getting started
===============

The `SkyView <https://skyview.gsfc.nasa.gov/>`_ service offers a cutout service for a
number of imaging surveys.

To see the list of surveys, use the `~astroquery.skyview.SkyViewClass.list_surveys` method.
Note that the list here is not necessarily up-to-date; if the archive has added surveys recently, SkyView will query all available SIAP services and they will appear when you run this code:

.. doctest-remote-data::

   >>> from astroquery.skyview import SkyView
   >>> SkyView.list_surveys()  # doctest: +IGNORE_OUTPUT
    ['1420MHz', '22MHz', '2MASS', '408MHz', 'AKARI', 'BAT-flux-1', 'CDFS LESS', 'CFHTLS-D-u', 'CFHTLS-W-u', 'CO', 'COBE', 'Comptel', 'DSS', 'DSS1B', 'DSS1R', 'DSS2', 'EBHIS', 'EGRET', 'EGRET3D', 'EUVE', 'FERMI', 'FIRST', 'GALEX', 'GLEAM1', 'GNS', 'GOODS ACS B', 'GOODS ISAAC H', 'GOODS VIMOS R', 'GOODSACISFB', 'GOODSHerschel1', 'GOODSHerschel2', 'GOODSHerschel3', 'GOODSHerschel4', 'GOODSHerschel5', 'GOODSIRAC 1', 'GOODSMIPS', 'GOODSNVLA', 'GRANAT', 'GTEE', 'HAlpha', 'Hawaii HDF B', 'HEAO1A', 'HERSCHEL SPIRE', 'HI4PI', 'HRI', 'HUDFISAAC', 'INTEGRALSPI_gc', 'INTGAL1735E', 'IRAS', 'IRIS', 'MELLINGER', 'nH', 'NVSS', 'Planck857I', 'PMN', 'PSPC0.6Int', 'PSPC1', 'PSPC2', 'RASS3', 'RASSBACK', 'RXTE3_20k_flux', 'SDSS', 'SDSSDR7', 'SFD', 'SHASSA', 'SkyView', 'Stripe82VLA', 'SUMSS', 'SWIFTUVOT', 'SWIFTXRT', 'TESS', 'TGSS', 'UKIDSS', 'UltraVista-H', 'VLSS', 'WENSS', 'WFCF', 'WISE', 'WMAP']

Some of the above SIAP services are catalogs that contain multiple surveys within them; querying these services will return products from each of their surveys that users can filter upon.

Image Retrieval
===============
When querying SkyView, one can either retrieve links for the files, or download and open the files as FITS objects.

Running `~astroquery.skyview.SkyViewClass.get_image_list` will only retrieve the links, without downloading:

.. doctest-remote-data::

    >>> SkyView.get_image_list(position='Eta Carinae', survey=['FERMI', 'HRI', 'DSS'])  # doctest: +IGNORE_OUTPUT
        ['https://skyview.gsfc.nasa.gov/cgi-bin/images?position=161.26474075372%2C-59.6844587777&survey=fermi1&pixels=300%2C300&sampler=LI&size=1.0%2C1.0&projection=Tan&coordinates=J2000.0&requestID=skv1697058481603&return=FITS',
        'https://skyview.gsfc.nasa.gov/cgi-bin/images?position=161.26474075372%2C-59.6844587777&survey=fermi2&pixels=300%2C300&sampler=LI&size=1.0%2C1.0&projection=Tan&coordinates=J2000.0&requestID=skv1697058481627&return=FITS',
        'https://skyview.gsfc.nasa.gov/cgi-bin/images?position=161.26474075372%2C-59.6844587777&survey=fermi3&pixels=300%2C300&sampler=LI&size=1.0%2C1.0&projection=Tan&coordinates=J2000.0&requestID=skv1697058481644&return=FITS',
        'https://skyview.gsfc.nasa.gov/cgi-bin/images?position=161.26474075372%2C-59.6844587777&survey=fermi4&pixels=300%2C300&sampler=LI&size=1.0%2C1.0&projection=Tan&coordinates=J2000.0&requestID=skv1697058481660&return=FITS',
        'https://skyview.gsfc.nasa.gov/cgi-bin/images?position=161.26474075372%2C-59.6844587777&survey=fermi5&pixels=300%2C300&sampler=LI&size=1.0%2C1.0&projection=Tan&coordinates=J2000.0&requestID=skv1697058481683&return=FITS',
        'https://skyview.gsfc.nasa.gov/cgi-bin/images?position=161.26474075372%2C-59.6844587777&survey=hri&pixels=300%2C300&sampler=LI&size=1.0%2C1.0&projection=Tan&coordinates=J2000.0&requestID=skv1697058483338&return=FITS',
        'https://skyview.gsfc.nasa.gov/cgi-bin/images?position=161.26474075372%2C-59.6844587777&survey=dss&pixels=300%2C300&sampler=LI&size=1.0%2C1.0&projection=Tan&coordinates=J2000.0&requestID=skv1697058484423&return=FITS']

while `~astroquery.skyview.SkyViewClass.get_images` will download the corresponding files and return an array of FITS objects

.. doctest-skip::

    >>> SkyView.get_images(position='Eta Carinae', survey=['FERMI', 'HRI', 'DSS'])  # doctest: +IGNORE_OUTPUT
        Downloading https://skyview.gsfc.nasa.gov/cgi-bin/images?position=161.26474075372%2C-59.6844587777&survey=fermi1&pixels=300%2C300&sampler=LI&size=1.0%2C1.0&projection=Tan&coordinates=J2000.0&requestID=skv1697058597559&return=FITS [Done]
        Downloading https://skyview.gsfc.nasa.gov/cgi-bin/images?position=161.26474075372%2C-59.6844587777&survey=fermi2&pixels=300%2C300&sampler=LI&size=1.0%2C1.0&projection=Tan&coordinates=J2000.0&requestID=skv1697058597581&return=FITS [Done]
        Downloading https://skyview.gsfc.nasa.gov/cgi-bin/images?position=161.26474075372%2C-59.6844587777&survey=fermi3&pixels=300%2C300&sampler=LI&size=1.0%2C1.0&projection=Tan&coordinates=J2000.0&requestID=skv1697058597605&return=FITS [Done]
        Downloading https://skyview.gsfc.nasa.gov/cgi-bin/images?position=161.26474075372%2C-59.6844587777&survey=fermi4&pixels=300%2C300&sampler=LI&size=1.0%2C1.0&projection=Tan&coordinates=J2000.0&requestID=skv1697058597640&return=FITS [Done]
        Downloading https://skyview.gsfc.nasa.gov/cgi-bin/images?position=161.26474075372%2C-59.6844587777&survey=fermi5&pixels=300%2C300&sampler=LI&size=1.0%2C1.0&projection=Tan&coordinates=J2000.0&requestID=skv1697058597723&return=FITS [Done]
        Downloading https://skyview.gsfc.nasa.gov/cgi-bin/images?position=161.26474075372%2C-59.6844587777&survey=hri&pixels=300%2C300&sampler=LI&size=1.0%2C1.0&projection=Tan&coordinates=J2000.0&requestID=skv1697058598976&return=FITS [Done]
        Downloading https://skyview.gsfc.nasa.gov/cgi-bin/images?position=161.26474075372%2C-59.6844587777&survey=dss&pixels=300%2C300&sampler=LI&size=1.0%2C1.0&projection=Tan&coordinates=J2000.0&requestID=skv1697058600237&return=FITS [Done]
        [[<astropy.io.fits.hdu.image.PrimaryHDU object at 0x0000015A61FD22C0>],
         [<astropy.io.fits.hdu.image.PrimaryHDU object at 0x0000015A61FD3B20>],
         [<astropy.io.fits.hdu.image.PrimaryHDU object at 0x0000015A61FF6FB0>],
         [<astropy.io.fits.hdu.image.PrimaryHDU object at 0x0000015A61E104F0>],
         [<astropy.io.fits.hdu.image.PrimaryHDU object at 0x0000015A61EDDC30>],
         [<astropy.io.fits.hdu.image.PrimaryHDU object at 0x0000015A61EDF3A0>],
         [<astropy.io.fits.hdu.image.PrimaryHDU object at 0x0000015A61F2D330>]]

Supported Parameters
--------------------
Running ``help()`` on any of the ``~astroquery.skyview.SkyViewClass.get_image`` methods will return the actively supported parameters::

        Parameters
        ----------
        position : str
            Determines the center of the field to be retrieved. Both
            coordinates (also equatorial ones) and object names are
            supported. Object names are converted to coordinates via the
            SIMBAD or NED name resolver. See the reference for more info
            on the supported syntax for coordinates.
        survey : str or list of str
            Select data from one or more surveys. The number of surveys
            determines the number of resulting file downloads. Passing a
            list with just one string has the same effect as passing this
            string directly.
        coordinates : str
            Choose among common equatorial, galactic and ecliptic
            coordinate systems (``"J2000"``, ``"B1950"``, ``"Galactic"``,
            ``"E2000"``, ``"ICRS"``) or pass a custom string.
        projection : str
            Choose among the map projections (the value in parentheses
            denotes the string to be passed):

            Gnomonic (Tan), default value
                good for small regions
            Rectangular (Car)
                simplest projection
            Aitoff (Ait)
                Hammer-Aitoff, equal area projection good for all sky maps
            Orthographic (Sin)
                Projection often used in interferometry
            Zenith Equal Area (Zea)
                equal area, azimuthal projection
            COBE Spherical Cube (Csc)
                Used in COBE data
            Arc (Arc)
                Similar to Zea but not equal-area
        pixels : str
            Selects the pixel dimensions of the image to be produced. A
            scalar value or a pair of values separated by comma may be
            given. If the value is a scalar the number of width and height
            of the image will be the same. By default a 300x300 image is
            produced.
        scaling : str
            Selects the transformation between pixel intensity and
            intensity on the displayed image. The supported values are:
            ``"Log"``, ``"Sqrt"``, ``"Linear"``, ``"HistEq"``,
            ``"LogLog"``.
        sampler : str
            The sampling algorithm determines how the data requested will
            be resampled so that it can be displayed.
        radius : `~astropy.units.Quantity` or None
            The angular radius of the specified field.


Reference/API
=============

.. automodapi:: astroquery.skyview
    :no-inheritance-diagram:
