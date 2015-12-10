"""
Utilities for making finder charts and overlay images for ALMA proposing
"""
import string

import numpy as np

from astropy import wcs
from astropy import log
from astropy import units as u
from astropy.io import fits

from astroquery.skyview import SkyView
from astroquery.alma import Alma


def pyregion_subset(region, data, mywcs):
    """
    Return a subset of an image (`data`) given a region.

    Parameters
    ----------
    region : `pyregion.parser_helper.Shape`
        A Shape from a pyregion-parsed region file
    data : np.ndarray
        An array with shape described by WCS
    mywcs : `astropy.wcs.WCS`
        A world coordinate system describing the data
    """
    import pyregion

    shapelist = pyregion.ShapeList([region])
    if shapelist[0].coord_format not in ('physical', 'image'):
        # Requires astropy >0.4...
        # pixel_regions = shapelist.as_imagecoord(
        #     self.wcs.celestial.to_header())
        # convert the regions to image (pixel) coordinates
        celhdr = mywcs.sub([wcs.WCSSUB_CELESTIAL]).to_header()
        pixel_regions = shapelist.as_imagecoord(celhdr)
    else:
        # For this to work, we'd need to change the reference pixel after
        # cropping.  Alternatively, we can just make the full-sized
        # mask... todo....
        raise NotImplementedError("Can't use non-celestial coordinates "
                                  "with regions.")
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
    log.debug("Shapes: data={0}, subdata={2}, mask={1}"
              .format(data.shape, mask.shape, subdata.shape))
    return (xlo, xhi, ylo, yhi), mask


def parse_frequency_support(frequency_support_str):
    """
    Given a "Frequency Support" string from ALMA queries, parse it into a set
    of frequency ranges

    Example input:

    '[86.26..88.14GHz,976.56kHz, XX YY] U [88.15..90.03GHz,976.56kHz, XX YY] U [98.19..100.07GHz,976.56kHz, XX YY] U [100.15..102.03GHz,976.56kHz, XX YY]'
    """
    supports = str(frequency_support_str).split('U')

    freq_ranges = [(float(sup[0]),
                    float(sup[1].split(',')[0].strip(string.ascii_letters))) *
                   u.Unit(sup[1].split(',')[0].strip(string.punctuation +
                                                     string.digits))
                   for i in supports for sup in [i.strip('[] ').split('..'), ]]
    return u.Quantity(freq_ranges)


def approximate_primary_beam_sizes(frequency_support_str):
    """
    Given a frequency support string, return the approximate 12m array beam
    size using 1.22 lambda / D
    """
    freq_ranges = parse_frequency_support(frequency_support_str)
    beam_sizes = [(1.22 * fr.mean().to(u.m, u.spectral()) /
                   (12 * u.m)).to(u.arcsec, u.dimensionless_angles())
                  for fr in freq_ranges]
    return u.Quantity(beam_sizes)


def make_finder_chart(target, radius, save_prefix, service=SkyView.get_images,
                      service_kwargs={'survey': ['2MASS-K'], 'pixels': 500},
                      alma_kwargs={'public': False, 'science': False},
                      private_band_colors=('red', 'darkred', 'orange',
                                           'brown', 'maroon'),
                      public_band_colors=('blue', 'cyan', 'green',
                                          'turquoise', 'teal'),
                      integration_time_contour_levels=np.logspace(0, 5, base=2,
                                                                  num=6),
                      ):
    """
    Create a "finder chart" showing where ALMA has pointed in various bands,
    including different color coding for public/private data and each band.

    Contours are set at various integration times.

    Parameters
    ----------
    target : `astropy.coordinates` or str
        A legitimate target name
    radius : `astropy.units.Quantity`
        A degree-equivalent radius
    save_prefix : str
        The prefix for the output files.  Both .reg and .png files will be
        written.  The .reg files will have the band numbers and
        public/private appended, while the .png file will be named
        prefix_almafinderchart.png
    service : function
        The `get_images` function of an astroquery service, e.g. SkyView.
    service_kwargs : dict
        The keyword arguments to pass to the specified service.  For example,
        for SkyView, you can give it the survey ID (e.g., 2MASS-K) and the
        number of pixels in the resulting image.  See the documentation for the
        individual services for more details.
    alma_kwargs : dict
        Keywords to pass to the ALMA archive when querying.
    private_band_colors / public_band_colors : tuple
        A tuple or list of colors to be associated with private/public
        observations in the various bands
    integration_time_contour_levels : list or np.array
        The levels at which to draw contours in units of seconds.  Default is
        log-spaced (2^n) seconds: [  1.,   2.,   4.,   8.,  16.,  32.])
    """
    import aplpy

    import pyregion
    from pyregion.parser_helper import Shape

    log.info("Querying {0} for images".format(service))
    images = service(target, radius=radius, **service_kwargs)

    log.info("Querying ALMA around {0}".format(target))
    catalog = Alma.query_region(coordinate=target, radius=radius,
                                **alma_kwargs)

    primary_beam_radii = [
        approximate_primary_beam_sizes(row['Frequency support'])
        for row in catalog]

    bands = np.unique(catalog['Band'])
    log.info("The bands used include: {0}".format(bands))
    band_colors_priv = dict(zip(bands, private_band_colors))
    band_colors_pub = dict(zip(bands, public_band_colors))

    private_circle_parameters = {
        band: [(row['RA'], row['Dec'], np.mean(rad).to(u.deg).value)
               for row, rad in zip(catalog, primary_beam_radii)
               if row['Release date'] != '' and row['Band'] == band]
        for band in bands}

    public_circle_parameters = {
        band: [(row['RA'], row['Dec'], np.mean(rad).to(u.deg).value)
               for row, rad in zip(catalog, primary_beam_radii)
               if row['Release date'] == '' and row['Band'] == band]
        for band in bands}

    unique_private_circle_parameters = {
        band: np.array(list(set(private_circle_parameters[band])))
        for band in bands}
    unique_public_circle_parameters = {
        band: np.array(list(set(public_circle_parameters[band])))
        for band in bands}

    for band in bands:
        log.info("BAND {0}".format(band))
        privrows = sum((catalog['Band'] == band) &
                       (catalog['Release date'] != ''))
        pubrows = sum((catalog['Band'] == band) &
                      (catalog['Release date'] == ''))
        log.info("PUBLIC:  Number of rows: {0}.  Unique pointings: "
                 "{1}".format(pubrows,
                              len(unique_public_circle_parameters[band])))
        log.info("PRIVATE: Number of rows: {0}.  Unique pointings: "
                 "{1}".format(privrows,
                              len(unique_private_circle_parameters[band])))

    prv_regions = {
        band: pyregion.ShapeList([Shape('circle', [x, y, r]) for x, y, r
                                  in private_circle_parameters[band]])
        for band in bands}
    pub_regions = {
        band: pyregion.ShapeList([Shape('circle', [x, y, r]) for x, y, r
                                  in public_circle_parameters[band]])
        for band in bands}
    for band in bands:
        circle_pars = np.vstack(
            [x for x in (private_circle_parameters[band],
                         public_circle_parameters[band]) if any(x)])
        for r, (x, y, c) in zip(prv_regions[band] + pub_regions[band],
                                circle_pars):
            r.coord_format = 'fk5'
            r.coord_list = [x, y, c]
            r.attr = ([], {'color': 'green', 'dash': '0 ', 'dashlist': '8 3',
                           'delete': '1 ', 'edit': '1 ', 'fixed': '0 ',
                           'font': '"helvetica 10 normal roman"', 'highlite':
                           '1 ', 'include': '1 ', 'move': '1 ', 'select': '1',
                           'source': '1', 'text': '', 'width': '1 '})

        if prv_regions[band]:
            prv_regions[band].write(
                '{0}_band{1}_private.reg'.format(save_prefix, band))
        if pub_regions[band]:
            pub_regions[band].write(
                '{0}_band{1}_public.reg'.format(save_prefix, band))

    prv_mask = {
        band: fits.PrimaryHDU(
            prv_regions[band].get_mask(images[0][0]).astype('int'),
            header=images[0][0].header) for band in bands if prv_regions[band]}
    pub_mask = {
        band: fits.PrimaryHDU(
            pub_regions[band].get_mask(images[0][0]).astype('int'),
            header=images[0][0].header) for band in bands if pub_regions[band]}

    hit_mask_public = {band: np.zeros_like(images[0][0].data)
                       for band in pub_mask}
    hit_mask_private = {band: np.zeros_like(images[0][0].data)
                        for band in prv_mask}
    mywcs = wcs.WCS(images[0][0].header)

    for band in bands:
        log.debug('Band: {0}'.format(band))
        for row, rad in zip(catalog, primary_beam_radii):
            shape = Shape('circle', (row['RA'], row['Dec'],
                                     np.mean(rad).to(u.deg).value))
            shape.coord_format = 'fk5'
            shape.coord_list = (row['RA'], row['Dec'],
                                np.mean(rad).to(u.deg).value)
            shape.attr = ([], {'color': 'green', 'dash': '0 ',
                               'dashlist': '8 3 ',
                               'delete': '1 ', 'edit': '1 ', 'fixed': '0 ',
                               'font': '"helvetica 10 normal roman"',
                               'highlite': '1 ', 'include': '1 ', 'move': '1 ',
                               'select': '1 ', 'source': '1', 'text': '',
                               'width': '1 '})
            log.debug('{1} {2}: {0}'
                      .format(shape, row['Release date'], row['Band']))
            if (row['Release date'] != '' and row['Band'] == band and
                    band in prv_mask):
                (xlo, xhi, ylo, yhi), mask = pyregion_subset(
                    shape, hit_mask_private[band], mywcs)
                log.debug("{0},{1},{2},{3}: {4}"
                          .format(xlo, xhi, ylo, yhi, mask.sum()))
                hit_mask_private[band][ylo:yhi, xlo:xhi] += row['Integration']*mask
            if (row['Release date'] == '' and row['Band'] == band and
                    band in pub_mask):
                (xlo, xhi, ylo, yhi), mask = pyregion_subset(
                    shape, hit_mask_public[band], mywcs)
                log.debug("{0},{1},{2},{3}: {4}"
                          .format(xlo, xhi, ylo, yhi, mask.sum()))
                hit_mask_public[band][ylo:yhi, xlo:xhi] += row['Integration']*mask

    fig = aplpy.FITSFigure(images[0])
    fig.show_grayscale(stretch='arcsinh')
    for band in bands:
        if band in pub_mask:
            fig.show_contour(fits.PrimaryHDU(data=hit_mask_public[band],
                                             header=images[0][0].header),
                             levels=integration_time_contour_levels,
                             colors=[band_colors_pub[band]] * 6)
        if band in prv_mask:
            fig.show_contour(fits.PrimaryHDU(data=hit_mask_private[band],
                                             header=images[0][0].header),
                             levels=integration_time_contour_levels,
                             colors=[band_colors_priv[band]] * 6)

    fig.save('{0}_almafinderchart.png'.format(save_prefix))

    return images, catalog, hit_mask_public, hit_mask_private
