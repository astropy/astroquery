"""
Example 10
++++++++++
Retrieve Hubble archival data of M83 and make a figure
"""
from astroquery.mast import Mast, Observations
from astropy.visualization import make_lupton_rgb, ImageNormalize
import matplotlib.pyplot as plt
import reproject

result = Observations.query_object('M83')
selected_bands = result[(result['obs_collection'] == 'HST') &
                        (result['instrument_name'] == 'WFC3/UVIS') &
                        ((result['filters'] == 'F657N') |
                         (result['filters'] == 'F487N') |
                         (result['filters'] == 'F336W')) &
                        (result['target_name'] == 'MESSIER-083')]
prodlist = Observations.get_product_list(selected_bands)
filtered_prodlist = Observations.filter_products(prodlist)

downloaded = Observations.download_products(filtered_prodlist)

blue = fits.open(downloaded['Local Path'][2])
red = fits.open(downloaded['Local Path'][5])
green = fits.open(downloaded['Local Path'][8])

target_header = red['SCI'].header
green_repr, _ = reproject.reproject_interp(green['SCI'], target_header)
blue_repr, _ = reproject.reproject_interp(blue['SCI'], target_header)


rgb_img = make_lupton_rgb(ImageNormalize(vmin=0, vmax=1)(red['SCI'].data),
                          ImageNormalize(vmin=0, vmax=0.3)(green_repr),
                          ImageNormalize(vmin=0, vmax=1)(blue_repr),
                          stretch=0.1,
                          minimum=0,
                         )

plt.imshow(rgb_img, origin='lower', interpolation='none')
