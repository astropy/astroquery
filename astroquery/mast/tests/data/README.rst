===============
MAST Test Data
===============

This directory contains sample data that is used to mock functions in `~astroquery.mast.tests.test_mast.py`.

To generate `~astroquery.mast.tests.data.mission_columns.json`, use the following:

.. doctest-remote-data::

    >>> import json
    >>> from astroquery.mast import utils
    ...
    >>> resp = utils._simple_request('https://mast.stsci.edu/search/util/api/v0.1/column_list', {'mission': 'hst'})
    >>> with open('mission_columns.json', 'w') as file:
    ...     json.dump(resp.json(), file, indent=4)  # doctest: +SKIP

To generate `~astroquery.mast.tests.data.panstarrs_columns.json`, use the following:

.. doctest-remote-data::

    >>> import json
    >>> from astroquery.mast import utils
    ...
    >>> resp = utils._simple_request('https://catalogs.mast.stsci.edu/api/v0.1/panstarrs/dr2/mean/metadata.json')
    >>> with open('panstarrs_columns.json', 'w') as file:
    ...     json.dump(resp.json(), file, indent=4)  # doctest: +SKIP

To generate `~astroquery.mast.tests.data.mission_products.json`, use the following:

.. doctest-remote-data::

    >>> import json
    >>> from astroquery.mast import utils
    ...
    >>> resp = utils._simple_request('https://mast.stsci.edu/search/hst/api/v0.1/list_products', {'dataset_ids': 'Z14Z0104T'})
    >>> with open('panstarrs_columns.json', 'w') as file:
    ...     json.dump(resp.json(), file, indent=4)  # doctest: +SKIP

To generate `~astroquery.mast.tests.data.mast_relative_path.json`, use the following:

.. doctest-remote-data::

    >>> import json
    >>> from astroquery.mast import utils
    ...
    >>> resp = utils._simple_request('https://mast.stsci.edu/api/v0.1/path_lookup/',
    ...                              {'uri': ['mast:HST/product/u9o40504m_c3m.fits', 'mast:HST/product/does_not_exist.fits']})
    >>> with open('mast_relative_path.json', 'w') as file:
    ...     json.dump(resp.json(), file, indent=4)  # doctest: +SKIP


To generate `~astroquery.mast.tests.data.resolver.json`, use the following:

.. doctest-remote-data::

    >>> import json
    >>> from astroquery.mast import utils
    ...
    >>> objects = ["TIC 307210830", "Barnard's Star", "M1", "M101", "M103", "M8", "M10"]
    >>> resp = utils._simple_request('http://mastresolver.stsci.edu/Santa-war/query',
    ...                              {'name': objects, 'outputFormat': 'json', 'resolveAll': 'true'})
    >>> with open('resolver.json', 'w') as file:
    ...     json.dump(resp.json(), file, indent=4)  # doctest: +SKIP

To generate `~astroquery.mast.tests.data.tap_collections.json`, use the following:

.. doctest-remote-data::

    >>> import json
    >>> from astroquery.mast import utils
    ...
    >>> resp = utils._simple_request('https://mast.stsci.edu/vo-tap/api/v0.1/openapi.json')
    ...
    >>> with open('tap_collections.json', 'w') as file:
    ...     json.dump(resp.json(), file, indent=4)  # doctest: +SKIP

To generate `~astroquery.mast.tests.data.tap_catalogs.vot`, use the following:

.. doctest-remote-data::

    >>> import pyvo
    >>> from astropy.io.votable import writeto
    ...
    >>> tap_service = pyvo.dal.TAPService("https://masttest.stsci.edu/vo-tap/api/v0.1/tic")
    >>> query = 'SELECT table_name, description FROM tap_schema.tables'
    >>> result = tap_service.run_sync(query)
    >>> writeto(result.votable, 'tap_catalogs.vot')  # doctest: +SKIP

To generate `~astroquery.mast.tests.data.tap_columns.vot`, use the following:

.. doctest-remote-data::

    >>> import pyvo
    >>> from astropy.io.votable import writeto
    ...
    >>> tap_service = pyvo.dal.TAPService("https://masttest.stsci.edu/vo-tap/api/v0.1/tic")
    >>> query = "SELECT column_name, datatype, unit, ucd, description FROM tap_schema.columns WHERE table_name = 'dbo.catalogrecord'"
    >>> result = tap_service.run_sync(query)
    >>> writeto(result.votable, 'tap_columns.vot')  # doctest: +SKIP

To generate `~astroquery.mast.tests.data.tap_capabilities.vot`, use the following:

.. doctest-remote-data::

    >>> import requests
    >>> import pyvo
    ...
    >>> tap_service = pyvo.dal.TAPService("https://masttest.stsci.edu/vo-tap/api/v0.1/tic")
    >>> caps_url = tap_service.baseurl.rstrip("/") + "/capabilities"
    >>> resp = requests.get(caps_url)
    >>> resp.raise_for_status()
    ...
    >>> with open("tap_capabilities.xml", "wb") as f:
    ...     f.write(resp.content)  # doctest: +SKIP

To generate `~astroquery.mast.tests.data.tap_results.vot`, use the following:

.. doctest-remote-data::

    >>> import pyvo
    >>> from astropy.io.votable import writeto
    ...
    >>> tap_service = pyvo.dal.TAPService("https://masttest.stsci.edu/vo-tap/api/v0.1/tic")
    >>> query = "SELECT TOP 10 * FROM dbo.catalogrecord WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 23.34086, 60.658, 0.002)) = 1"
    >>> result = tap_service.run_sync(query)
    >>> writeto(result.votable, 'tap_results.vot')  # doctest: +SKIP
