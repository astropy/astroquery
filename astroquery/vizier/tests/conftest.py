# Licensed under a 3-clause BSD style license - see LICENSE.rst

from astropy import units as u
from astropy.coordinates import SkyCoord


scalar_skycoord = SkyCoord(ra=299.590 * u.deg, dec=35.201 * u.deg, frame="icrs")
vector_skycoord = SkyCoord(
    ra=[299.590, 299.90] * u.deg, dec=[35.201, 35.201] * u.deg, frame="icrs")
