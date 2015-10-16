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
   m83urls = Alma.stage_data(m83table['Member ous id'])
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

.. _gallery-almaskyview:

Example 7
+++++++++
Find ALMA pointings that have been observed toward M83, then overplot the
various fields-of view on a 2MASS image retrieved from SkyView.  See
http://nbviewer.ipython.org/gist/keflavich/19175791176e8d1fb204 for the
notebook.  There is an even more sophisticated version at
http://nbviewer.ipython.org/gist/keflavich/bb12b772d6668cf9181a, which shows
Orion KL in all observed bands.

.. code-block:: python

    # Querying ALMA archive for M83 pointings and plotting them on a 2MASS image

    # In[2]:

    from astroquery.alma import Alma
    from astroquery.skyview import SkyView
    import string
    from astropy import units as u
    import pylab as pl
    import aplpy


    # Retrieve M83 2MASS K-band image:

    # In[3]:

    m83_images = SkyView.get_images(position='M83', survey=['2MASS-K'], pixels=1500)


    # Retrieve ALMA archive information *including* private data and non-science fields:
    # 

    # In[4]:

    m83 = Alma.query_object('M83', public=False, science=False)


    # In[5]:

    m83


    # Parse components of the ALMA data.  Specifically, find the frequency support - the frequency range covered - and convert that into a central frequency for beam radius estimation.

    # In[6]:

    def parse_frequency_support(frequency_support_str):
        supports = frequency_support_str.split("U")
        freq_ranges = [(float(sup.strip('[] ').split("..")[0]),
                        float(sup.strip('[] ').split("..")[1].split(',')[0].strip(string.letters)))
                       *u.Unit(sup.strip('[] ').split("..")[1].split(',')[0].strip(string.punctuation+string.digits))
                       for sup in supports]
        return u.Quantity(freq_ranges)

    def approximate_primary_beam_sizes(frequency_support_str):
        freq_ranges = parse_frequency_support(frequency_support_str)
        beam_sizes = [(1.22*fr.mean().to(u.m, u.spectral())/(12*u.m)).to(u.arcsec,
                                                                         u.dimensionless_angles())
                      for fr in freq_ranges]
        return u.Quantity(beam_sizes)


    # In[7]:

    primary_beam_radii = [approximate_primary_beam_sizes(row['Frequency support']) for row in m83]


    # Compute primary beam parameters for the public and private components of the data for plotting below.

    # In[8]:

    print "The bands used include: ",np.unique(m83['Band'])


    # In[9]:

    private_circle_parameters = [(row['RA'],row['Dec'],np.mean(rad).to(u.deg).value)
                                 for row,rad in zip(m83, primary_beam_radii)
                                 if row['Release date']!='' and row['Band']==3]
    public_circle_parameters = [(row['RA'],row['Dec'],np.mean(rad).to(u.deg).value)
                                 for row,rad in zip(m83, primary_beam_radii)
                                 if row['Release date']=='' and row['Band']==3]
    unique_private_circle_parameters = np.array(list(set(private_circle_parameters)))
    unique_public_circle_parameters = np.array(list(set(public_circle_parameters)))

    print "BAND 3"
    print "PUBLIC:  Number of rows: {0}.  Unique pointings: {1}".format(len(m83), len(unique_public_circle_parameters))
    print "PRIVATE: Number of rows: {0}.  Unique pointings: {1}".format(len(m83), len(unique_private_circle_parameters))

    private_circle_parameters_band6 = [(row['RA'],row['Dec'],np.mean(rad).to(u.deg).value)
                                 for row,rad in zip(m83, primary_beam_radii)
                                 if row['Release date']!='' and row['Band']==6]
    public_circle_parameters_band6 = [(row['RA'],row['Dec'],np.mean(rad).to(u.deg).value)
                                 for row,rad in zip(m83, primary_beam_radii)
                                 if row['Release date']=='' and row['Band']==6]


    # Show all of the private observation pointings that have been acquired

    # In[10]:

    fig = aplpy.FITSFigure(m83_images[0])
    fig.show_grayscale(stretch='arcsinh')
    fig.show_circles(unique_private_circle_parameters[:,0],
                     unique_private_circle_parameters[:,1],
                     unique_private_circle_parameters[:,2],
                     color='r', alpha=0.2)


    # In principle, all of the pointings shown below should be downloadable from the archive:

    # In[11]:

    fig = aplpy.FITSFigure(m83_images[0])
    fig.show_grayscale(stretch='arcsinh')
    fig.show_circles(unique_public_circle_parameters[:,0],
                     unique_public_circle_parameters[:,1],
                     unique_public_circle_parameters[:,2],
                     color='b', alpha=0.2)


    # Use pyregion to write the observed regions to disk.  Pyregion has a very awkward API; there is (in principle) work in progress to improve that situation but for now one must do all this extra work.

    # In[16]:

    import pyregion
    from pyregion.parser_helper import Shape
    prv_regions = pyregion.ShapeList([Shape('circle',[x,y,r]) for x,y,r in private_circle_parameters])
    pub_regions = pyregion.ShapeList([Shape('circle',[x,y,r]) for x,y,r in public_circle_parameters])
    for r,(x,y,c) in zip(prv_regions+pub_regions,
                         np.vstack([private_circle_parameters,
                                    public_circle_parameters])):
        r.coord_format = 'fk5'
        r.coord_list = [x,y,c]
        r.attr = ([], {'color': 'green',  'dash': '0 ',  'dashlist': '8 3 ',  'delete': '1 ',  'edit': '1 ',
                       'fixed': '0 ',  'font': '"helvetica 10 normal roman"',  'highlite': '1 ',
                       'include': '1 ',  'move': '1 ',  'select': '1 ',  'source': '1',  'text': '',
                       'width': '1 '})
    
    prv_regions.write('M83_observed_regions_private_March2015.reg')
    pub_regions.write('M83_observed_regions_public_March2015.reg')


    # In[17]:

    from astropy.io import fits


    # In[18]:

    prv_mask = fits.PrimaryHDU(prv_regions.get_mask(m83_images[0][0]).astype('int'),
                               header=m83_images[0][0].header)
    pub_mask = fits.PrimaryHDU(pub_regions.get_mask(m83_images[0][0]).astype('int'),
                               header=m83_images[0][0].header)


    # In[19]:

    pub_mask.writeto('public_m83_almaobs_mask.fits', clobber=True)


    # In[20]:

    fig = aplpy.FITSFigure(m83_images[0])
    fig.show_grayscale(stretch='arcsinh')
    fig.show_contour(prv_mask, levels=[0.5,1], colors=['r','r'])
    fig.show_contour(pub_mask, levels=[0.5,1], colors=['b','b'])


    # ## More advanced ##
    # 
    # Now we create a 'hit mask' showing the relative depth of each observed field in each band

    # In[21]:

    hit_mask_band3_public = np.zeros_like(m83_images[0][0].data)
    hit_mask_band3_private = np.zeros_like(m83_images[0][0].data)
    hit_mask_band6_public = np.zeros_like(m83_images[0][0].data)
    hit_mask_band6_private = np.zeros_like(m83_images[0][0].data)
    from astropy import wcs
    mywcs = wcs.WCS(m83_images[0][0].header)


    # In[22]:

    for row,rad in zip(m83, primary_beam_radii):
        shape = Shape('circle', (row['RA'], row['Dec'],np.mean(rad).to(u.deg).value))
        shape.coord_format = 'fk5'
        shape.coord_list = (row['RA'], row['Dec'],np.mean(rad).to(u.deg).value)
        shape.attr = ([], {'color': 'green',  'dash': '0 ',  'dashlist': '8 3 ',  'delete': '1 ',  'edit': '1 ',
                       'fixed': '0 ',  'font': '"helvetica 10 normal roman"',  'highlite': '1 ',
                       'include': '1 ',  'move': '1 ',  'select': '1 ',  'source': '1',  'text': '',
                       'width': '1 '})
        if row['Release date']=='' and row['Band']==3:
            (xlo,xhi,ylo,yhi),mask = pyregion_subset(shape, hit_mask_band3_private, mywcs) 
            hit_mask_band3_private[ylo:yhi,xlo:xhi] += row['Integration']*mask
        elif row['Release date'] and row['Band']==3:
            (xlo,xhi,ylo,yhi),mask = pyregion_subset(shape, hit_mask_band3_public, mywcs)
            hit_mask_band3_public[ylo:yhi,xlo:xhi] += row['Integration']*mask
        elif row['Release date'] and row['Band']==6:
            (xlo,xhi,ylo,yhi),mask = pyregion_subset(shape, hit_mask_band6_public, mywcs)
            hit_mask_band6_public[ylo:yhi,xlo:xhi] += row['Integration']*mask
        elif row['Release date']=='' and row['Band']==6:
            (xlo,xhi,ylo,yhi),mask = pyregion_subset(shape, hit_mask_band6_private, mywcs)
            hit_mask_band6_private[ylo:yhi,xlo:xhi] += row['Integration']*mask


    # In[23]:

    fig = aplpy.FITSFigure(m83_images[0])
    fig.show_grayscale(stretch='arcsinh')
    fig.show_contour(fits.PrimaryHDU(data=hit_mask_band3_public, header=m83_images[0][0].header),
                     levels=np.logspace(0,5,base=2, num=6), colors=['r']*6)
    fig.show_contour(fits.PrimaryHDU(data=hit_mask_band3_private, header=m83_images[0][0].header),
                     levels=np.logspace(0,5,base=2, num=6), colors=['y']*6)
    fig.show_contour(fits.PrimaryHDU(data=hit_mask_band6_public, header=m83_images[0][0].header),
                     levels=np.logspace(0,5,base=2, num=6), colors=['c']*6)
    fig.show_contour(fits.PrimaryHDU(data=hit_mask_band6_private, header=m83_images[0][0].header),
                     levels=np.logspace(0,5,base=2, num=6), colors=['b']*6)


    # In[24]:

    from astropy import wcs
    import pyregion
    from astropy import log

    def pyregion_subset(region, data, mywcs):
        """
        Return a subset of an image (`data`) given a region.
        """
        shapelist = pyregion.ShapeList([region])
        if shapelist[0].coord_format not in ('physical','image'):
            # Requires astropy >0.4...
            # pixel_regions = shapelist.as_imagecoord(self.wcs.celestial.to_header())
            # convert the regions to image (pixel) coordinates
            celhdr = mywcs.sub([wcs.WCSSUB_CELESTIAL]).to_header()
            pixel_regions = shapelist.as_imagecoord(celhdr)
        else:
            # For this to work, we'd need to change the reference pixel after cropping.
            # Alternatively, we can just make the full-sized mask... todo....
            raise NotImplementedError("Can't use non-celestial coordinates with regions.")
            pixel_regions = shapelist

        # This is a hack to use mpl to determine the outer bounds of the regions
        # (but it's a legit hack - pyregion needs a major internal refactor
        # before we can approach this any other way, I think -AG)
        mpl_objs = pixel_regions.get_mpl_patches_texts()[0]

        # Find the minimal enclosing box containing all of the regions
        # (this will speed up the mask creation below)
        extent = mpl_objs[0].get_extents()
        xlo, ylo = extent.min
        xhi, yhi = extent.max
        all_extents = [obj.get_extents() for obj in mpl_objs]
        for ext in all_extents:
            xlo = xlo if xlo < ext.min[0] else ext.min[0]
            ylo = ylo if ylo < ext.min[1] else ext.min[1]
            xhi = xhi if xhi > ext.max[0] else ext.max[0]
            yhi = yhi if yhi > ext.max[1] else ext.max[1]

        log.debug("Region boundaries: ")
        log.debug("xlo={xlo}, ylo={ylo}, xhi={xhi}, yhi={yhi}".format(xlo=xlo,
                                                                      ylo=ylo,
                                                                      xhi=xhi,
                                                                      yhi=yhi))

    
        subwcs = mywcs[ylo:yhi, xlo:xhi]
        subhdr = subwcs.sub([wcs.WCSSUB_CELESTIAL]).to_header()
        subdata = data[ylo:yhi, xlo:xhi]
    
        mask = shapelist.get_mask(header=subhdr,
                                  shape=subdata.shape)
        log.debug("Shapes: data={0}, subdata={2}, mask={1}".format(data.shape, mask.shape, subdata.shape))
        return (xlo,xhi,ylo,yhi),mask

Example 8
+++++++++

Retrieve data from a particular co-I or PI from the ESO archive

.. code-block:: python

   from astroquery.eso import Eso
   
   # log in so you can get proprietary data
   Eso.login('aginsburg')
   # make sure you don't filter out anything
   Eso.ROW_LIMIT = 1e6

   # List all of your pi/co projects
   all_pi_proj = Eso.query_instrument('apex', pi_coi='ginsburg')

   # Have a look at the project IDs only
   print(set(all_pi_proj['APEX Project ID']))
   # set(['E-095.F-9802A-2015', 'E-095.C-0242A-2015', 'E-093.C-0144A-2014'])

   # The full project name includes prefix and suffix
   full_proj = 'E-095.F-9802A-2015'
   proj_id = full_proj[2:-6]

   # Then get the APEX quicklook "reduced" data
   tbl = Eso.query_apex_quicklooks(prog_id=proj_id)

   # and finally, download it
   files = Eso.retrieve_data(tbl['Product ID'])

   # then move the files to your local directory
   # note that there is no .TAR suffix... not sure why this is
   import shutil
   for fn in files:
       shutil.move(fn+'.TAR','.')
