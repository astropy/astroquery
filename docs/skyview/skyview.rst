.. doctest-skip-all

.. _astroquery_skyview:

**************************************
Skyview Queries (`astroquery.skyview`)
**************************************

Getting started
===============

The `SkyView <skyview.gsfc.nasa.gov>`_ service offers a cutout service for a
number of imaging surveys.

To see the list of surveys, use the `list_surveys` method:

.. code-block:: python

   >>> from astroquery.skyview import SkyView
   >>> SkyView.list_surveys()
   {'DiffuseX-ray': [u'RASS Background 1',
                     u'RASS Background 2',
                     u'RASS Background 3',
                     u'RASS Background 4',
                     u'RASS Background 5',
                     u'RASS Background 6',
                     u'RASS Background 7'],
    'GOODS/HDF/CDF(Allwavebands)': [u'GOODS: Chandra ACIS HB',
                                    u'GOODS: Chandra ACIS FB',
                                    u'GOODS: Chandra ACIS SB',
                                    u'GOODS: VLT VIMOS U',
                                    u'GOODS: VLT VIMOS R',
                                    u'GOODS: HST ACS B',
                                    u'GOODS: HST ACS V',
                                    u'GOODS: HST ACS I',
                                    u'GOODS: HST ACS Z',
                                    u'Hawaii HDF U',
                                    u'Hawaii HDF B',
                                    u'Hawaii HDF V0201',
                                    u'Hawaii HDF V0401',
                                    u'Hawaii HDF R',
                                    u'Hawaii HDF I',
                                    u'Hawaii HDF z',
                                    u'Hawaii HDF HK',
                                    u'GOODS: HST NICMOS',
                                    u'GOODS: VLT ISAAC J',
                                    u'GOODS: VLT ISAAC H',
                                    u'GOODS: VLT ISAAC Ks',
                                    u'HUDF: VLT ISAAC Ks',
                                    u'GOODS: Spitzer IRAC 3.6',
                                    u'GOODS: Spitzer IRAC 4.5',
                                    u'GOODS: Spitzer IRAC 5.8',
                                    u'GOODS: Spitzer IRAC 8.0',
                                    u'GOODS: Spitzer MIPS 24',
                                    u'GOODS: Herschel 100',
                                    u'GOODS: Herschel 160',
                                    u'GOODS: Herschel 250',
                                    u'GOODS: Herschel 350',
                                    u'GOODS: Herschel 500',
                                    u'CDFS: LESS',
                                    u'GOODS: VLA North'],
    'GammaRay': [u'Fermi 5',
                 u'Fermi 4',
                 u'Fermi 3',
                 u'Fermi 2',
                 u'Fermi 1',
                 u'EGRET (3D)',
                 u'EGRET <100 MeV',
                 u'EGRET >100 MeV',
                 u'COMPTEL'],
    'HardX-ray': [u'INT GAL 17-35 Flux',
                  u'INT GAL 17-60 Flux',
                  u'INT GAL 35-80 Flux',
                  u'INTEGRAL/SPI GC',
                  u'GRANAT/SIGMA',
                  u'RXTE Allsky 3-8keV Flux',
                  u'RXTE Allsky 3-20keV Flux',
                  u'RXTE Allsky 8-20keV Flux'],
    'IRAS': [u'IRIS  12',
             u'IRIS  25',
             u'IRIS  60',
             u'IRIS 100',
             u'SFD100m',
             u'SFD Dust Map',
             u'IRAS  12 micron',
             u'IRAS  25 micron',
             u'IRAS  60 micron',
             u'IRAS 100 micron'],
    'InfraredHighRes': [u'2MASS-J',
                        u'2MASS-H',
                        u'2MASS-K',
                        u'UKIDSS-Y',
                        u'UKIDSS-J',
                        u'UKIDSS-H',
                        u'UKIDSS-K',
                        u'WISE 3.4',
                        u'WISE 4.6',
                        u'WISE 12',
                        u'WISE 22'],
    'Optical:DSS': [u'DSS',
                    u'DSS1 Blue',
                    u'DSS1 Red',
                    u'DSS2 Red',
                    u'DSS2 Blue',
                    u'DSS2 IR'],
    'Optical:SDSS': [u'SDSSg',
                     u'SDSSi',
                     u'SDSSr',
                     u'SDSSu',
                     u'SDSSz',
                     u'SDSSdr7g',
                     u'SDSSdr7i',
                     u'SDSSdr7r',
                     u'SDSSdr7u',
                     u'SDSSdr7z'],
    'OtherOptical': [u'Mellinger Red',
                     u'Mellinger Green',
                     u'Mellinger Blue',
                     u'NEAT',
                     u'H-Alpha Comp',
                     u'SHASSA H',
                     u'SHASSA CC',
                     u'SHASSA C',
                     u'SHASSA Sm'],
    'Planck': [u'Planck 857',
               u'Planck 545',
               u'Planck 353',
               u'Planck 217',
               u'Planck 143',
               u'Planck 100',
               u'Planck 070',
               u'Planck 044',
               u'Planck 030'],
    'Radio': [u'GB6 (4850MHz)',
              u'VLA FIRST (1.4 GHz)',
              u'NVSS',
              u'Stripe82VLA',
              u'1420MHz (Bonn)',
              u'nH',
              u'SUMSS 843 MHz',
              u'0408MHz',
              u'WENSS',
              u'CO',
              u'VLSSr',
              u'0035MHz'],
    'SoftX-ray': [u'RASS-Cnt Soft',
                  u'RASS-Cnt Hard',
                  u'RASS-Cnt Broad',
                  u'PSPC 2.0 Deg-Int',
                  u'PSPC 1.0 Deg-Int',
                  u'PSPC 0.6 Deg-Int',
                  u'HRI',
                  u'HEAO 1 A-2'],
    'SwiftBAT': [u'BAT SNR 14-195',
                 u'BAT SNR 14-20',
                 u'BAT SNR 20-24',
                 u'BAT SNR 24-35',
                 u'BAT SNR 35-50',
                 u'BAT SNR 50-75',
                 u'BAT SNR 75-100',
                 u'BAT SNR 100-150',
                 u'BAT SNR 150-195'],
    'UV': [u'GALEX Near UV',
           u'GALEX Far UV',
           u'ROSAT WFC F1',
           u'ROSAT WFC F2',
           u'EUVE 83 A',
           u'EUVE 171 A',
           u'EUVE 405 A',
           u'EUVE 555 A'],
    'WMAP/COBE': [u'WMAP ILC',
                  u'WMAP Ka',
                  u'WMAP K',
                  u'WMAP Q',
                  u'WMAP V',
                  u'WMAP W',
                  u'COBE DIRBE/AAM',
                  u'COBE DIRBE/ZSMA']}

There are two essential methods: `get_images` searches for and downloads files,
while `get_image_list` just searches for the files.

.. code-block:: python

    >>> paths = SkyView.get_images(position='Eta Carinae',
    ...                       survey=['Fermi 5', 'HRI', 'DSS'])
    Downloading http://skyview.gsfc.nasa.gov/tempspace/fits/skv668576311417_1.fits
    |=========================================================================================================================| 371k/371k (100.00%)         0s
    Downloading http://skyview.gsfc.nasa.gov/tempspace/fits/skv668576311417_2.fits
    |=========================================================================================================================| 371k/371k (100.00%)         0s
    Downloading http://skyview.gsfc.nasa.gov/tempspace/fits/skv668576311417_3.fits
    |=========================================================================================================================| 374k/374k (100.00%)         0s
    >>> print paths
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
