"""Make the TeVCat file ``data/tevcat.html` for local testing."""

import json
from astroquery.tevcat.core import _TeVCat

t = _TeVCat()

t._download_data()
t._extract_version()
t._extract_data()
t._make_table(with_notes=True)

# Make tevcata.fits.gz file for inclusion in Gammapy
t.table.remove_columns(['notes', 'private_notes', 'greens_cat'])
t.table.write('tevcat.fits.gz', overwrite=True)

#open('tevcat.html', 'w').write(t.response.text)
#json.dump(t._sources, open('tevcat.json', 'w'))
