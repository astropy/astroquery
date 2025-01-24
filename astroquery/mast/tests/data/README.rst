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
