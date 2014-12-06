.. doctest-skip-all

A Gallery of Queries
====================

A series of queries folks have performed for research or for kicks.  

Example 1
+++++++++

This illustrates querying Vizier with specific keyword, and the use of 
`astropy.coordinates` to describe a query.
Vizier's keywords can indicate wavelength & object type, although only 
object type is shown here.

.. code-block:: python

    >>> from astroquery.vizier import Vizier
    >>> v = Vizier(keywords=['stars:white_dwarf'])
    >>> from astropy import coordinates
    >>> from astropy import units as u
    >>> c = coordinates.SkyCoord(0,0,unit=('deg','deg'),frame='icrs')
    >>> result = v.query_region(c, radius=2*u.deg)
    >>> print len(result)
    31
    >>> result[0].pprint()
       LP    Rem Name  RA1950   DE1950  Rmag l_Pmag Pmag u_Pmag spClass   pm   pmPA _RA.icrs _DE.icrs
    -------- --- ---- -------- -------- ---- ------ ---- ------ ------- ------ ---- -------- --------
    584-0063          00 03 23 +00 01.8 18.1        18.3              f  0.219   93 00 05 57 +00 18.7
    643-0083          23 50 40 +00 33.4 15.9        17.0              k  0.197   93 23 53 14 +00 50.3
    584-0030          23 54 05 -01 32.3 16.6        17.7              k  0.199  193 23 56 39 -01 15.4
    

Example 2
+++++++++

This illustrates adding new output fields to SIMBAD queries.
Run `~astroquery.simbad.SimbadClass.list_votable_fields` to get the full list of valid fields.

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> s = Simbad()
    >>> # bibcodelist(date1-date2) lists the number of bibliography
    >>> # items referring to each object over that date range
    >>> s.add_votable_fields('bibcodelist(2003-2013)')
    >>> r = s.query_object('m31')
    >>> r.pprint()
    MAIN_ID      RA          DEC      RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE     BIBLIST_2003_2013
    ------- ------------ ------------ ------- -------- ------------ ------------ ------------- -------- -------------- ------------------- -----------------
      M  31 00 42 44.330 +41 16 07.50       7        7          nan          nan             0        B              I 2006AJ....131.1163S              3758


Example 3
+++++++++

This illustrates finding the spectral type of some particular star.

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> customSimbad = Simbad()
    >>> customSimbad.add_votable_fields('sptype')
    >>> result = customSimbad.query_object('g her')
    >>> result['MAIN_ID'][0]
    'V* g Her'
    >>> result['SP_TYPE'][0]
    'M6III'
    

Example 4
+++++++++

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> customSimbad = Simbad()
    >>> # We've seen errors where ra_prec was NAN, but it's an int: that's a problem
    >>> # this is a workaround we adapted
    >>> customSimbad.add_votable_fields('ra(d)','dec(d)')
    >>> customSimbad.remove_votable_fields('coordinates')
    >>> from astropy import coordinates
    >>> C = coordinates.SkyCoord(0,0,unit=('deg','deg'), frame='icrs')
    >>> result = customSimbad.query_region(C, radius='2 degrees')
    >>> result[:5].pprint()
        MAIN_ID        RA_d       DEC_d
     ------------- ----------- ------------
     ALFALFA 5-186  0.00000000   0.00000000
     ALFALFA 5-188  0.00000000   0.00000000
     ALFALFA 5-206  0.00000000   0.00000000
     ALFALFA 5-241  0.00000000   0.00000000
     ALFALFA 5-293  0.00000000   0.00000000

Example 5
+++++++++

This illustrates a simple usage of the open_exoplanet_catalogue module.

Finding the mass of a specific planet:

.. code-block:: python

        >>> from astroquery import open_exoplanet_catalogue as oec
        >>> from astroquery.open_exoplanet_catalogue import findvalue
        >>> cata = oec.get_catalogue()
        >>> kepler68b = cata.find(".//planet[name='Kepler-68 b']")
        >>> print findvalue( kepler68b, 'mass')
        0.02105109

Example 6
+++++++++

Grab some data from ALMA, then analyze it using the Spectral Cube package after
identifying some spectral lines in the data.

.. code-block:: python

   from astroquery.alma import Alma
   from astroquery.splatalogue import Splatalogue
   from astroquery.simbad import Simbad
   from astropy import units as u
   from astropy import constants
   from spectral_cube import SpectralCube

   m83table = Alma.query_object('M83', public=True)
   m83urls = Alma.stage_data(m83table['Asdm_uid'])
   # Sometimes there can be duplicates: avoid them with
   # list(set())
   m83files = Alma.download_and_extract_files(list(set(m83urls['URL'])))
   m83files = m83files
   
   Simbad.add_votable_fields('rvel')
   m83simbad = Simbad.query_object('M83')
   rvel = m83simbad['RVel_Rvel'][0]*u.Unit(m83simbad['RVel_Rvel'].unit)

   for fn in m83files:
       if 'line' in fn:
           cube = SpectralCube.read(fn)
           # Convert frequencies to their rest frequencies
           frange = u.Quantity([cube.spectral_axis.min(),
                                cube.spectral_axis.max()]) * (1+rvel/constants.c)

           # Query the top 20 most common species in the frequency range of the
           # cube with an upper energy state <= 50K
           lines = Splatalogue.query_lines(frange[0], frange[1], top20='top20',
                                           energy_max=50, energy_type='eu_k',
                                           only_NRAO_recommended=True)
           lines.pprint()

           # Change the cube coordinate system to be in velocity with respect
           # to the rest frequency (in the M83 rest frame)
           rest_frequency = lines['Freq-GHz'][0]*u.GHz / (1+rvel/constants.c)
           vcube = cube.with_spectral_unit(u.km/u.s,
                                           rest_value=rest_frequency,
                                           velocity_convention='radio')

           # Write the cube with the specified line name
           fmt = "{Species}{Resolved QNs}"
           row = lines[0]
           linename = fmt.format(**dict(zip(row.colnames,row.data)))
           vcube.write('M83_ALMA_{linename}.fits'.format(linename=linename))
