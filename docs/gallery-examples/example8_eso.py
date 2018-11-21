from astroquery.eso import Eso
import shutil

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
for fn in files:
    shutil.move(fn, '.')
