"""
Query ALMA archive for M83 pointings and plotting them on a 2MASS image
"""

import numpy as np
from astroquery.alma import Alma
from astroquery.skyview import SkyView
import string
from astropy import units as u
from astropy.io import fits
from astropy import wcs
from astropy import log
import pylab as pl
import aplpy
import pyregion


# Retrieve M83 2MASS K-band image:
m83_images = SkyView.get_images(position='M83', survey=['2MASS-K'],
                                pixels=1500)

# Retrieve ALMA archive information *including* private data and non-science
# fields:
m83 = Alma.query_object('M83', public=False, science=False)


# Parse components of the ALMA data.  Specifically, find the frequency support
# - the frequency range covered - and convert that into a central frequency for
# beam radius estimation.  
def parse_frequency_support(frequency_support_str):
    supports = frequency_support_str.split("U")
    freq_ranges = [(float(sup.strip('[] ').split("..")[0]),
                    float(sup.strip('[] ')
                          .split("..")[1]
                          .split(', ')[0]
                          .strip(string.ascii_letters)))
                   *u.Unit(sup.strip('[] ')
                           .split("..")[1]
                           .split(', ')[0]
                           .strip(string.punctuation+string.digits))
                   for sup in supports]
    return u.Quantity(freq_ranges)

def approximate_primary_beam_sizes(frequency_support_str):
    freq_ranges = parse_frequency_support(frequency_support_str)
    beam_sizes = [(1.22*fr.mean().to(u.m,
                                     u.spectral())/(12*u.m)).to(u.arcsec,
                                                                u.dimensionless_angles())
                  for fr in freq_ranges]
    return u.Quantity(beam_sizes)


primary_beam_radii = [approximate_primary_beam_sizes(row['Frequency support']) for row in m83]


# Compute primary beam parameters for the public and private components of the data for plotting below.
print("The bands used include: ", np.unique(m83['Band']))

private_circle_parameters = [(row['RA'], row['Dec'], np.mean(rad).to(u.deg).value)
                             for row, rad in zip(m83, primary_beam_radii)
                             if row['Release date']!=b'' and row['Band']==3]
public_circle_parameters = [(row['RA'], row['Dec'], np.mean(rad).to(u.deg).value)
                             for row, rad in zip(m83, primary_beam_radii)
                             if row['Release date']==b'' and row['Band']==3]
unique_private_circle_parameters = np.array(list(set(private_circle_parameters)))
unique_public_circle_parameters = np.array(list(set(public_circle_parameters)))

print("BAND 3")
print("PUBLIC:  Number of rows: {0}.  Unique pointings: {1}".format(len(m83), len(unique_public_circle_parameters)))
print("PRIVATE: Number of rows: {0}.  Unique pointings: {1}".format(len(m83), len(unique_private_circle_parameters)))

private_circle_parameters_band6 = [(row['RA'], row['Dec'], np.mean(rad).to(u.deg).value)
                             for row, rad in zip(m83, primary_beam_radii)
                             if row['Release date']!=b'' and row['Band']==6]
public_circle_parameters_band6 = [(row['RA'], row['Dec'], np.mean(rad).to(u.deg).value)
                             for row, rad in zip(m83, primary_beam_radii)
                             if row['Release date']==b'' and row['Band']==6]


# Show all of the private observation pointings that have been acquired
fig = aplpy.FITSFigure(m83_images[0])
fig.show_grayscale(stretch='arcsinh', vmid=0.1)
fig.show_circles(unique_private_circle_parameters[:, 0],
                 unique_private_circle_parameters[:, 1],
                 unique_private_circle_parameters[:, 2],
                 color='r', alpha=0.2)

fig = aplpy.FITSFigure(m83_images[0])
fig.show_grayscale(stretch='arcsinh', vmid=0.1)
fig.show_circles(unique_public_circle_parameters[:, 0],
                 unique_public_circle_parameters[:, 1],
                 unique_public_circle_parameters[:, 2],
                 color='b', alpha=0.2)


# Use pyregion to write the observed regions to disk.  Pyregion has a very
# awkward API; there is (in principle) work in progress to improve that
# situation but for now one must do all this extra work.

import pyregion
from pyregion.parser_helper import Shape
prv_regions = pyregion.ShapeList([Shape('circle', [x, y, r]) for x, y, r in private_circle_parameters])
pub_regions = pyregion.ShapeList([Shape('circle', [x, y, r]) for x, y, r in public_circle_parameters])
for r, (x, y, c) in zip(prv_regions+pub_regions,
                     np.vstack([private_circle_parameters,
                                public_circle_parameters])):
    r.coord_format = 'fk5'
    r.coord_list = [x, y, c]
    r.attr = ([], {'color': 'green',  'dash': '0 ',  'dashlist': '8 3 ',  'delete': '1 ',  'edit': '1 ',
                   'fixed': '0 ',  'font': '"helvetica 10 normal roman"',  'highlite': '1 ',
                   'include': '1 ',  'move': '1 ',  'select': '1 ',  'source': '1',  'text': '',
                   'width': '1 '})

