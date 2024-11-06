===============
MAST Test Data
===============

This directory contains sample data that is used to mock functions in `~astroquery.mast.tests.test_mast.py`.

To generate `~astroquery.mast.tests.data.mission_columns.json`, use the following:

.. code-block:: python

    >>> import json
    >>> from astroquery.mast import utils

    >>> params = {'mission': 'hst'}
    >>> resp = utils._simple_request(f'https://mast.stsci.edu/search/util/api/v0.1/column_list', {'mission': 'hst'})
    >>> with open('mission_columns.json', 'w') as file:
    >>>     json.dump(resp.json(), file, indent=4)
