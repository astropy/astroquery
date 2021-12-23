# Licensed under a 3-clause BSD style license - see LICENSE.rst

from pytest_astropy_header.display import (PYTEST_HEADER_MODULES,
                                           TESTED_VERSIONS)


def pytest_configure(config):
    config.option.astropy_header = True

    PYTEST_HEADER_MODULES['Astropy'] = 'astropy'
    PYTEST_HEADER_MODULES['APLpy'] = 'aplpy'
    PYTEST_HEADER_MODULES['pyregion'] = 'pyregion'
    PYTEST_HEADER_MODULES['regions'] = 'regions'
    PYTEST_HEADER_MODULES['pyVO'] = 'pyvo'
    PYTEST_HEADER_MODULES['mocpy'] = 'mocpy'
    PYTEST_HEADER_MODULES['astropy-healpix'] = 'astropy_healpix'
    PYTEST_HEADER_MODULES['vamdclib'] = 'vamdclib'

    # keyring doesn't provide __version__ any more
    # PYTEST_HEADER_MODULES['keyring'] = 'keyring'

    del PYTEST_HEADER_MODULES['h5py']
    del PYTEST_HEADER_MODULES['Scipy']
    del PYTEST_HEADER_MODULES['Pandas']

    # add '_testrun' to the version name so that the user-agent indicates that
    # it's being run in a test
    from astroquery import version
    version.version += '_testrun'

    TESTED_VERSIONS['astroquery'] = version.version
    TESTED_VERSIONS['astropy_helpers'] = version.astropy_helpers_version
