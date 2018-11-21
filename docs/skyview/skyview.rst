.. doctest-skip-all

.. _astroquery_skyview:

**************************************
Skyview Queries (`astroquery.skyview`)
**************************************

Getting started
===============

The `SkyView <https://skyview.gsfc.nasa.gov/>`_ service offers a cutout service for a
number of imaging surveys.

To see the list of surveys, use the `~astroquery.skyview.SkyViewClass.list_surveys` method.  Note that the list here is not necessarily up-to-date; if SkyView has added surveys recently, they will appear when you run this code:

.. code-block:: python

   >>> from astroquery.skyview import SkyView
   >>> SkyView.list_surveys()
    {'Allbands:GOODS/HDF/CDF': ['GOODS: Chandra ACIS HB',
                                'GOODS: Chandra ACIS FB',
                                'GOODS: Chandra ACIS SB',
                                'GOODS: VLT VIMOS U',
                                'GOODS: VLT VIMOS R',
                                'GOODS: HST ACS B',
                                'GOODS: HST ACS V',
                                'GOODS: HST ACS I',
                                'GOODS: HST ACS Z',
                                'Hawaii HDF U',
                                'Hawaii HDF B',
                                'Hawaii HDF V0201',
                                'Hawaii HDF V0401',
                                'Hawaii HDF R',
                                'Hawaii HDF I',
                                'Hawaii HDF z',
                                'Hawaii HDF HK',
                                'GOODS: HST NICMOS',
                                'GOODS: VLT ISAAC J',
                                'GOODS: VLT ISAAC H',
                                'GOODS: VLT ISAAC Ks',
                                'HUDF: VLT ISAAC Ks',
                                'GOODS: Spitzer IRAC 3.6',
                                'GOODS: Spitzer IRAC 4.5',
                                'GOODS: Spitzer IRAC 5.8',
                                'GOODS: Spitzer IRAC 8.0',
                                'GOODS: Spitzer MIPS 24',
                                'GOODS: Herschel 100',
                                'GOODS: Herschel 160',
                                'GOODS: Herschel 250',
                                'GOODS: Herschel 350',
                                'GOODS: Herschel 500',
                                'CDFS: LESS',
                                'GOODS: VLA North'],
     'Allbands:HiPS': ['UltraVista-H',
                       'UltraVista-J',
                       'UltraVista-Ks',
                       'UltraVista-NB118',
                       'UltraVista-Y',
                       'CFHTLS-W-u',
                       'CFHTLS-W-g',
                       'CFHTLS-W-r',
                       'CFHTLS-W-i',
                       'CFHTLS-W-z',
                       'CFHTLS-D-u',
                       'CFHTLS-D-g',
                       'CFHTLS-D-r',
                       'CFHTLS-D-i',
                       'CFHTLS-D-z'],
     'GammaRay': ['Fermi 5',
                  'Fermi 4',
                  'Fermi 3',
                  'Fermi 2',
                  'Fermi 1',
                  'EGRET (3D)',
                  'EGRET <100 MeV',
                  'EGRET >100 MeV',
                  'COMPTEL'],
     'HardX-ray': ['INT GAL 17-35 Flux',
                   'INT GAL 17-60 Flux',
                   'INT GAL 35-80 Flux',
                   'INTEGRAL/SPI GC',
                   'GRANAT/SIGMA',
                   'RXTE Allsky 3-8keV Flux',
                   'RXTE Allsky 3-20keV Flux',
                   'RXTE Allsky 8-20keV Flux'],
     'IR:2MASS': ['2MASS-J', '2MASS-H', '2MASS-K'],
     'IR:AKARI': ['AKARI N60', 'AKARI WIDE-S', 'AKARI WIDE-L', 'AKARI N160'],
     'IR:IRAS': ['IRIS  12',
                 'IRIS  25',
                 'IRIS  60',
                 'IRIS 100',
                 'SFD100m',
                 'SFD Dust Map',
                 'IRAS  12 micron',
                 'IRAS  25 micron',
                 'IRAS  60 micron',
                 'IRAS 100 micron'],
     'IR:Planck': ['Planck 857',
                   'Planck 545',
                   'Planck 353',
                   'Planck 217',
                   'Planck 143',
                   'Planck 100',
                   'Planck 070',
                   'Planck 044',
                   'Planck 030'],
     'IR:UKIDSS': ['UKIDSS-Y', 'UKIDSS-J', 'UKIDSS-H', 'UKIDSS-K'],
     'IR:WISE': ['WISE 3.4', 'WISE 4.6', 'WISE 12', 'WISE 22'],
     'IR:WMAP&COBE': ['WMAP ILC',
                      'WMAP Ka',
                      'WMAP K',
                      'WMAP Q',
                      'WMAP V',
                      'WMAP W',
                      'COBE DIRBE/AAM',
                      'COBE DIRBE/ZSMA'],
     'Optical:DSS': ['DSS',
                     'DSS1 Blue',
                     'DSS1 Red',
                     'DSS2 Red',
                     'DSS2 Blue',
                     'DSS2 IR'],
     'Optical:SDSS': ['SDSSg',
                      'SDSSi',
                      'SDSSr',
                      'SDSSu',
                      'SDSSz',
                      'SDSSdr7g',
                      'SDSSdr7i',
                      'SDSSdr7r',
                      'SDSSdr7u',
                      'SDSSdr7z'],
     'OtherOptical': ['Mellinger Red',
                      'Mellinger Green',
                      'Mellinger Blue',
                      'NEAT',
                      'H-Alpha Comp',
                      'SHASSA H',
                      'SHASSA CC',
                      'SHASSA C',
                      'SHASSA Sm'],
     'ROSATDiffuse': ['RASS Background 1',
                      'RASS Background 2',
                      'RASS Background 3',
                      'RASS Background 4',
                      'RASS Background 5',
                      'RASS Background 6',
                      'RASS Background 7'],
     'ROSATw/sources': ['RASS-Cnt Soft',
                        'RASS-Cnt Hard',
                        'RASS-Cnt Broad',
                        'PSPC 2.0 Deg-Int',
                        'PSPC 1.0 Deg-Int',
                        'PSPC 0.6 Deg-Int',
                        'HRI'],
     'Radio:GHz': ['CO',
                   'GB6 (4850MHz)',
                   'VLA FIRST (1.4 GHz)',
                   'NVSS',
                   'Stripe82VLA',
                   '1420MHz (Bonn)',
                   'HI4PI',
                   'EBHIS',
                   'nH'],
     'Radio:GLEAM': ['GLEAM 72-103 MHz',
                     'GLEAM 103-134 MHz',
                     'GLEAM 139-170 MHz',
                     'GLEAM 170-231 MHz'],
     'Radio:MHz': ['SUMSS 843 MHz',
                   '0408MHz',
                   'WENSS',
                   'TGSS ADR1',
                   'VLSSr',
                   '0035MHz'],
     'SoftX-ray': ['SwiftXRTCnt', 'SwiftXRTExp', 'SwiftXRTInt', 'HEAO 1 A-2'],
     'SwiftUVOT': ['UVOT WHITE Intensity',
                   'UVOT V Intensity',
                   'UVOT B Intensity',
                   'UVOT U Intensity',
                   'UVOT UVW1 Intensity',
                   'UVOT UVM2 Intensity',
                   'UVOT UVW2 Intensity'],
     'UV': ['GALEX Near UV',
            'GALEX Far UV',
            'ROSAT WFC F1',
            'ROSAT WFC F2',
            'EUVE 83 A',
            'EUVE 171 A',
            'EUVE 405 A',
            'EUVE 555 A'],
     'X-ray:SwiftBAT': ['BAT SNR 14-195',
                        'BAT SNR 14-20',
                        'BAT SNR 20-24',
                        'BAT SNR 24-35',
                        'BAT SNR 35-50',
                        'BAT SNR 50-75',
                        'BAT SNR 75-100',
                        'BAT SNR 100-150',
                        'BAT SNR 150-195']}

