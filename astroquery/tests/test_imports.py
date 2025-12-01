# Licensed under a 3-clause BSD style license - see LICENSE.rst
import sys
import importlib
import pytest
from unittest.mock import patch
from pytest_remotedata.disable_internet import no_internet

# List of all astroquery modules to test
ASTROQUERY_MODULES = [
    'astroquery.alma',
    'astroquery.astrometry_net',
    'astroquery.besancon',
    'astroquery.cadc',
    'astroquery.cosmosim',
    'astroquery.esa',
    'astroquery.esasky',
    'astroquery.eso',
    'astroquery.exoplanet_orbit_database',
    'astroquery.fermi',
    'astroquery.gaia',
    'astroquery.gama',
    'astroquery.gemini',
    'astroquery.heasarc',
    'astroquery.hitran',
    'astroquery.ipac.irsa.ibe',
    'astroquery.hips2fits',
    'astroquery.image_cutouts',
    'astroquery.imcce',
    'astroquery.ipac',
    'astroquery.ipac.irsa',
    'astroquery.ipac.irsa.irsa_dust',
    'astroquery.ipac.ned',
    'astroquery.ipac.nexsci.nasa_exoplanet_archive',
    'astroquery.jplhorizons',
    'astroquery.jplsbdb',
    'astroquery.jplspec',
    'astroquery.linelists',
    'astroquery.magpis',
    'astroquery.mast',
    'astroquery.mocserver',
    'astroquery.mpc',
    'astroquery.nasa_ads',
    'astroquery.nist',
    'astroquery.nvas',
    'astroquery.oac',
    'astroquery.ogle',
    'astroquery.open_exoplanet_catalogue',
    'astroquery.sdss',
    'astroquery.simbad',
    'astroquery.skyview',
    'astroquery.solarsystem',
    'astroquery.splatalogue',
    'astroquery.svo_fps',
    'astroquery.utils',
    'astroquery.vamdc',
    'astroquery.vo_conesearch',
    'astroquery.vizier',
    'astroquery.vsa',
    'astroquery.wfau',
    'astroquery.xmatch',
]


class SocketTracker:
    def __init__(self):
        self.socket_attempts = []

    def __call__(self, *args, **kwargs):
        # Record the attempt
        self.socket_attempts.append((args, kwargs))
        # Raise a clear error to indicate socket creation
        raise RuntimeError("Socket creation attempted during import")


@pytest.mark.parametrize("module_name", ASTROQUERY_MODULES)
def test_no_http_calls_during_import(module_name):
    """
    Test that importing astroquery modules does not make any remote calls.

    This is a regression test for 3343, and the error that raises is not
    properly caught by the framework below, but that's an unrelated issue.

    This is the error shown if Gaia(show_server_messages=True) is called:
    ```
    E       TypeError: isinstance() arg 2 must be a type, a tuple of types, or a union
    ```
    """
    with no_internet():
        if module_name in sys.modules:
            del sys.modules[module_name]

        tracker = SocketTracker()
        with patch('socket.socket', tracker):
            importlib.import_module(module_name)

        assert not tracker.socket_attempts, (
            f"Module {module_name} attempted to create {len(tracker.socket_attempts)} "
            "socket(s) during import:\n" + (
                "\n".join(f"  - {args} {kwargs}" for args, kwargs in tracker.socket_attempts)
            )
        )