prv_regions.write('M83_observed_regions_private_March2015.reg')
pub_regions.write('M83_observed_regions_public_March2015.reg')

prv_mask = fits.PrimaryHDU(prv_regions.get_mask(m83_images[0][0]).astype('int'),
                           header=m83_images[0][0].header)
pub_mask = fits.PrimaryHDU(pub_regions.get_mask(m83_images[0][0]).astype('int'),
                           header=m83_images[0][0].header)

pub_mask.writeto('public_m83_almaobs_mask.fits', clobber=True)

fig = aplpy.FITSFigure(m83_images[0])
fig.show_grayscale(stretch='arcsinh', vmid=0.1)
fig.show_contour(prv_mask, levels=[0.5, 1], colors=['r', 'r'])
fig.show_contour(pub_mask, levels=[0.5, 1], colors=['b', 'b'])

# ## More advanced ##
#
# Now we create a 'hit mask' showing the relative depth of each observed field in each band

hit_mask_band3_public = np.zeros_like(m83_images[0][0].data)
hit_mask_band3_private = np.zeros_like(m83_images[0][0].data)
hit_mask_band6_public = np.zeros_like(m83_images[0][0].data)
hit_mask_band6_private = np.zeros_like(m83_images[0][0].data)

mywcs = wcs.WCS(m83_images[0][0].header)

def pyregion_subset(region, data, mywcs):
    """
    Return a subset of an image (`data`) given a region.
    """
    shapelist = pyregion.ShapeList([region])
    if shapelist[0].coord_format not in ('physical', 'image'):
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
        xlo = int(xlo if xlo < ext.min[0] else ext.min[0])
        ylo = int(ylo if ylo < ext.min[1] else ext.min[1])
        xhi = int(xhi if xhi > ext.max[0] else ext.max[0])
        yhi = int(yhi if yhi > ext.max[1] else ext.max[1])

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
    return (xlo, xhi, ylo, yhi), mask


for row, rad in zip(m83, primary_beam_radii):
    shape = Shape('circle', (row['RA'], row['Dec'], np.mean(rad).to(u.deg).value))
    shape.coord_format = 'fk5'
    shape.coord_list = (row['RA'], row['Dec'], np.mean(rad).to(u.deg).value)
    shape.attr = ([], {'color': 'green',  'dash': '0 ',  'dashlist': '8 3 ',
                       'delete': '1 ',  'edit': '1 ', 'fixed': '0 ',
                       'font': '"helvetica 10 normal roman"',  'highlite': '1 ',
                       'include': '1 ',  'move': '1 ',  'select': '1 ',
                       'source': '1',  'text': '', 'width': '1 '})
    if row['Release date']==b'' and row['Band']==3:
        (xlo, xhi, ylo, yhi), mask = pyregion_subset(shape, hit_mask_band3_private, mywcs)
        hit_mask_band3_private[ylo:yhi, xlo:xhi] += row['Integration']*mask
    elif row['Release date'] and row['Band']==3:
        (xlo, xhi, ylo, yhi), mask = pyregion_subset(shape, hit_mask_band3_public, mywcs)
        hit_mask_band3_public[ylo:yhi, xlo:xhi] += row['Integration']*mask
    elif row['Release date'] and row['Band']==6:
        (xlo, xhi, ylo, yhi), mask = pyregion_subset(shape, hit_mask_band6_public, mywcs)
        hit_mask_band6_public[ylo:yhi, xlo:xhi] += row['Integration']*mask
    elif row['Release date']==b'' and row['Band']==6:
        (xlo, xhi, ylo, yhi), mask = pyregion_subset(shape, hit_mask_band6_private, mywcs)
        hit_mask_band6_private[ylo:yhi, xlo:xhi] += row['Integration']*mask


fig = aplpy.FITSFigure(m83_images[0])
fig.show_grayscale(stretch='arcsinh', vmid=0.1)
for mask, color in zip([hit_mask_band3_public,
                        hit_mask_band3_private,
                        hit_mask_band6_public,
                        hit_mask_band6_private,
                       ],
                       'rycb'):

    if np.any(mask):
        fig.show_contour(fits.PrimaryHDU(data=mask, header=m83_images[0][0].header),
                         levels=np.logspace(0, 5, base=2, num=6), colors=[color]*6)