There are two essential methods:
`~astroquery.skyview.SkyViewClass.get_images` searches for and downloads
files, while `~astroquery.skyview.SkyViewClass.get_image_list` just searches
for the files.

.. code-block:: python

    >>> paths = SkyView.get_images(position='Eta Carinae',
    ...                       survey=['Fermi 5', 'HRI', 'DSS'])
    Downloading http://skyview.gsfc.nasa.gov/tempspace/fits/skv668576311417_1.fits
    |=========================================================================================================================| 371k/371k (100.00%)         0s
    Downloading http://skyview.gsfc.nasa.gov/tempspace/fits/skv668576311417_2.fits
    |=========================================================================================================================| 371k/371k (100.00%)         0s
    Downloading http://skyview.gsfc.nasa.gov/tempspace/fits/skv668576311417_3.fits
    |=========================================================================================================================| 374k/374k (100.00%)         0s
    >>> print(paths)
    [[<astropy.io.fits.hdu.image.PrimaryHDU object at 0x10ef3a250>], [<astropy.io.fits.hdu.image.PrimaryHDU object at 0x10f096f10>], [<astropy.io.fits.hdu.image.PrimaryHDU object at 0x10f0aea50>]]

Without the download:

.. code-block:: python


    >>> SkyView.get_image_list(position='Eta Carinae',
                      survey=['Fermi 5', 'HRI', 'DSS'])
    [u'http://skyview.gsfc.nasa.gov/tempspace/fits/skv669807193757_1.fits',
     u'http://skyview.gsfc.nasa.gov/tempspace/fits/skv669807193757_2.fits',
     u'http://skyview.gsfc.nasa.gov/tempspace/fits/skv669807193757_3.fits']


Reference/API
=============

.. automodapi:: astroquery.skyview
    :no-inheritance-diagram:
