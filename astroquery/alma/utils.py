"""
Utilities for making finder charts and overlay images for ALMA proposing
"""
import string
import os

import numpy as np

from astropy import wcs
from astropy import log
from astropy import units as u
from astropy.io import fits
from astropy.utils.console import ProgressBar

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
    ALMA "Frequency Support" strings have the form:

    [100.63..101.57GHz,488.28kHz, XX YY] U
    [102.43..103.37GHz,488.28kHz, XX YY] U
    [112.74..113.68GHz,488.28kHz, XX YY] U
    [114.45..115.38GHz,488.28kHz, XX YY]

    at least, as far as we have seen.  The "U" is meant to be the Union symbol.
    This function will parse such a string into a list of pairs of astropy
    Quantities representing the frequency range.  It will ignore the resolution
    and polarizations.
    """
    if not isinstance(frequency_support_str, str):
        supports = frequency_support_str.tostring().decode('ascii').split('U')
    else:
        supports = frequency_support_str.split('U')

    freq_ranges = [(float(sup[0]),
                    float(sup[1].split(',')[0].strip(string.ascii_letters))) *
                   u.Unit(sup[1].split(',')[0].strip(string.punctuation +
                                                     string.digits))
                   for i in supports for sup in [i.strip('[] ').split('..'), ]]
    return u.Quantity(freq_ranges)


def approximate_primary_beam_sizes(frequency_support_str,
                                   dish_diameter=12 * u.m, first_null=1.220):
    """
    Using parse_frequency_support, determine the mean primary beam size in each
    observed band

    Parameters
    ----------
    frequency_support_str : str
        The frequency support string, see `parse_frequency_support`
    dish_diameter : `~astropy.units.Quantity`
        Meter-equivalent unit.  The diameter of the dish.
    first_null : float
        The position of the first null of an Airy.  Used to compute resolution
        as :math:`R = 1.22 \lambda/D`
    """
    freq_ranges = parse_frequency_support(frequency_support_str)
    beam_sizes = [(first_null * fr.mean().to(u.m, u.spectral()) /
                   (dish_diameter)).to(u.arcsec, u.dimensionless_angles())
                  for fr in freq_ranges]
    return u.Quantity(beam_sizes)


def make_finder_chart(target, radius, save_prefix, service=SkyView.get_images,
                      service_kwargs={'survey': ['2MASS-K'], 'pixels': 500},
                      alma_kwargs={'public': False, 'science': False},
                      **kwargs):
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
    log.info("Querying {0} for images".format(service))
    images = service(target, radius=radius, **service_kwargs)

    image0_hdu = images[0][0]

    return make_finder_chart_from_image(image0_hdu, target=target,
                                        radius=radius, save_prefix=save_prefix,
                                        alma_kwargs=alma_kwargs,
                                        **kwargs)

def make_finder_chart_from_image(image, target, radius, save_prefix,
                                 alma_kwargs={'public': False,
                                              'science': False},
                                 **kwargs):
    """
    Create a "finder chart" showing where ALMA has pointed in various bands,
    including different color coding for public/private data and each band.

    Contours are set at various integration times.

    Parameters
    ----------
    image : fits.PrimaryHDU or fits.ImageHDU object
        The image to overlay onto
    target : `astropy.coordinates` or str
        A legitimate target name
    radius : `astropy.units.Quantity`
        A degree-equivalent radius
    save_prefix : str
        The prefix for the output files.  Both .reg and .png files will be
        written.  The .reg files will have the band numbers and
        public/private appended, while the .png file will be named
        prefix_almafinderchart.png
    alma_kwargs : dict
        Keywords to pass to the ALMA archive when querying.
    private_band_colors / public_band_colors : tuple
        A tuple or list of colors to be associated with private/public
        observations in the various bands
    integration_time_contour_levels : list or np.array
        The levels at which to draw contours in units of seconds.  Default is
        log-spaced (2^n) seconds: [  1.,   2.,   4.,   8.,  16.,  32.])
    """
    log.info("Querying ALMA around {0}".format(target))
    catalog = Alma.query_region(coordinate=target, radius=radius,
                                **alma_kwargs)

    return make_finder_chart_from_image_and_catalog(image, catalog=catalog,
                                                    save_prefix=save_prefix,
                                                    **kwargs)

def make_finder_chart_from_image_and_catalog(image, catalog, save_prefix,
                                             alma_kwargs={'public': False,
                                                          'science': False},
                                             bands=(3,4,5,6,7,8,9),
                                             private_band_colors=('maroon',
                                                                  'red',
                                                                  'orange',
                                                                  'coral',
                                                                  'brown',
                                                                  'yellow',
                                                                  'mediumorchid'),
                                             public_band_colors=('blue',
                                                                 'cyan',
                                                                 'green',
                                                                 'turquoise',
                                                                 'teal',
                                                                 'darkslategrey',
                                                                 'chartreuse'),
                                             integration_time_contour_levels=np.logspace(0,
                                                                                         5,
                                                                                         base=2,
                                                                                         num=6),
                                             save_masks=False,
                                             use_saved_masks=False,
                                            ):
    """
    Create a "finder chart" showing where ALMA has pointed in various bands,
    including different color coding for public/private data and each band.

    Contours are set at various integration times.

    Parameters
    ----------
    image : fits.PrimaryHDU or fits.ImageHDU object
        The image to overlay onto
    catalog : astropy.Table object
        The catalog of ALMA observations
    save_prefix : str
        The prefix for the output files.  Both .reg and .png files will be
        written.  The .reg files will have the band numbers and
        public/private appended, while the .png file will be named
        prefix_almafinderchart.png
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



    primary_beam_radii = [
        approximate_primary_beam_sizes(row['Frequency support'])
        for row in catalog]

    all_bands = bands
    bands = used_bands = np.unique(catalog['Band'])
    log.info("The bands used include: {0}".format(used_bands))
    band_colors_priv = dict(zip(all_bands, private_band_colors))
    band_colors_pub = dict(zip(all_bands, public_band_colors))
    log.info("Color map private: {0}".format(band_colors_priv))
    log.info("Color map public: {0}".format(band_colors_pub))

    if use_saved_masks:
        hit_mask_public = {}
        hit_mask_private = {}

        for band in bands:
            pubfile = '{0}_band{1}_public.fits'.format(save_prefix, band)
            if os.path.exists(pubfile):
                hit_mask_public[band] = fits.getdata(pubfile)
            privfile = '{0}_band{1}_private.fits'.format(save_prefix, band)
            if os.path.exists(privfile):
                hit_mask_private[band] = fits.getdata(privfile)

    else:
        today = np.datetime64('today')

        private_circle_parameters = {
            band: [(row['RA'], row['Dec'], np.mean(rad).to(u.deg).value)
                   for row, rad in zip(catalog, primary_beam_radii)
                   if not row['Release date'] or
                   (np.datetime64(row['Release date']) > today and row['Band'] == band)]
            for band in bands}

        public_circle_parameters = {
            band: [(row['RA'], row['Dec'], np.mean(rad).to(u.deg).value)
                   for row, rad in zip(catalog, primary_beam_radii)
                   if row['Release date'] and
                   (np.datetime64(row['Release date']) <= today and row['Band'] == band)]
            for band in bands}

        unique_private_circle_parameters = {
            band: np.array(list(set(private_circle_parameters[band])))
            for band in bands}
        unique_public_circle_parameters = {
            band: np.array(list(set(public_circle_parameters[band])))
            for band in bands}

        release_dates = np.array(catalog['Release date'], dtype=np.datetime64)

        for band in bands:
            log.info("BAND {0}".format(band))
            privrows = sum((catalog['Band'] == band) &
                           (release_dates > today))
            pubrows = sum((catalog['Band'] == band) &
                          (release_dates <= today))
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
                prv_regions[band].get_mask(image).astype('int'),
                header=image.header) for band in bands if prv_regions[band]}
        pub_mask = {
            band: fits.PrimaryHDU(
                pub_regions[band].get_mask(image).astype('int'),
                header=image.header) for band in bands if pub_regions[band]}

        hit_mask_public = {band: np.zeros_like(image.data)
                           for band in pub_mask}
        hit_mask_private = {band: np.zeros_like(image.data)
                            for band in prv_mask}
        mywcs = wcs.WCS(image.header)

        for band in bands:
            log.debug('Band: {0}'.format(band))
            for row, rad in ProgressBar(list(zip(catalog, primary_beam_radii))):
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

                if not row['Release date']:
                    reldate = False
                else:
                    reldate = np.datetime64(row['Release date'])

                if (((not reldate) or (reldate > today)) and
                    (row['Band'] == band) and
                    (band in prv_mask)
                   ):
                    # private: release_date = 'sometime' says when it will be released
                    (xlo, xhi, ylo, yhi), mask = pyregion_subset(
                        shape, hit_mask_private[band], mywcs)
                    log.debug("{0},{1},{2},{3}: {4}"
                              .format(xlo, xhi, ylo, yhi, mask.sum()))
                    hit_mask_private[band][ylo:yhi, xlo:xhi] += row['Integration']*mask
                elif (reldate and (reldate <= today) and (row['Band'] == band) and
                      (band in pub_mask)):
                    # public: release_date = '' should mean already released
                    (xlo, xhi, ylo, yhi), mask = pyregion_subset(
                        shape, hit_mask_public[band], mywcs)
                    log.debug("{0},{1},{2},{3}: {4}"
                              .format(xlo, xhi, ylo, yhi, mask.sum()))
                    hit_mask_public[band][ylo:yhi, xlo:xhi] += row['Integration']*mask

        if save_masks:
            for band in bands:
                if band in hit_mask_public:
                    hdu = fits.PrimaryHDU(data=hit_mask_public[band],
                                          header=image.header)
                    hdu.writeto('{0}_band{1}_public.fits'.format(save_prefix, band),
                                clobber=True)
                if band in hit_mask_private:
                    hdu = fits.PrimaryHDU(data=hit_mask_private[band],
                                          header=image.header)
                    hdu.writeto('{0}_band{1}_private.fits'.format(save_prefix, band),
                                clobber=True)

    fig = aplpy.FITSFigure(fits.HDUList(image), convention='calabretta')
    fig.show_grayscale(stretch='arcsinh')
    for band in bands:
        if band in hit_mask_public:
            fig.show_contour(fits.PrimaryHDU(data=hit_mask_public[band],
                                             header=image.header),
                             levels=integration_time_contour_levels,
                             colors=[band_colors_pub[band]] * len(integration_time_contour_levels),
                             convention='calabretta')
        if band in hit_mask_private:
            fig.show_contour(fits.PrimaryHDU(data=hit_mask_private[band],
                                             header=image.header),
                             levels=integration_time_contour_levels,
                             colors=[band_colors_priv[band]] * len(integration_time_contour_levels),
                             convention='calabretta')

    fig.save('{0}_almafinderchart.png'.format(save_prefix))

    return image, catalog, hit_mask_public, hit_mask_private

